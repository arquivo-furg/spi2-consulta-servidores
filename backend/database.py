from __future__ import annotations

import os

import psycopg


def get_connection() -> psycopg.Connection[tuple[object, ...]]:
    return psycopg.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )
