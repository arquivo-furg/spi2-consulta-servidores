import os
import re
from functools import wraps
from threading import BoundedSemaphore

from flask import Flask, jsonify, request
from psycopg.errors import QueryCanceled

from database import get_connection


app = Flask(__name__)
# O limite de buscas é compartilhado pelas threads deste processo.
search_slots = BoundedSemaphore(int(os.getenv("API_MAX_CONCURRENT_REQUESTS", "2")))

ALLOWED_PARAMETERS = {
    "nome",
    "cargo",
    "uf",
    "orgao",
    "similar",
    "limit",
    "page",
    "page_size",
}
VALID_UFS = {
    "AC",
    "AL",
    "AP",
    "AM",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MT",
    "MS",
    "MG",
    "PA",
    "PB",
    "PR",
    "PE",
    "PI",
    "RJ",
    "RN",
    "RS",
    "RO",
    "RR",
    "SC",
    "SP",
    "SE",
    "TO",
}
SEARCH_VALUE_PATTERN = re.compile(r"[\w\sÀ-ÿ.,'()&/+ºª-]+", re.UNICODE)
SQL_INJECTION_PATTERN = re.compile(
    r"--|/\*|\*/|;|\bunion\s+select\b|\bdrop\s+table\b|"
    r"\binsert\s+into\b|\bdelete\s+from\b|\bupdate\s+\w+\s+set\b|"
    r"\balter\s+table\b|\bcreate\s+table\b|\btruncate\s+table\b|"
    r"\bpg_sleep\s*\(|\b(?:or|and)\b\s+['\"\d].*=",
    re.IGNORECASE,
)


@app.get("/health")
def health():
    return success_response({"status": "ok"}, "api disponivel")


def success_response(data, message, pagination=None):
    response = {
        "sucesso": True,
        "mensagem": message,
        "dados": data,
    }
    if pagination is not None:
        response["paginacao"] = pagination

    return jsonify(response), 200


def error_response(message, status_code):
    return (
        jsonify(
            {
                "sucesso": False,
                "mensagem": message,
                "dados": None,
            }
        ),
        status_code,
    )


@app.errorhandler(404)
def resource_not_found(_error):
    return error_response("recurso nao encontrado", 404)


def serialize_servers(servers):
    return [
        {"id": id_, "nome": name, "cargo": role, "uf": state, "orgao": agency}
        for id_, name, role, state, agency in servers
    ]


def normalize_search_value(parameter, value):
    normalized = " ".join(value.split())

    if parameter == "similar":
        normalized = " ".join(normalized.replace("%", " ").split())

    if (
        not normalized
        or normalized in {"'", '"'}
        or SEARCH_VALUE_PATTERN.fullmatch(normalized) is None
        or SQL_INJECTION_PATTERN.search(normalized) is not None
    ):
        raise ValueError(f"parametro invalido: {parameter}")

    if parameter == "uf":
        if re.fullmatch(r"[A-Za-z]{2}", normalized) is None:
            raise ValueError("parametro invalido: uf")

        normalized = normalized.upper()
        if normalized not in VALID_UFS:
            raise ValueError("uf invalida")

        return normalized

    return normalized


def parse_positive_integer(parameter, default, maximum=None):
    raw_value = request.args.get(parameter)

    if raw_value is None:
        return default

    if re.fullmatch(r"[0-9]+", raw_value) is None:
        raise ValueError(f"parametro invalido: {parameter}")

    value = int(raw_value)
    if value < 1 or (maximum is not None and value > maximum):
        raise ValueError(f"parametro invalido: {parameter}")

    return value


def no_results_message(name, role, state, agency, similar):
    informed_filters = [
        value
        for value in (name, role, state, agency, similar)
        if value is not None
    ]

    if len(informed_filters) != 1:
        return "nenhum registro encontrado"
    if name is not None:
        return "nome nao encontrado"
    if role is not None:
        return "cargo nao encontrado"
    if state is not None:
        return "nenhum registro encontrado para a uf informada"
    if agency is not None:
        return "orgao nao encontrado"

    return "nenhum nome similar encontrado"


def limit_concurrent_requests(view):
    @wraps(view)
    def limited_view(*args, **kwargs):
        # Não cria fila de espera na API: sem vaga, devolve 429 imediatamente.
        if not search_slots.acquire(blocking=False):
            return error_response("limite de buscas simultaneas excedido", 429)

        try:
            return view(*args, **kwargs)
        finally:
            search_slots.release()

    return limited_view


def handle_search_timeout(view):
    @wraps(view)
    def timed_view(*args, **kwargs):
        try:
            return view(*args, **kwargs)
        except QueryCanceled:
            return error_response("tempo limite da consulta excedido", 504)

    return timed_view


