"""Gateway: the only service clients talk to.

It owns no data. Every ``/api`` route forwards to one internal service and
passes that service's status code and body back unchanged.
"""

from typing import Annotated, Any

import httpx
from fastapi import Body, FastAPI, Response
from pydantic_settings import BaseSettings

from shop.common.config import load_settings
from shop.common.health import add_health_routes
from shop.common.lifecycle import on_shutdown
from shop.common.logs import configure_logging
from shop.common.upstream import call_upstream


class GatewaySettings(BaseSettings):
    users_url: str
    catalog_url: str
    checkout_url: str
    # Longer than checkout's own upstream timeouts added together: an outer
    # caller that gives up first leaves the inner work running with nobody
    # waiting for the answer.
    upstream_timeout_seconds: float = 5.0


def build_app(settings: GatewaySettings, transport: httpx.BaseTransport | None = None) -> FastAPI:
    """Build the app. ``transport`` lets tests stand in for the other services."""
    http = httpx.Client(timeout=settings.upstream_timeout_seconds, transport=transport)
    users_url = settings.users_url.rstrip("/")
    catalog_url = settings.catalog_url.rstrip("/")
    checkout_url = settings.checkout_url.rstrip("/")

    app = FastAPI(title="gateway", lifespan=on_shutdown(http.close))
    # Ready as soon as it is serving. Readiness deliberately does not depend
    # on the other services: one of them blinking should fail the routes that
    # need it, not take the whole entry point out of rotation.
    add_health_routes(app)

    def forward(name: str, method: str, url: str, json: Any | None = None) -> Response:
        upstream = call_upstream(http, name, method, url, json=json)
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            media_type=upstream.headers.get("content-type"),
        )

    @app.get("/api/products")
    def list_products() -> Response:
        return forward("catalog", "GET", f"{catalog_url}/products")

    @app.get("/api/products/{product_id}")
    def get_product(product_id: int) -> Response:
        return forward("catalog", "GET", f"{catalog_url}/products/{product_id}")

    @app.get("/api/users/{user_id}")
    def get_user(user_id: int) -> Response:
        return forward("users", "GET", f"{users_url}/users/{user_id}")

    @app.post("/api/orders")
    def place_order(order: Annotated[dict[str, Any], Body()]) -> Response:
        return forward("checkout", "POST", f"{checkout_url}/orders", json=order)

    @app.get("/api/orders/{order_id}")
    def get_order(order_id: int) -> Response:
        return forward("checkout", "GET", f"{checkout_url}/orders/{order_id}")

    return app


def create_app() -> FastAPI:
    """Entry point for ``uvicorn --factory``: configure from the environment."""
    configure_logging("gateway")
    return build_app(load_settings(GatewaySettings))
