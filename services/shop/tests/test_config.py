import pytest

from shop.checkout.app import CheckoutSettings
from shop.common.config import ConfigError, load_settings


def test_missing_variables_are_named(monkeypatch):
    for name in ("DATABASE_URL", "USERS_URL", "CATALOG_URL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("USERS_URL", "http://users.test")

    with pytest.raises(ConfigError) as raised:
        load_settings(CheckoutSettings)

    message = str(raised.value)
    assert "DATABASE_URL" in message
    assert "CATALOG_URL" in message
    assert "USERS_URL" not in message


def test_invalid_value_is_named(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://x@db/x")
    monkeypatch.setenv("USERS_URL", "http://users.test")
    monkeypatch.setenv("CATALOG_URL", "http://catalog.test")
    monkeypatch.setenv("UPSTREAM_TIMEOUT_SECONDS", "soon")

    with pytest.raises(ConfigError, match="UPSTREAM_TIMEOUT_SECONDS"):
        load_settings(CheckoutSettings)


def test_environment_is_read(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://x@db/x")
    monkeypatch.setenv("USERS_URL", "http://users.test")
    monkeypatch.setenv("CATALOG_URL", "http://catalog.test")
    monkeypatch.delenv("UPSTREAM_TIMEOUT_SECONDS", raising=False)

    settings = load_settings(CheckoutSettings)

    assert settings.users_url == "http://users.test"
    assert settings.upstream_timeout_seconds == 2.0
