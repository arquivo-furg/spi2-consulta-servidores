"""Executa os cenarios de entradas invalidas da API contra a stack real."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


# Usar apenas uma stack de teste descartável: os cenários ocupam a tabela
# servidor e as vagas de busca durante as verificações.
def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validacao real dos erros da API")
    parser.add_argument(
        "--suite",
        choices=("errors", "sql-injection"),
        default="errors",
    )
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--project-directory", type=Path, default=Path.cwd())
    parser.add_argument("--db-user", required=True)
    parser.add_argument("--db-name", required=True)
    parser.add_argument("--lock-seconds", type=float, default=4.0)
    return parser.parse_args()


# Centraliza a chamada HTTP para registrar status, corpo e tempo de cada caso.
# HTTP 400/404/429/504 são respostas da API; erro de transporte é outra falha.
def request_json(
    base_url: str,
    path: str = "/api/servidores",
    params: dict[str, str] | None = None,
    timeout: float = 8.0,
    raw_query: str | None = None,
) -> dict[str, object]:
    query = raw_query if raw_query is not None else urlencode(params or {})
    url = f"{base_url.rstrip('/')}{path}"
    if query:
        url = f"{url}?{query}"

    started = time.perf_counter()
    request = Request(url, headers={"User-Agent": "spi-ii-api-validation/1.0"})

    try:
        with urlopen(request, timeout=timeout) as response:
            status = response.status
            raw_body = response.read().decode("utf-8", errors="replace")
            transport_error = None
    except HTTPError as error:
        status = error.code
        raw_body = error.read().decode("utf-8", errors="replace")
        transport_error = None
    except (URLError, TimeoutError, OSError) as error:
        status = None
        raw_body = ""
        transport_error = f"{type(error).__name__}: {error}"

    try:
        body: object = json.loads(raw_body) if raw_body else None
    except json.JSONDecodeError:
        body = raw_body

    return {
        "method": "GET",
        "path": path,
        "params": params or {},
        "status": status,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
        "body": body,
        "transport_error": transport_error,
    }


def message_is(response: dict[str, object], expected: str) -> bool:
    body = response["body"]
    return isinstance(body, dict) and body.get("mensagem") == expected


# Não basta receber o código esperado: o erro também precisa seguir o JSON da API.
def controlled_error(response: dict[str, object], status: int, message: str) -> bool:
    body = response["body"]
    return (
        response["transport_error"] is None
        and response["status"] == status
        and isinstance(body, dict)
        and body.get("sucesso") is False
        and body.get("dados") is None
        and body.get("mensagem") == message
    )


# Segura a tabela em outra conexão. A consulta da API fica esperando e deve
# atingir o statement_timeout, sem depender de uma busca naturalmente lenta.
def start_table_lock(
    project_directory: Path,
    db_user: str,
    db_name: str,
    seconds: float,
) -> subprocess.Popen[str]:
    sql = (
        "BEGIN; LOCK TABLE servidor IN ACCESS EXCLUSIVE MODE; "
        f"SELECT pg_sleep({seconds}); COMMIT;"
    )
    process = subprocess.Popen(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "db",
            "psql",
            "-v",
            "ON_ERROR_STOP=1",
            "-U",
            db_user,
            "-d",
            db_name,
            "-c",
            sql,
        ],
        cwd=project_directory,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    time.sleep(0.75)
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        raise RuntimeError(f"falha ao bloquear tabela: {stdout}\n{stderr}")
    return process


# Aguarda o COMMIT do processo auxiliar antes de iniciar o próximo cenário.
def finish_table_lock(process: subprocess.Popen[str]) -> None:
    try:
        stdout, stderr = process.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        raise RuntimeError(f"bloqueio nao finalizou: {stdout}\n{stderr}")

    if process.returncode != 0:
        raise RuntimeError(f"falha no bloqueio: {stdout}\n{stderr}")


# Cada cenário fornece sua própria regra de aprovação; o restante só monta
# o registro da requisição e da resposta para o arquivo de evidências.
def run_case(
    case_id: str,
    name: str,
    response: dict[str, object],
    validator: Callable[[dict[str, object]], bool],
) -> dict[str, object]:
    return {
        "id": case_id,
        "cenario": name,
        "resultado": "aprovado" if validator(response) else "reprovado",
        "requisicao": {
            "metodo": response["method"],
            "rota": response["path"],
            "parametros": response["params"],
        },
        "resposta": {
            "status": response["status"],
            "tempo_ms": response["elapsed_ms"],
            "corpo": response["body"],
            "erro_transporte": response["transport_error"],
        },
    }


# Guarda existência, contagem e resumo dos conteúdos antes/depois dos ataques.
# Só comparar contagens não detectaria uma alteração de valores em linhas existentes.
# Os hashes servem para comparar conteúdos; não são backup nem proteção dos dados.
def database_snapshot(arguments: argparse.Namespace) -> dict[str, object]:
    query = """
