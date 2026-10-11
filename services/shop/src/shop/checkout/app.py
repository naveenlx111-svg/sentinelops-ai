"""Checkout service: owns the ``orders`` table and places orders.

Placing an order is the one operation in the shop that crosses services: it
asks ``users`` whether the buyer exists, asks ``catalog`` to reserve stock,
then records the order.
"""

from datetime import datetime
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from pydantic_settings import BaseSettings
from sqlalchemy import func
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
from shop.common.upstream import call_upstream, require_success


class CheckoutSettings(BaseSettings):
    database_url: str
    users_url: str
    catalog_url: str
    # Applied separately to connecting, sending and reading, not to the call
    # as a whole.
    upstream_timeout_seconds: float = 2.0


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int]
    product_id: Mapped[int]
    quantity: Mapped[int]
    total_cents: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class OrderIn(BaseModel):
    user_id: int
    product_id: int
    quantity: int = Field(gt=0)


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    product_id: int
    quantity: int
    total_cents: int
    created_at: datetime


class ReservedProduct(BaseModel):
    """The part of catalog's reservation answer that checkout relies on."""

    price_cents: int = Field(ge=0)


def build_app(settings: CheckoutSettings, transport: httpx.BaseTransport | None = None) -> FastAPI:
    """Build the app. ``transport`` lets tests stand in for the other services."""
    engine = make_engine(settings.database_url)
    get_session = session_dependency(engine)
    SessionDep = Annotated[Session, Depends(get_session)]
    http = httpx.Client(timeout=settings.upstream_timeout_seconds, transport=transport)
    users_url = settings.users_url.rstrip("/")
    catalog_url = settings.catalog_url.rstrip("/")

    app = FastAPI(title="checkout", lifespan=on_shutdown(http.close, engine.dispose))
    add_health_routes(app, is_ready=lambda: database_is_ready(engine, Order))
    install_database_error_handler(app)

    @app.post("/orders", response_model=OrderOut, status_code=201)
    def place_order(order: OrderIn, session: SessionDep) -> Order:
        user = call_upstream(http, "users", "GET", f"{users_url}/users/{order.user_id}")
        if user.status_code == 404:
            raise HTTPException(status_code=404, detail="user not found")
        require_success(user, "users")

        reservation = call_upstream(
            http,
            "catalog",
            "POST",
            f"{catalog_url}/products/{order.product_id}/reserve",
            json={"quantity": order.quantity},
        )
        if reservation.status_code == 404:
            raise HTTPException(status_code=404, detail="product not found")
        if reservation.status_code == 409:
            raise HTTPException(status_code=409, detail="insufficient stock")
        require_success(reservation, "catalog")
        try:
            product = ReservedProduct.model_validate_json(reservation.content)
        except ValidationError as exc:
            raise HTTPException(
                status_code=502, detail="catalog returned an unexpected response"
            ) from exc

        # Known limitation: if this write fails, the stock reserved above is
        # not given back. See "Known limitations" in docs/PROJECT_MAP.md.
        row = Order(
            user_id=order.user_id,
            product_id=order.product_id,
            quantity=order.quantity,
            total_cents=product.price_cents * order.quantity,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return row

    @app.get("/orders/{order_id}", response_model=OrderOut)
    def get_order(order_id: int, session: SessionDep) -> Order:
        row = session.get(Order, order_id)
        if row is None:
            raise HTTPException(status_code=404, detail="order not found")
        return row

    return app


def create_app() -> FastAPI:
    """Entry point for ``uvicorn --factory``: configure from the environment."""
    configure_logging("checkout")
    return build_app(load_settings(CheckoutSettings))
