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

    filter_column = "servidor.nome"
    filter_value = name

    if role is not None:
        filter_column = "cargo.descricao"
        filter_value = role
    elif state is not None:
        filter_column = "servidor.uf_sigla"
        filter_value = state
    elif agency is not None:
        filter_column = "orgao.nome"
        filter_value = agency

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
                WHERE {filter_column} = %s
                ORDER BY servidor.id
                """,
                (filter_value,),
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
