from conftest import UNREACHABLE_DATABASE_URL
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from shop.users.app import UsersSettings, build_app


def test_returns_a_seeded_user(database_url):
    with TestClient(build_app(UsersSettings(database_url=database_url))) as client:
        response = client.get("/users/1")

    assert response.status_code == 200
    assert response.json() == {"id": 1, "email": "asha@example.com", "name": "Asha"}


def test_unknown_user_is_404(database_url):
    with TestClient(build_app(UsersSettings(database_url=database_url))) as client:
        response = client.get("/users/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "user not found"}


def test_ready_when_database_answers(database_url):
    with TestClient(build_app(UsersSettings(database_url=database_url))) as client:
        assert client.get("/readyz").status_code == 200


def test_alive_but_not_ready_without_a_database():
    settings = UsersSettings(database_url=UNREACHABLE_DATABASE_URL)
    with TestClient(build_app(settings)) as client:
        assert client.get("/healthz").status_code == 200
        assert client.get("/readyz").status_code == 503

        response = client.get("/users/1")

    assert response.status_code == 503
    assert response.json() == {"detail": "database unavailable"}


def test_not_ready_when_the_table_is_missing(database_url):
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP TABLE users")
    engine.dispose()

    with TestClient(build_app(UsersSettings(database_url=database_url))) as client:
        assert client.get("/healthz").status_code == 200
        assert client.get("/readyz").status_code == 503
