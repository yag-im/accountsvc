"""Console entrypoint that runs the service under uvicorn.

Invoked as ``accountsvc`` (console script) or ``python -m accountsvc``. In
production it is wrapped by ``opentelemetry-instrument`` for zero-code tracing.
"""

from __future__ import annotations

import uvicorn

from accountsvc.core.config import get_settings
from accountsvc.core.logging import build_logging_config


def main() -> None:
    """Run the ASGI server with the application's structured logging configuration."""
    settings = get_settings()
    uvicorn.run(
        "accountsvc.main:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        log_config=build_logging_config(settings),
        access_log=False,
        server_header=False,
        timeout_graceful_shutdown=settings.graceful_shutdown_timeout_seconds,
    )


if __name__ == "__main__":
    main()