SELECT json_build_object(
  'tabelas', json_build_object(
    'cargo', to_regclass('public.cargo') IS NOT NULL,
    'orgao', to_regclass('public.orgao') IS NOT NULL,
    'uf', to_regclass('public.uf') IS NOT NULL,
    'servidor', to_regclass('public.servidor') IS NOT NULL
  ),
  'contagens', json_build_object(
    'cargo', (SELECT count(*) FROM cargo),
    'orgao', (SELECT count(*) FROM orgao),
    'uf', (SELECT count(*) FROM uf),
    'servidor', (SELECT count(*) FROM servidor)
  ),
  'fingerprints', json_build_object(
    'cargo', (
      SELECT md5(COALESCE(
        string_agg(concat_ws(chr(31), id::text, descricao), chr(30) ORDER BY id),
        ''
      )) FROM cargo
    ),
    'orgao', (
      SELECT md5(COALESCE(
        string_agg(concat_ws(chr(31), id::text, nome), chr(30) ORDER BY id),
        ''
      )) FROM orgao
    ),
    'uf', (
      SELECT md5(COALESCE(string_agg(sigla, chr(30) ORDER BY sigla), ''))
      FROM uf
    ),
    'servidor', (
      SELECT md5(COALESCE(
        string_agg(
          concat_ws(
            chr(31),
            id::text,
            nome,
            cargo_id::text,
            orgao_id::text,
            COALESCE(uf_sigla, '<NULL>')
          ),
          chr(30) ORDER BY id
        ),
        ''
      )) FROM servidor
    )
  )
)::text;
"""
    completed = subprocess.run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "db",
            "psql",
            "-v",
            "ON_ERROR_STOP=1",
            "-U",
            arguments.db_user,
            "-d",
            arguments.db_name,
            "-Atc",
            query,
        ],
        cwd=arguments.project_directory,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"falha ao verificar banco: {completed.stderr}")

    return json.loads(completed.stdout.strip())


# A tentativa deve ser recusada sem expor SQL, driver ou traceback na resposta.
# Esta checagem não substitui a comparação do banco feita no fim da suíte.
def is_controlled_injection_response(response: dict[str, object]) -> bool:
    body = response["body"]
    serialized = json.dumps(body, ensure_ascii=False).lower()
    internal_markers = (
        "traceback",
        "psycopg",
        "sqlstate",
        "select servidor",
        "database error",
    )
    return (
        response["transport_error"] is None
        and response["status"] in {400, 404}
        and isinstance(body, dict)
        and body.get("sucesso") is False
        and body.get("dados") is None
        and not any(marker in serialized for marker in internal_markers)
    )


def health_is_available(base_url: str) -> tuple[bool, dict[str, object]]:
    response = request_json(base_url, "/health")
    body = response["body"]
    available = (
        response["status"] == 200
        and isinstance(body, dict)
        and body.get("sucesso") is True
        and body.get("dados", {}).get("status") == "ok"
    )
    return available, response


# SQLI-07 já está codificado para URL. Passar por urlencode de novo transformaria
# %27 em %2527 e testaria uma entrada diferente da planejada.
def injection_query(field: str, payload_id: str, payload: str) -> str | None:
    if payload_id != "SQLI-07":
        return None

    query = f"{quote(field, safe='')}={payload}"
    if field == "similar":
        query += "&limit=100"
    return query


def injection_case(
    base_url: str,
    case_id: str,
    field: str,
    payload_id: str,
    payload: str,
    params: dict[str, str],
) -> dict[str, object]:
    response = request_json(
        base_url,
        params=params,
        raw_query=injection_query(field, payload_id, payload),
    )
    health_available, health_response = health_is_available(base_url)
    # O payload tenta dormir 5 s; responder em menos de 4 s é o limiar deste caso.
    # É uma verificação auxiliar, não uma prova isolada de ausência de injeção.
    time_attack_blocked = payload_id != "SQLI-06" or float(
        response["elapsed_ms"]
    ) < 4000
    passed = (
        is_controlled_injection_response(response)
        and health_available
        and time_attack_blocked
    )
    return {
        "id": case_id,
        "payload_id": payload_id,
        "filtro_contaminado": field,
        "payload": payload,
        "resultado": "aprovado" if passed else "reprovado",
        "requisicao": {
            "metodo": "GET",
            "rota": "/api/servidores",
            "parametros": params,
        },
        "resposta": {
            "status": response["status"],
            "tempo_ms": response["elapsed_ms"],
            "corpo": response["body"],
            "erro_transporte": response["transport_error"],
        },
        "verificacoes": {
            "resposta_controlada": is_controlled_injection_response(response),
            "ataque_temporal_abaixo_de_4s": time_attack_blocked,
            "api_disponivel_apos_caso": health_available,
            "health_status": health_response["status"],
        },
    }


# Primeiro testa cada entrada em cada filtro; depois repete o ataque destrutivo
# junto com filtros válidos. Ao final, compara o banco e verifica /health.
# Os payloads tentam alterar o banco: executar somente contra a fixture de teste.
def run_sql_injection_suite(arguments: argparse.Namespace) -> int:
    payloads = [
        ("SQLI-01", "'"),
        ("SQLI-02", "' OR '1'='1' --"),
        ("SQLI-03", "nome' --"),
        ("SQLI-04", "' UNION SELECT NULL --"),
        ("SQLI-05", "'; DROP TABLE servidor; --"),
        ("SQLI-06", "' OR pg_sleep(5) IS NULL --"),
        ("SQLI-07", "%27%20OR%20%271%27%3D%271%27%20--"),
        ("SQLI-08", '\" OR \"1\"=\"1'),
    ]
    fields = ("nome", "cargo", "uf", "orgao", "similar")
    before = database_snapshot(arguments)
    cases: list[dict[str, object]] = []

    for payload_id, payload in payloads:
        for field in fields:
            params = {field: payload}
            if field == "similar":
                params["limit"] = "100"
            cases.append(
                injection_case(
                    arguments.base_url,
                    f"{payload_id}-{field.upper()}",
                    field,
                    payload_id,
                    payload,
                    params,
                )
            )

    # Os valores abaixo dependem da fixture sintética, não dos dados públicos.
    baseline = {
        "nome": "SERVIDOR QA DUPLICADO",
        "cargo": "CARGO QA",
        "uf": "RS",
        "orgao": "ORGAO QA",
    }
    destructive_payload = "'; DROP TABLE servidor; --"
    for field in fields:
        params = dict(baseline)
        params[field] = destructive_payload
        if field == "similar":
            params["similar"] = destructive_payload
            params["limit"] = "100"
        cases.append(
            injection_case(
                arguments.base_url,
                f"SQLI-COMB-{field.upper()}",
                field,
                "SQLI-05",
                destructive_payload,
                params,
            )
        )

    after = database_snapshot(arguments)
    final_health, final_health_response = health_is_available(arguments.base_url)
    tables_exist = all(after["tabelas"].values())
    # Mesmo uma resposta HTTP controlada reprova a suíte se o banco mudou.
    integrity_preserved = before == after and tables_exist
    approved = sum(case["resultado"] == "aprovado" for case in cases)
    criterion_met = approved == len(cases) and integrity_preserved and final_health
    report = {
        "task": "PROJ-46",
        "executado_em_utc": datetime.now(timezone.utc).isoformat(),
        "alvo": arguments.base_url,
        "ambiente": {
            "stack": "Docker Compose com Flask/Gunicorn e PostgreSQL reais",
            "endpoint_com_filtros": "/api/servidores",
            "filtros_testados": list(fields),
        },
        "resumo": {
            "total": len(cases),
            "aprovados": approved,
            "reprovados": len(cases) - approved,
            "integridade_preservada": integrity_preserved,
            "api_disponivel_ao_final": final_health,
            "criterio_atendido": criterion_met,
        },
        "integridade_banco": {
            "antes": before,
            "depois": after,
            "contagens_e_fingerprints_identicos": before == after,
            "todas_as_tabelas_presentes": tables_exist,
        },
        "health_final": {
            "status": final_health_response["status"],
            "tempo_ms": final_health_response["elapsed_ms"],
            "corpo": final_health_response["body"],
        },
        "casos": cases,
    }

    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if criterion_met else 1


def main() -> int:
    arguments = parse_arguments()
    if arguments.suite == "sql-injection":
        return run_sql_injection_suite(arguments)

    base_url = arguments.base_url
    cases: list[dict[str, object]] = []

    # Cada tupla tem ID, descrição, rota, parâmetros e função de validação.
    # A fixture tem dois servidores de mesmo nome para conferir lista e paginação.
    specifications: list[
        tuple[
            str,
            str,
            str,
            dict[str, str],
            Callable[[dict[str, object]], bool],
        ]
    ] = [
        (
            "ERR-01A",
            "filtro vazio",
            "/api/servidores",
            {"nome": ""},
            lambda response: controlled_error(
                response, 400, "parametro invalido: nome"
            ),
        ),
        (
            "ERR-01B",
            "filtro somente com espacos",
            "/api/servidores",
            {"nome": "   "},
            lambda response: controlled_error(
                response, 400, "parametro invalido: nome"
            ),
        ),
        (
            "ERR-02",
            "tentativa representativa de SQL injection",
            "/api/servidores",
            {"nome": "' OR '1'='1' --"},
            lambda response: controlled_error(
                response, 400, "parametro invalido: nome"
            ),
        ),
        (
            "ERR-03",
            "nome valido ausente",
            "/api/servidores",
            {"nome": "NOME QA INEXISTENTE 20261004"},
            lambda response: controlled_error(response, 404, "nome nao encontrado"),
        ),
        (
            "API-07",
            "nome com multiplos registros paginados",
            "/api/servidores",
            {"nome": "SERVIDOR QA DUPLICADO", "page": "1", "page_size": "1"},
            lambda response: (
                response["status"] == 200
                and isinstance(response["body"], dict)
                and response["body"].get("sucesso") is True
                and response["body"].get("mensagem")
                == "multiplos registros encontrados"
                and len(response["body"].get("dados", [])) == 1
                and response["body"].get("paginacao", {}).get("total_registros")
                == 2
                and response["body"].get("paginacao", {}).get("total_paginas")
                == 2
            ),
        ),
        (
            "ERR-04",
            "cargo fora do formato",
            "/api/servidores",
            {"cargo": "###"},
            lambda response: controlled_error(
                response, 400, "parametro invalido: cargo"
            ),
        ),
        (
            "ERR-05",
            "UF inexistente",
            "/api/servidores",
            {"uf": "ZZ"},
            lambda response: controlled_error(response, 400, "uf invalida"),
        ),
        (
            "ERR-06",
            "orgao fora do formato",
            "/api/servidores",
            {"orgao": "###"},
            lambda response: controlled_error(
                response, 400, "parametro invalido: orgao"
            ),
        ),
        (
            "ERR-07A",
            "rota inexistente",
            "/api/rota-inexistente",
            {},
            lambda response: controlled_error(
                response, 404, "recurso nao encontrado"
            ),
        ),
        (
            "ERR-07B",
            "pagina fora da faixa",
            "/api/servidores",
            {"nome": "SERVIDOR QA DUPLICADO", "page": "99", "page_size": "1"},
            lambda response: controlled_error(response, 404, "pagina inexistente"),
        ),
        (
            "ERR-10",
            "parametro desconhecido",
            "/api/servidores",
            {"desconhecido": "valor"},
            lambda response: controlled_error(
                response, 400, "parametro desconhecido: desconhecido"
            ),
        ),
        (
            "ERR-11A",
            "limite nao numerico",
            "/api/servidores",
            {"similar": "SERVIDOR QA", "limit": "abc"},
            lambda response: controlled_error(
                response, 400, "parametro invalido: limit"
            ),
        ),
        (
            "ERR-11B",
            "limite acima do maximo",
            "/api/servidores",
            {"similar": "SERVIDOR QA", "limit": "101"},
            lambda response: controlled_error(
                response, 400, "parametro invalido: limit"
            ),
        ),
        (
            "ERR-11C",
            "pagina menor que um",
            "/api/servidores",
            {"nome": "SERVIDOR QA DUPLICADO", "page": "0"},
            lambda response: controlled_error(
                response, 400, "parametro invalido: page"
            ),
        ),
        (
            "ERR-11D",
            "tamanho de pagina acima do maximo",
            "/api/servidores",
            {"nome": "SERVIDOR QA DUPLICADO", "page_size": "101"},
            lambda response: controlled_error(
                response, 400, "parametro invalido: page_size"
            ),
        ),
        (
            "ERR-12A",
            "limite sem busca por similaridade",
            "/api/servidores",
            {"limit": "10"},
            lambda response: controlled_error(
                response, 400, "parametro limit exige similar"
            ),
        ),
        (
            "ERR-12B",
            "combinacao com UF invalida",
            "/api/servidores",
            {"nome": "SERVIDOR QA DUPLICADO", "uf": "ZZ"},
            lambda response: controlled_error(response, 400, "uf invalida"),
        ),
    ]

    for case_id, name, path, params, validator in specifications:
        response = request_json(base_url, path, params)
        cases.append(run_case(case_id, name, response, validator))

    # Uma consulta esperando o bloqueio deve voltar como HTTP 504 em JSON.
    timeout_lock = start_table_lock(
        arguments.project_directory,
        arguments.db_user,
        arguments.db_name,
        arguments.lock_seconds,
    )
    try:
        timeout_response = request_json(
            base_url,
            params={"nome": "SERVIDOR QA DUPLICADO"},
        )
    finally:
        finish_table_lock(timeout_lock)
    cases.append(
        run_case(
            "ERR-08",
            "timeout por espera de bloqueio no PostgreSQL",
            timeout_response,
            lambda response: controlled_error(
                response, 504, "tempo limite da consulta excedido"
            ),
        )
    )

    # Com as vagas de busca ocupadas, as demais requisições devem receber 429.
    # As que entraram podem terminar em 504 enquanto a tabela estiver bloqueada.
    concurrency_lock = start_table_lock(
        arguments.project_directory,
        arguments.db_user,
        arguments.db_name,
        arguments.lock_seconds,
    )
    try:
        with ThreadPoolExecutor(max_workers=12) as executor:
            futures = [
                executor.submit(
                    request_json,
                    base_url,
                    "/api/servidores",
                    {"nome": "SERVIDOR QA DUPLICADO"},
                )
                for _ in range(12)
            ]
            concurrent_responses = [
                future.result() for future in as_completed(futures)
            ]
    finally:
        finish_table_lock(concurrency_lock)

    status_counts: dict[str, int] = {}
    for response in concurrent_responses:
        key = str(response["status"])
        status_counts[key] = status_counts.get(key, 0) + 1

    concurrency_passed = (
        status_counts.get("429", 0) > 0
        and set(status_counts).issubset({"429", "504"})
        and all(response["transport_error"] is None for response in concurrent_responses)
    )
    cases.append(
        {
            "id": "ERR-09",
            "cenario": "excesso de buscas simultaneas",
            "resultado": "aprovado" if concurrency_passed else "reprovado",
            "requisicao": {
                "metodo": "GET",
                "rota": "/api/servidores",
                "parametros": {"nome": "SERVIDOR QA DUPLICADO"},
                "quantidade": len(concurrent_responses),
            },
            "resposta": {
                "status_por_quantidade": dict(sorted(status_counts.items())),
                "amostras_por_status": {
                    str(response["status"]): response["body"]
                    for response in concurrent_responses
                },
                "tempos_ms": sorted(
                    float(response["elapsed_ms"])
                    for response in concurrent_responses
                ),
                "erros_transporte": [
                    response["transport_error"]
                    for response in concurrent_responses
                    if response["transport_error"] is not None
                ],
            },
        }
    )

    # O último caso confere se os testes não deixaram a API indisponível.
    health_response = request_json(base_url, "/health")
    health_passed = (
        health_response["status"] == 200
        and isinstance(health_response["body"], dict)
        and health_response["body"].get("dados", {}).get("status") == "ok"
    )
    cases.append(
        run_case(
            "POS-01",
            "disponibilidade apos entradas invalidas, timeout e concorrencia",
            health_response,
            lambda _response: health_passed,
        )
    )

    approved = sum(case["resultado"] == "aprovado" for case in cases)
    report = {
        "task": "PROJ-45",
        "executado_em_utc": datetime.now(timezone.utc).isoformat(),
        "alvo": base_url,
        "ambiente": {
            "stack": "Docker Compose com Flask/Gunicorn e PostgreSQL reais",
            "timeout_banco_ms": 2000,
            "limite_concorrencia_api": 2,
            "registros_fixture": 2,
        },
        "resumo": {
            "total": len(cases),
            "aprovados": approved,
            "reprovados": len(cases) - approved,
            "criterio_atendido": approved == len(cases),
        },
        "casos": cases,
    }

    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["resumo"]["criterio_atendido"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
