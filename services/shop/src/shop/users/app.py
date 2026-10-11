"""Users service: owns the ``users`` table and answers lookups by id."""

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings
from sqlalchemy.orm import Mapped, Session, mapped_column

from shop.common.config import load_settings
from shop.common.db import (
    Base,
    database_is_ready,
    install_database_error_handler,
    make_engine,
    session_dependency,
)
from shop.common.health import add_health_routes
from shop.common.lifecycle import on_shutdown
from shop.common.logs import configure_logging


class UsersSettings(BaseSettings):
    database_url: str


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str]
    name: Mapped[str]


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str


def build_app(settings: UsersSettings) -> FastAPI:
    engine = make_engine(settings.database_url)
    get_session = session_dependency(engine)

    app = FastAPI(title="users", lifespan=on_shutdown(engine.dispose))
    add_health_routes(app, is_ready=lambda: database_is_ready(engine, User))
    install_database_error_handler(app)

    @app.get("/users/{user_id}", response_model=UserOut)
    def get_user(user_id: int, session: Annotated[Session, Depends(get_session)]) -> User:
        user = session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="user not found")
        return user

    return app


def create_app() -> FastAPI:
    """Entry point for ``uvicorn --factory``: configure from the environment."""
    configure_logging("users")
    return build_app(load_settings(UsersSettings))
