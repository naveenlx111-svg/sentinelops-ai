import pytest
from fastapi.testclient import TestClient

from shop.catalog.app import CatalogSettings, build_app

LAPTOP_STAND = 3  # seeded with 3 in stock


@pytest.fixture
def client(database_url):
    with TestClient(build_app(CatalogSettings(database_url=database_url))) as test_client:
        yield test_client


def test_lists_products_in_id_order(client):
    response = client.get("/products")

    assert response.status_code == 200
    assert [product["name"] for product in response.json()] == [
        "Mechanical keyboard",
        "USB-C hub",
        "Laptop stand",
    ]


def test_unknown_product_is_404(client):
    assert client.get("/products/999").status_code == 404


def test_reserving_takes_units_out_of_stock(client):
    response = client.post(f"/products/{LAPTOP_STAND}/reserve", json={"quantity": 2})

    assert response.status_code == 200
    assert response.json()["stock"] == 1
    assert client.get(f"/products/{LAPTOP_STAND}").json()["stock"] == 1


def test_reserving_exactly_the_remaining_stock_succeeds(client):
    response = client.post(f"/products/{LAPTOP_STAND}/reserve", json={"quantity": 3})

    assert response.status_code == 200
    assert response.json()["stock"] == 0


def test_reserving_more_than_stock_is_refused_and_changes_nothing(client):
    response = client.post(f"/products/{LAPTOP_STAND}/reserve", json={"quantity": 4})

    assert response.status_code == 409
    assert response.json() == {"detail": "insufficient stock"}
    assert client.get(f"/products/{LAPTOP_STAND}").json()["stock"] == 3


def test_reserving_an_unknown_product_is_404(client):
    assert client.post("/products/999/reserve", json={"quantity": 1}).status_code == 404


@pytest.mark.parametrize("quantity", [0, -1])
def test_non_positive_quantity_is_rejected(client, quantity):
    response = client.post(f"/products/{LAPTOP_STAND}/reserve", json={"quantity": quantity})

    assert response.status_code == 422
