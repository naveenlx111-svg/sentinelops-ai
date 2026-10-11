"""Catalog service: owns the ``products`` table, including stock levels."""

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings
from sqlalchemy import select, update
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


class CatalogSettings(BaseSettings):
    database_url: str


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    price_cents: Mapped[int]
    stock: Mapped[int]


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price_cents: int
    stock: int


class ReserveRequest(BaseModel):
    quantity: int = Field(gt=0)


def build_app(settings: CatalogSettings) -> FastAPI:
    engine = make_engine(settings.database_url)
    get_session = session_dependency(engine)
    SessionDep = Annotated[Session, Depends(get_session)]

    app = FastAPI(title="catalog", lifespan=on_shutdown(engine.dispose))
    add_health_routes(app, is_ready=lambda: database_is_ready(engine, Product))
    install_database_error_handler(app)

    @app.get("/products", response_model=list[ProductOut])
    def list_products(session: SessionDep) -> list[Product]:
        return list(session.scalars(select(Product).order_by(Product.id)))

    @app.get("/products/{product_id}", response_model=ProductOut)
    def get_product(product_id: int, session: SessionDep) -> Product:
        product = session.get(Product, product_id)
        if product is None:
            raise HTTPException(status_code=404, detail="product not found")
        return product

    @app.post("/products/{product_id}/reserve", response_model=ProductOut)
    def reserve_stock(product_id: int, body: ReserveRequest, session: SessionDep) -> Product:
        """Take ``quantity`` units out of stock, or refuse.

        A single UPDATE carries the stock check in its WHERE clause, so two
        concurrent reservations cannot both take the last unit.
        """
        result = session.execute(
            update(Product)
            .where(Product.id == product_id, Product.stock >= body.quantity)
            .values(stock=Product.stock - body.quantity)
        )
        session.commit()
        product = session.get(Product, product_id)
        if product is None:
            raise HTTPException(status_code=404, detail="product not found")
        if result.rowcount == 0:
            raise HTTPException(status_code=409, detail="insufficient stock")
        return product

    return app


def create_app() -> FastAPI:
    """Entry point for ``uvicorn --factory``: configure from the environment."""
    configure_logging("catalog")
    return build_app(load_settings(CatalogSettings))
