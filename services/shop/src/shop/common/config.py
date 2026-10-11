"""Loading configuration from environment variables.

Each service declares the variables it needs as a ``BaseSettings`` subclass;
a field named ``users_url`` is read from the variable ``USERS_URL``.

Addresses have no defaults on purpose. A service that has not been told where
its dependencies are refuses to start and names what is missing, instead of
quietly dialling ``localhost``.
"""

from pydantic import ValidationError
from pydantic_settings import BaseSettings


class ConfigError(RuntimeError):
    """A required environment variable is missing or has an invalid value."""


def load_settings[S: BaseSettings](settings_cls: type[S]) -> S:
    """Build settings from the environment, or fail naming the bad variables."""
    try:
        return settings_cls()
    except ValidationError as exc:
        problems = "; ".join(
            f"{'_'.join(str(part) for part in error['loc']).upper()}: {error['msg']}"
            for error in exc.errors()
        )
        raise ConfigError(f"cannot start, bad environment configuration: {problems}") from exc
