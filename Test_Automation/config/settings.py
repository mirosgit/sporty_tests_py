"""Central configuration, read from environment variables and an optional `.env` file."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

# Seconds for explicit UI waits and API requests.
DEFAULT_TIMEOUT = 10.0


class ConfigurationError(RuntimeError):
    """Raised when a required setting is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    base_url: str
    user_id: str
    headless: bool
    default_timeout: float

    @property
    def api_url(self) -> str:
        return f"{self.base_url}/api"

    @property
    def app_url(self) -> str:
        return f"{self.base_url}/?user-id={self.user_id}"

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            base_url=_read_base_url(),
            user_id=_read_required("USER_ID"),
            headless=_read_bool("HEADLESS", default=True),
            default_timeout=DEFAULT_TIMEOUT,
        )


def _read_required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigurationError(f"{name} is not set. Copy .env.example to .env and fill it in.")
    return value


def _read_base_url() -> str:
    value = _read_required("BASE_URL")
    if not value.startswith(("http://", "https://")):
        raise ConfigurationError(f"BASE_URL must start with http:// or https://, got {value!r}")
    return value.rstrip("/")


def _read_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes"}:
        return True
    if normalized in {"0", "false", "no"}:
        return False
    raise ConfigurationError(f"{name} must be true or false, got {value!r}")
