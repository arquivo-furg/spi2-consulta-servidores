"""Importa o CSV tratado em um banco com as tabelas vazias."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path

import psycopg


HEADERS = ("origem", "arquivo_origem", "linha_origem", "nome", "cargo", "orgao", "uf")


def load_staging(cursor: psycopg.Cursor[tuple[object, ...]], path: Path) -> None:
    # A tabela temporária recebe o CSV antes de separar cargos, órgãos e servidores.
    # ON COMMIT DROP remove essa etapa intermediária ao concluir a transação.
    cursor.execute(
        """
        CREATE TEMP TABLE importacao (
            ordem BIGINT GENERATED ALWAYS AS IDENTITY,
            origem TEXT NOT NULL,
            arquivo_origem TEXT NOT NULL,
            linha_origem BIGINT NOT NULL,
            nome TEXT NOT NULL,
            cargo TEXT NOT NULL,
            orgao TEXT NOT NULL,
            uf VARCHAR(2)
        ) ON COMMIT DROP
        """
    )

    with path.open("r", encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        if tuple(reader.fieldnames or ()) != HEADERS:
            raise ValueError("cabecalho do arquivo tratado nao corresponde ao formato esperado")

        # COPY envia linhas tipadas pelo driver, sem montar INSERT com texto do CSV.
        with cursor.copy(
            "COPY importacao (origem, arquivo_origem, linha_origem, nome, cargo, orgao, uf) FROM STDIN"
        ) as copy:
            for line_number, row in enumerate(reader, start=2):
                if None in row or any(row[column] is None for column in HEADERS):
                    raise ValueError(f"estrutura invalida na linha {line_number}")
                copy.write_row(
                    (
                        row["origem"],
                        row["arquivo_origem"],
                        row["linha_origem"],
                        row["nome"],
                        row["cargo"],
                        row["orgao"],
                        row["uf"] or None,
                    )
                )


def import_data(database_url: str, path: Path) -> dict[str, object]:
    # Toda a carga usa uma transação: qualquer erro desfaz também os INSERT anteriores.
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    (SELECT count(*) FROM cargo),
                    (SELECT count(*) FROM orgao),
                    (SELECT count(*) FROM uf),
                    (SELECT count(*) FROM servidor)
                """
            )
            # A importação não acumula registros de uma carga anterior.
            if any(cursor.fetchone() or ()):
                raise ValueError("as tabelas de destino devem estar vazias")

            load_staging(cursor, path)

            cursor.execute(
                """
                SELECT origem, arquivo_origem, count(*)
                FROM importacao
                GROUP BY origem, arquivo_origem
                ORDER BY origem, arquivo_origem
                """
            )
            # Estas contagens identificam quanto veio de cada arquivo tratado.
            sources = [
                {"origem": origin, "arquivo": filename, "registros": count}
                for origin, filename, count in cursor.fetchall()
            ]

            cursor.execute(
                """
                INSERT INTO cargo (id, descricao)
                SELECT row_number() OVER (ORDER BY cargo), cargo
                FROM (SELECT DISTINCT cargo FROM importacao) AS cargos
                """
            )
            cursor.execute(
                """
                INSERT INTO orgao (id, nome)
                SELECT row_number() OVER (ORDER BY orgao), orgao
                FROM (SELECT DISTINCT orgao FROM importacao) AS orgaos
                """
            )
            cursor.execute(
                """
                INSERT INTO uf (sigla)
                SELECT DISTINCT uf
                FROM importacao
                WHERE uf IS NOT NULL
                """
            )
            cursor.execute(
                """
                INSERT INTO servidor (id, nome, cargo_id, orgao_id, uf_sigla)
                SELECT dados.ordem, dados.nome, cargo.id, orgao.id, dados.uf
                FROM importacao AS dados
                JOIN cargo ON cargo.descricao = dados.cargo
                JOIN orgao ON orgao.nome = dados.orgao
                ORDER BY dados.ordem
                """
            )

            cursor.execute(
                """
                SELECT
                    (SELECT count(*) FROM cargo),
                    (SELECT count(*) FROM orgao),
                    (SELECT count(*) FROM uf),
                    (SELECT count(*) FROM servidor),
                    (SELECT count(*) FROM importacao)
                """
            )
            cargo, orgao, uf, servidor, staging = cursor.fetchone() or (0, 0, 0, 0, 0)
            # Detecta perda de linhas caso algum JOIN não encontre a referência criada.
            if servidor != staging:
                raise ValueError("a contagem importada nao corresponde ao arquivo tratado")

    return {
        "arquivo_tratado": path.name,
        "fontes": sources,
        "tabelas": {"cargo": cargo, "orgao": orgao, "uf": uf, "servidor": servidor},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arquivo", type=Path, required=True)
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    args = parser.parse_args()

    if not args.arquivo.is_file():
        parser.error(f"arquivo tratado nao encontrado: {args.arquivo}")
    if not args.database_url:
        parser.error("informe --database-url ou a variavel DATABASE_URL")

    try:
        result = import_data(args.database_url, args.arquivo)
    except (ValueError, psycopg.Error) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
