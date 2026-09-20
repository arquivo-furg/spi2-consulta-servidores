"""Prepara o banco vazio com os arquivos locais antes de iniciar a API."""
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import psycopg
from psycopg.conninfo import make_conninfo

from import_data import import_data


def prepare_database(data_dir: Path) -> None:
    fields = {"host": "DB_HOST", "port": "DB_PORT", "dbname": "DB_NAME",
              "user": "DB_USER", "password": "DB_PASSWORD"}
    connection_string = make_conninfo(**{field: os.environ[name] for field, name in fields.items()})
    with psycopg.connect(connection_string) as connection:
        populated = connection.execute("SELECT EXISTS (SELECT 1 FROM servidor)").fetchone()[0]
    # O volume pode ter uma carga anterior, mesmo que os arquivos brutos não estejam mais aqui.
    if populated:
        print("Banco já preenchido; mantendo os dados.", flush=True)
        return

    print("Banco vazio; preparando os arquivos de dados/.", flush=True)
    # O CSV intermediário só é necessário durante a primeira importação.
    with tempfile.TemporaryDirectory() as directory:
        prepared = Path(directory) / "importacao.csv"
        subprocess.run([
            sys.executable, str(Path(__file__).with_name("prepare_data.py")),
            "--aposentados", str(data_dir / "aposentados"),
            "--carreiras", str(data_dir / "carreiras"), "--saida", str(prepared),
        ], check=True)
        with prepared.open(encoding="utf-8", newline="") as source:
            rows = csv.reader(source)
            next(rows, None)
            if next(rows, None) is None:
                raise ValueError("os arquivos locais não produziram registros válidos")
        result = import_data(connection_string, prepared)
        print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    try:
        prepare_database(Path("/dados"))
    except (ValueError, KeyError, OSError, psycopg.Error, subprocess.CalledProcessError) as error:
        print(f"Não foi possível preparar o banco: {error}", file=sys.stderr, flush=True)
        sys.exit(1)
