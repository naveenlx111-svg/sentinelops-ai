"""Database plumbing shared by the services that own tables."""

import logging
from collections.abc import Callable, Iterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import Engine, create_engine, literal, select
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


def make_engine(database_url: str) -> Engine:
    """Create a pooled engine. No connection is opened until first use.

    ``pool_pre_ping`` tests a pooled connection before handing it out, so a
    database restart costs one transparent reconnect instead of a failed
    request. ``connect_timeout`` bounds how long a new connection attempt may
    hang when the database host does not answer.
    """
    return create_engine(database_url, pool_pre_ping=True, connect_args={"connect_timeout": 3})


def session_dependency(engine: Engine) -> Callable[[], Iterator[Session]]:
    """Return a FastAPI dependency that yields one session per request.

    A session borrows a pooled connection only when it first runs SQL, so a
    handler that calls other services before touching the database holds no
    connection while it waits on them.
    """
    factory = sessionmaker(engine, expire_on_commit=False)

    def get_session() -> Iterator[Session]:
        with factory() as session:
            yield session

    return get_session


def database_is_ready(engine: Engine, table: type[Base]) -> bool:
    """True when the database answers and this service's own table exists.

    Checking the table, not just the connection, keeps a service from
    reporting ready against a database that was never initialised.
    """
    try:
        with engine.connect() as connection:
            connection.execute(select(literal(1)).select_from(table).limit(1))
    except SQLAlchemyError as exc:
        reason = str(getattr(exc, "orig", None) or exc).splitlines()[0]
        logger.warning("not ready: %s", reason)
        return False
    return True


def install_database_error_handler(app: FastAPI) -> None:
    """Answer 503 instead of a bare 500 when the database cannot be reached."""

    @app.exception_handler(OperationalError)
    def database_unavailable(request: Request, exc: OperationalError) -> JSONResponse:
        # exc.orig is the driver's message (host, port, reason); it carries no
        # SQL parameters and no password.
        logger.error(
            "database unavailable on %s %s: %s", request.method, request.url.path, exc.orig
        )
        return JSONResponse({"detail": "database unavailable"}, status_code=503)
