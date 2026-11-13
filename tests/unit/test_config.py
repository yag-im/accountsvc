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


def test_sqldb_engine_options_parsed_from_json_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_SQLDB_ENGINE_OPTIONS", '{"pool_pre_ping": true, "pool_size": 2, "pool_timeout": 10}')
    settings = Settings(_env_file=None, **_DB)  # pyright: ignore[reportCallIssue]
    assert settings.sqldb_engine_options == {"pool_pre_ping": True, "pool_size": 2, "pool_timeout": 10}


def test_sqldb_engine_options_defaults_to_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_SQLDB_ENGINE_OPTIONS", raising=False)
    settings = Settings(_env_file=None, **_DB)  # pyright: ignore[reportCallIssue]
    assert settings.sqldb_engine_options == {}


def test_sqldb_engine_options_rejects_non_object(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_SQLDB_ENGINE_OPTIONS", "[1, 2]")
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **_DB)  # pyright: ignore[reportCallIssue]


def test_sqlalchemy_dsn_is_string() -> None:
    settings = Settings(_env_file=None, **_DB)  # pyright: ignore[reportCallIssue]
    assert settings.sqlalchemy_dsn.startswith("postgresql+psycopg://")
