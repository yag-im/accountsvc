"""Async database engine and session factory construction."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from accountsvc.core.config import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    """Create the async SQLAlchemy engine with pooling and query timeouts."""
    statement_timeout_ms = str(int(settings.db_command_timeout_seconds * 1000))
    return create_async_engine(
        settings.sqlalchemy_dsn,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout_seconds,
        pool_recycle=settings.db_pool_recycle_seconds,
        pool_pre_ping=True,
        echo=False,
        connect_args={
            "application_name": settings.service_name,
            "connect_timeout": int(settings.db_pool_timeout_seconds),
            # libpq has no client-side query timeout; enforce it server-side.
            "options": f"-c statement_timeout={statement_timeout_ms}",
        },
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create a session factory bound to the given engine."""
    return async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
