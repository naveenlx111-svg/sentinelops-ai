"""Liveness and readiness endpoints, the same on every service."""

from collections.abc import Callable

from fastapi import FastAPI
from fastapi.responses import JSONResponse


def add_health_routes(app: FastAPI, is_ready: Callable[[], bool] = lambda: True) -> None:
    """Register ``/healthz`` and ``/readyz``.

    They answer different questions, and orchestrators act on them differently:
    a failed liveness check gets the process restarted, a failed readiness
    check only stops traffic being sent to it.
    """

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        """Liveness: the process is up and serving HTTP. Checks no dependencies."""
        return {"status": "ok"}

    @app.get("/readyz")
    def readyz() -> JSONResponse:
        """Readiness: this instance can do useful work right now."""
        if is_ready():
            return JSONResponse({"status": "ready"})
        return JSONResponse({"status": "not ready"}, status_code=503)
