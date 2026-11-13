"""Unit tests for database engine construction."""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.pool import QueuePool

from accountsvc.core.config import Settings
from accountsvc.core.database import create_engine

_DB = {"db_host": "localhost", "db_user": "user", "db_password": "pass", "db_name": "accountsvc"}


def _pool(settings: Settings) -> Any:
    pool = create_engine(settings).sync_engine.pool
    assert isinstance(pool, QueuePool)
    return pool


def test_engine_uses_db_settings_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_SQLDB_ENGINE_OPTIONS", raising=False)
    settings = Settings(_env_file=None, **_DB, db_pool_size=7, db_max_overflow=4)  # pyright: ignore[reportCallIssue]
    pool = _pool(settings)
    assert pool.size() == 7
    assert pool._max_overflow == 4
    assert pool._pre_ping is True


def test_engine_options_override_db_settings() -> None:
    options = {"pool_pre_ping": True, "pool_size": 2, "max_overflow": 3, "pool_timeout": 10, "pool_recycle": 120}
    settings = Settings(_env_file=None, **_DB, sqldb_engine_options=options)  # pyright: ignore[reportCallIssue]
    pool = _pool(settings)
    assert pool.size() == 2
    assert pool._max_overflow == 3
    assert pool._timeout == 10
    assert pool._recycle == 120
    assert pool._pre_ping is True
