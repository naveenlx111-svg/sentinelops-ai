"""Checkout tests. The users and catalog services are replaced by handlers."""

import json
from collections.abc import Callable

import httpx
from conftest import UNREACHABLE_DATABASE_URL
from fastapi.testclient import TestClient

from shop.checkout.app import CheckoutSettings, build_app

Handler = Callable[[httpx.Request], httpx.Response]

ORDER = {"user_id": 1, "product_id": 2, "quantity": 2}


def user_exists(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"id": 1, "email": "asha@example.com", "name": "Asha"})


def stock_reserved(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200, json={"id": 2, "name": "USB-C hub", "price_cents": 189900, "stock": 98}
    )


def answers(status_code: int, detail: str = "") -> Handler:
    return lambda request: httpx.Response(status_code, json={"detail": detail})


class Upstreams:
    """Stands in for users and catalog, and records what checkout sent them."""

    def __init__(self, users: Handler = user_exists, catalog: Handler = stock_reserved) -> None:
        self._handlers = {"users.test": users, "catalog.test": catalog}
        self.requests: list[httpx.Request] = []
        self.transport = httpx.MockTransport(self._handle)

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self._handlers[request.url.host](request)

    def called(self, host: str) -> bool:
        return any(request.url.host == host for request in self.requests)


def checkout(upstreams: Upstreams, database_url: str = UNREACHABLE_DATABASE_URL) -> TestClient:
    settings = CheckoutSettings(
        database_url=database_url,
        users_url="http://users.test",
        catalog_url="http://catalog.test/",  # trailing slash must not matter
    )
    return TestClient(build_app(settings, transport=upstreams.transport))


def test_places_an_order_and_stores_it(database_url):
    upstreams = Upstreams()
    with checkout(upstreams, database_url) as client:
        created = client.post("/orders", json=ORDER)
        fetched = client.get(f"/orders/{created.json()['id']}")

    assert created.status_code == 201
    assert created.json()["total_cents"] == 2 * 189900
    assert fetched.status_code == 200
    assert fetched.json() == created.json()

    reserve = upstreams.requests[1]
    assert reserve.method == "POST"
    assert str(reserve.url) == "http://catalog.test/products/2/reserve"
    assert json.loads(reserve.content) == {"quantity": 2}


def test_unknown_order_is_404(database_url):
    with checkout(Upstreams(), database_url) as client:
        assert client.get("/orders/999").status_code == 404


def test_unknown_user_is_404_and_no_stock_is_reserved():
    upstreams = Upstreams(users=answers(404, "user not found"))
    with checkout(upstreams) as client:
        response = client.post("/orders", json=ORDER)

    assert response.status_code == 404
    assert response.json() == {"detail": "user not found"}
    assert not upstreams.called("catalog.test")


def test_unknown_product_is_404():
    upstreams = Upstreams(catalog=answers(404, "product not found"))
    with checkout(upstreams) as client:
        response = client.post("/orders", json=ORDER)

    assert response.status_code == 404
    assert response.json() == {"detail": "product not found"}


def test_insufficient_stock_is_409_and_no_order_is_stored(database_url):
    upstreams = Upstreams(catalog=answers(409, "insufficient stock"))
    with checkout(upstreams, database_url) as client:
        response = client.post("/orders", json=ORDER)
        first_order = client.get("/orders/1")

    assert response.status_code == 409
    assert first_order.status_code == 404


def test_slow_users_service_is_504():
    def too_slow(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("no answer in time", request=request)

    upstreams = Upstreams(users=too_slow)
    with checkout(upstreams) as client:
        response = client.post("/orders", json=ORDER)

    assert response.status_code == 504
    assert response.json() == {"detail": "users timed out"}
    assert not upstreams.called("catalog.test")


def test_unreachable_catalog_service_is_502():
    def refused(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with checkout(Upstreams(catalog=refused)) as client:
        response = client.post("/orders", json=ORDER)

    assert response.status_code == 502
    assert response.json() == {"detail": "catalog unreachable"}


def test_failing_users_service_is_502():
    with checkout(Upstreams(users=answers(500))) as client:
        response = client.post("/orders", json=ORDER)

    assert response.status_code == 502
    assert response.json() == {"detail": "users returned 500"}


def test_malformed_catalog_answer_is_502():
    def nonsense(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"price": "free"})

    with checkout(Upstreams(catalog=nonsense)) as client:
        response = client.post("/orders", json=ORDER)

    assert response.status_code == 502
    assert response.json() == {"detail": "catalog returned an unexpected response"}


def test_non_positive_quantity_is_rejected_before_any_call():
    upstreams = Upstreams()
    with checkout(upstreams) as client:
        response = client.post("/orders", json={**ORDER, "quantity": 0})

    assert response.status_code == 422
    assert upstreams.requests == []
