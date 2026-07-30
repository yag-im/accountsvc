"""Application lifespan management for startup and graceful shutdown."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from accountsvc.core.config import Settings
from accountsvc.core.database import create_engine, create_session_factory

logger = logging.getLogger("accountsvc.lifespan")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Initialize shared resources on startup and dispose of them on shutdown."""
    settings: Settings = app.state.settings
    engine = create_engine(settings)
    app.state.db_engine = engine
    app.state.db_sessionmaker = create_session_factory(engine)
    logger.info("application_startup_complete", extra={"environment": settings.environment})
    try:
        yield
    finally:
        await engine.dispose()
        logger.info("application_shutdown_complete")
