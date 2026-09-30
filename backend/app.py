from flask import Flask, jsonify, request

from database import get_connection


app = Flask(__name__)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def serialize_servers(servers):
    return [
        {"id": id_, "nome": name, "cargo": role, "uf": state, "orgao": agency}
        for id_, name, role, state, agency in servers
    ]


@app.get("/api/servidores")
def search_servers():
    name = request.args.get("nome")
    role = request.args.get("cargo")
    state = request.args.get("uf")
    agency = request.args.get("orgao")
    similar = request.args.get("similar")

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
        similar = " ".join(similar.replace("%", " ").split())
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
    similar_limit = None

    if similar is not None:
        order_clause = "similarity(servidor.nome, %s) DESC, servidor.id"
        values.append(similar)
        similar_limit = min(int(request.args.get("limit", 100)), 100)

    pagination_requested = "page" in request.args or "page_size" in request.args
    total = None

    if pagination_requested:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 100))
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

    if pagination_requested:
        return jsonify({"dados": data, "total": total})

    return jsonify(data)


if __name__ == "__main__":
    app.run()
