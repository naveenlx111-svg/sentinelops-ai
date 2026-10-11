"""Calling another service over HTTP, with every failure mapped explicitly."""

import logging
from typing import Any

import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def call_upstream(
    client: httpx.Client, name: str, method: str, url: str, json: Any | None = None
) -> httpx.Response:
    """Send one request to another service and return its response.

    A dependency that does not answer in time becomes 504; one that cannot be
    reached at all becomes 502. Either way the caller gets a prompt, specific
    error instead of hanging.

    There are no retries. Repeating a call that is not idempotent, such as
    reserving stock, could perform it twice.
    """
    try:
        return client.request(method, url, json=json)
    except httpx.TimeoutException as exc:
        logger.warning("%s timed out: %s %s (%s)", name, method, url, type(exc).__name__)
        raise HTTPException(status_code=504, detail=f"{name} timed out") from exc
    except httpx.TransportError as exc:
        logger.warning("%s unreachable: %s %s (%s)", name, method, url, type(exc).__name__)
        raise HTTPException(status_code=502, detail=f"{name} unreachable") from exc


def require_success(response: httpx.Response, name: str) -> None:
    """Turn any non-2xx answer the caller has not handled into a 502."""
    if not response.is_success:
        logger.warning("%s returned %s for %s", name, response.status_code, response.request.url)
        raise HTTPException(status_code=502, detail=f"{name} returned {response.status_code}")
