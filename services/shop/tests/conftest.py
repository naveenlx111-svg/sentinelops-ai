import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine

INIT_SQL_DIR = Path(__file__).resolve().parents[1] / "db" / "init"

# A syntactically valid address where nothing listens, for tests that must
# not, or must fail to, reach a database.
UNREACHABLE_DATABASE_URL = "postgresql+psycopg://nobody@127.0.0.1:1/nothing"


@pytest.fixture
def database_url() -> str:
    """A PostgreSQL URL with the schema and seed data freshly applied.

    The tables are rebuilt from the same SQL files the real database is
    initialised with, so a model that drifts from the schema fails here.
    """
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("set TEST_DATABASE_URL to run the tests that need PostgreSQL")
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP TABLE IF EXISTS orders, products, users")
        for sql_file in sorted(INIT_SQL_DIR.glob("*.sql")):
            connection.exec_driver_sql(sql_file.read_text())
    engine.dispose()
    return url
