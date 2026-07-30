"""Unit tests for application configuration."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from accountsvc.core.config import Settings

_DB = {"db_host": "localhost", "db_user": "user", "db_password": "pass", "db_name": "accountsvc"}


def test_missing_db_password_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_DB_PASSWORD", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None, db_host="h", db_user="u", db_name="d")  # pyright: ignore[reportCallIssue]


def test_log_level_is_normalized() -> None:
    settings = Settings(_env_file=None, **_DB, log_level="debug")  # pyright: ignore[reportCallIssue]
    assert settings.log_level == "DEBUG"


def test_invalid_log_level_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **_DB, log_level="verbose")  # pyright: ignore[reportCallIssue]


def test_sqlalchemy_dsn_is_string() -> None:
    settings = Settings(_env_file=None, **_DB)  # pyright: ignore[reportCallIssue]
    assert settings.sqlalchemy_dsn.startswith("postgresql+asyncpg://")
