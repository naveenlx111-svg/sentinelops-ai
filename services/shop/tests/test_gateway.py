"""Gateway tests. The three internal services are replaced by handlers."""

import json
from collections.abc import Callable

import httpx
from fastapi.testclient import TestClient

from shop.gateway.app import GatewaySettings, build_app

Handler = Callable[[httpx.Request], httpx.Response]


def gateway(handler: Handler) -> TestClient:
    settings = GatewaySettings(
        users_url="http://users.test",
        catalog_url="http://catalog.test",
        checkout_url="http://checkout.test",
    )
    return TestClient(build_app(settings, transport=httpx.MockTransport(handler)))


def test_health_needs_no_upstream():
    def never_called(request: httpx.Request) -> httpx.Response:
        raise AssertionError(f"unexpected upstream call: {request.url}")

    with gateway(never_called) as client:
        assert client.get("/healthz").status_code == 200
        assert client.get("/readyz").status_code == 200


def test_each_route_reaches_the_right_service():
    seen: list[str] = []

    def record(request: httpx.Request) -> httpx.Response:
        seen.append(f"{request.method} {request.url}")
        return httpx.Response(200, json={})

    with gateway(record) as client:
        client.get("/api/products")
        client.get("/api/products/2")
        client.get("/api/users/1")
        client.post("/api/orders", json={"user_id": 1, "product_id": 2, "quantity": 1})
        client.get("/api/orders/7")

    assert seen == [
        "GET http://catalog.test/products",
        "GET http://catalog.test/products/2",
        "GET http://users.test/users/1",
        "POST http://checkout.test/orders",
        "GET http://checkout.test/orders/7",
    ]


def test_order_body_and_created_status_pass_through():
    received: dict = {}

    def create(request: httpx.Request) -> httpx.Response:
        received.update(json.loads(request.content))
        return httpx.Response(201, json={"id": 7, "total_cents": 189900})

    order = {"user_id": 1, "product_id": 2, "quantity": 1}
    with gateway(create) as client:
        response = client.post("/api/orders", json=order)

    assert received == order
    assert response.status_code == 201
    assert response.json() == {"id": 7, "total_cents": 189900}
    assert response.headers["content-type"] == "application/json"


def test_upstream_errors_pass_through_unchanged():
    def not_found(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "product not found"})

    with gateway(not_found) as client:
        response = client.get("/api/products/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "product not found"}


def test_unreachable_service_is_502():
    def refused(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with gateway(refused) as client:
        response = client.get("/api/products")

    assert response.status_code == 502
    assert response.json() == {"detail": "catalog unreachable"}


def test_slow_service_is_504():
    def too_slow(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("no answer in time", request=request)

    with gateway(too_slow) as client:
        response = client.post("/api/orders", json={"user_id": 1, "product_id": 2, "quantity": 1})

    assert response.status_code == 504
    assert response.json() == {"detail": "checkout timed out"}
