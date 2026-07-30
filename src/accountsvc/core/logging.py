"""Centralized structured (JSON) logging configuration.

All log records are emitted as single-line JSON objects enriched with service
metadata, the active request id and the active OpenTelemetry trace/span ids. A
logging filter drops access-log records for health-check endpoints.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import logging.config
from typing import Any

from accountsvc.core.config import Settings
from accountsvc.core.context import request_id_ctx
from accountsvc.core.observability import current_trace_context

_HEALTH_PATHS = frozenset({"/healthz", "/readyz"})

# uvicorn access-log records carry positional args of the form
# (client_addr, method, path, http_version, status); index 2 holds the request path.
_ACCESS_LOG_PATH_INDEX = 2

_RESERVED_RECORD_ATTRS = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "message",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "taskName",
        "thread",
        "threadName",
    }
)


class HealthCheckAccessLogFilter(logging.Filter):
    """Drop server access-log records that target health-check endpoints."""

    def filter(self, record: logging.LogRecord) -> bool:
        args = record.args
        if isinstance(args, tuple) and len(args) > _ACCESS_LOG_PATH_INDEX:
            path = str(args[_ACCESS_LOG_PATH_INDEX]).split("?", 1)[0]
            if path in _HEALTH_PATHS:
                return False
        return True


class JsonFormatter(logging.Formatter):
    """Render log records as structured JSON with correlation metadata."""

    def __init__(self, service: str, environment: str) -> None:
        super().__init__()
        self._service = service
        self._environment = environment

    def format(self, record: logging.LogRecord) -> str:
        trace_id, span_id = current_trace_context()
        payload: dict[str, Any] = {
            "timestamp": dt.datetime.fromtimestamp(record.created, tz=dt.UTC).isoformat(),
            "severity": record.levelname,
            "service": self._service,
            "environment": self._environment,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(),
            "trace_id": trace_id,
            "span_id": span_id,
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack"] = self.formatStack(record.stack_info)

        for key, value in record.__dict__.items():
            if key not in _RESERVED_RECORD_ATTRS and key not in payload:
                payload[key] = value

        return json.dumps(payload, default=str, separators=(",", ":"))


def build_logging_config(settings: Settings) -> dict[str, Any]:
    """Build a :func:`logging.config.dictConfig` dictionary for the service."""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "health_access": {"()": HealthCheckAccessLogFilter},
        },
        "formatters": {
            "json": {
                "()": JsonFormatter,
                "service": settings.service_name,
                "environment": settings.environment,
            },
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "accountsvc": {"handlers": ["stdout"], "level": settings.log_level, "propagate": False},
            "uvicorn": {"handlers": ["stdout"], "level": settings.log_level, "propagate": False},
            "uvicorn.error": {"handlers": ["stdout"], "level": settings.log_level, "propagate": False},
            "uvicorn.access": {
                "handlers": ["stdout"],
                "level": settings.log_level,
                "propagate": False,
                "filters": ["health_access"],
            },
            "sqlalchemy.engine": {
                "handlers": ["stdout"],
                "level": "INFO" if settings.debug else "WARNING",
                "propagate": False,
            },
        },
        "root": {"handlers": ["stdout"], "level": settings.log_level},
    }


def configure_logging(settings: Settings) -> None:
    """Apply the structured logging configuration to the root logging system."""
    logging.config.dictConfig(build_logging_config(settings))