@app.get("/api/servidores")
@limit_concurrent_requests
@handle_search_timeout
def search_servers():
    unknown_parameters = sorted(set(request.args) - ALLOWED_PARAMETERS)
    if unknown_parameters:
        return error_response(
            f"parametro desconhecido: {unknown_parameters[0]}", 400
        )

    try:
        name = (
            normalize_search_value("nome", request.args["nome"])
            if "nome" in request.args
            else None
        )
        role = (
            normalize_search_value("cargo", request.args["cargo"])
            if "cargo" in request.args
            else None
        )
        state = (
            normalize_search_value("uf", request.args["uf"])
            if "uf" in request.args
            else None
        )
        agency = (
            normalize_search_value("orgao", request.args["orgao"])
            if "orgao" in request.args
            else None
        )
        similar = (
            normalize_search_value("similar", request.args["similar"])
            if "similar" in request.args
            else None
        )

        if similar is None and "limit" in request.args:
            raise ValueError("parametro limit exige similar")

        similar_limit = (
            parse_positive_integer("limit", 100, maximum=100)
            if similar is not None
            else None
        )

        pagination_requested = "page" in request.args or "page_size" in request.args
        if pagination_requested:
            page = parse_positive_integer("page", 1, maximum=2_147_483_647)
            page_size = parse_positive_integer("page_size", 100, maximum=100)
    except ValueError as error:
        return error_response(str(error), 400)

    filters = (
        ("servidor.nome", name),
        ("cargo.descricao", role),
        ("servidor.uf_sigla", state),
        ("orgao.nome", agency),
    )
    # As colunas são fixas do código; a entrada do usuário vai nos parâmetros
    # %s do psycopg, nunca interpolada no texto SQL.
    conditions = []
    values = []

    for column, value in filters:
        if value is not None:
            conditions.append(f"{column} = %s")
            values.append(value)

    if similar is not None:
        conditions.append("servidor.nome %% %s")
        values.append(similar)

    if not conditions:
        conditions.append("servidor.nome = %s")
        values.append(None)

    where_clause = " AND ".join(conditions)
    # O COUNT usa só os filtros; ORDER BY, LIMIT e OFFSET acrescentam parâmetros depois.
    where_values = tuple(values)
    order_clause = "servidor.id"
    limit_clause = ""
    offset_clause = ""

    if similar is not None:
        order_clause = "servidor.nome <-> %s, servidor.id"
        values.append(similar)
    total = None

    if pagination_requested:
        offset = (page - 1) * page_size

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT count(*)
                    FROM servidor
                    JOIN cargo ON cargo.id = servidor.cargo_id
                    JOIN orgao ON orgao.id = servidor.orgao_id
                    WHERE {where_clause}
                    """,
                    where_values,
                )
                total = cursor.fetchone()[0]

        if similar_limit is not None:
            total = min(total, similar_limit)

        # Arredonda para cima sem criar uma página extra quando a divisão é exata.
        total_pages = (total + page_size - 1) // page_size
        if (total == 0 and page > 1) or (
            total_pages > 0 and page > total_pages
        ):
            return error_response("pagina inexistente", 404)

        pagination = {
            "pagina": page,
            "tamanho_pagina": page_size,
            "total_registros": total,
            "total_paginas": total_pages,
        }

        if similar_limit is not None:
            # A última página não pode ultrapassar o limite global da similaridade.
            page_size = min(page_size, max(total - offset, 0))

        values.append(page_size)
        values.append(offset)
        limit_clause = "LIMIT %s"
        offset_clause = "OFFSET %s"
    elif similar_limit is not None:
        values.append(similar_limit)
        limit_clause = "LIMIT %s"

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT servidor.id,
                       servidor.nome,
                       cargo.descricao,
                       servidor.uf_sigla,
                       orgao.nome
                FROM servidor
                JOIN cargo ON cargo.id = servidor.cargo_id
                JOIN orgao ON orgao.id = servidor.orgao_id
                WHERE {where_clause}
                ORDER BY {order_clause}
                {limit_clause}
                {offset_clause}
                """,
                tuple(values),
            )
            servers = cursor.fetchall()

    data = serialize_servers(servers)

    if not data:
        return error_response(
            no_results_message(
                name,
                role,
                state,
                agency,
                similar,
            ),
            404,
        )

    message = (
        "registro encontrado"
        if len(data) == 1
        else "multiplos registros encontrados"
    )

    if pagination_requested:
        if total > 1:
            message = "multiplos registros encontrados"
        return success_response(data, message, pagination)

    return success_response(data, message)


if __name__ == "__main__":
    app.run()
