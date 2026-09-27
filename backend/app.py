from flask import Flask, jsonify, request

from database import get_connection


app = Flask(__name__)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/servidores")
def search_servers():
    name = request.args.get("nome")
    role = request.args.get("cargo")
    state = request.args.get("uf")
    agency = request.args.get("orgao")

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

    if not conditions:
        conditions.append("servidor.nome = %s")
        values.append(None)

    where_clause = " AND ".join(conditions)

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
                ORDER BY servidor.id
                """,
                tuple(values),
            )
            servers = cursor.fetchall()

    return jsonify(
        [
            {"id": id_, "nome": name, "cargo": role, "uf": state, "orgao": agency}
            for id_, name, role, state, agency in servers
        ]
    )


if __name__ == "__main__":
    app.run()
