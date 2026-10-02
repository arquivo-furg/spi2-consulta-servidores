from __future__ import annotations

import os

import psycopg


def get_connection() -> psycopg.Connection[tuple[object, ...]]:
    # O PostgreSQL cancela o comando que exceder esse tempo, inclusive espera por lock.
    statement_timeout_ms = int(os.getenv("DB_STATEMENT_TIMEOUT_MS", "2000"))

    return psycopg.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        options=f"-c statement_timeout={statement_timeout_ms}",
    )
