"""Releasing resources when a service stops."""

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastapi import FastAPI


def on_shutdown(
    *cleanups: Callable[[], None],
) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    """Build a FastAPI lifespan that runs each cleanup when the app stops."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield
        for cleanup in cleanups:
            cleanup()

    return lifespan
