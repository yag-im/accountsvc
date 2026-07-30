"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from accountsvc import __version__
from accountsvc.api import health
from accountsvc.api.errors import register_exception_handlers
from accountsvc.api.middleware import RequestContextMiddleware
from accountsvc.api.router import api_router
from accountsvc.core.config import Settings, get_settings
from accountsvc.core.lifespan import lifespan
from accountsvc.core.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = settings or get_settings()
    configure_logging(settings)

    app = FastAPI(
        title="accountsvc",
        version=__version__,
        summary="Service managing user identities, profiles, and account lifecycle.",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url=None,
        openapi_url="/openapi.json",
    )
    app.state.settings = settings

    app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(api_router)

    return app
