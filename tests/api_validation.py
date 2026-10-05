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
from urllib.parse import urlencode
from urllib.request import Request, urlopen


# Usar apenas uma stack de teste descartável: os cenários ocupam a tabela
# servidor e as vagas de busca durante as verificações.
def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validacao real dos erros da API")
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
) -> dict[str, object]:
    query = urlencode(params or {})
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


def main() -> int:
    arguments = parse_arguments()
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
