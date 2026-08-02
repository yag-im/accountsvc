"""Application configuration sourced from the environment and dotenv files."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal
from urllib.parse import quote

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "dev", "stage", "prod"]

_VALID_LOG_LEVELS = frozenset({"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"})


class Settings(BaseSettings):
    """Strongly-typed application settings.

    Values are read (in order of precedence) from environment variables, then the
    ``.env`` and ``secrets.env`` dotenv files, and finally the defaults declared here.
    Required settings without a default cause a validation error at startup.
    """

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=(".env", "secrets.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: Environment = "local"
    service_name: str = "accountsvc"
    debug: bool = False
    log_level: str = "INFO"

    host: str = "0.0.0.0"  # noqa: S104 - the service is designed to run in a container
    port: int = Field(default=8080, ge=1, le=65535)

    db_host: str
    db_port: int = Field(default=5432, ge=1, le=65535)
    db_user: str
    db_password: str
    db_name: str
    db_pool_size: int = Field(default=5, ge=1)
    db_max_overflow: int = Field(default=10, ge=0)
    db_pool_timeout_seconds: float = Field(default=30.0, gt=0)
    db_pool_recycle_seconds: int = Field(default=1800, gt=0)
    db_command_timeout_seconds: float = Field(default=30.0, gt=0)

    graceful_shutdown_timeout_seconds: int = Field(default=30, ge=0)

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in _VALID_LOG_LEVELS:
            msg = f"Invalid log level {value!r}; expected one of {sorted(_VALID_LOG_LEVELS)}."
            raise ValueError(msg)
        return normalized

    @property
    def sqlalchemy_dsn(self) -> str:
        """Return the database URL as a string suitable for SQLAlchemy."""
        password = quote(self.db_password, safe="")
        return f"postgresql+asyncpg://{self.db_user}:{password}@{self.db_host}:{self.db_port}/{self.db_name}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance.

    The cache guarantees a single validated configuration object per process while
    remaining overridable in tests via FastAPI dependency overrides.
    """
    # pydantic-settings populates required fields (e.g. database_url) from the
    # environment at runtime, which the static type checker cannot infer.
    return Settings()  # pyright: ignore[reportCallIssue]
