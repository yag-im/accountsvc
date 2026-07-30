"""ASGI middleware for request-id propagation and structured access logging.

This middleware assigns (or honours) an ``X-Request-ID`` per request, exposes it
to the logging system via a context variable, and emits one structured access log
line per request. Health-check endpoints are intentionally excluded so probe
traffic does not flood the logs.
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from accountsvc.core.context import request_id_ctx

_REQUEST_ID_HEADER = b"x-request-id"
_HEALTH_PATHS = frozenset({"/healthz", "/readyz"})

access_logger = logging.getLogger("accountsvc.access")


class RequestContextMiddleware:
    """Attach a request id to each request and log access records."""

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        headers = dict(scope["headers"])
        incoming = headers.get(_REQUEST_ID_HEADER)
        request_id = incoming.decode("latin-1") if incoming else uuid.uuid4().hex
        token = request_id_ctx.set(request_id)

        status_code = 500
        start = time.perf_counter()

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                message.setdefault("headers", []).append((_REQUEST_ID_HEADER, request_id.encode("latin-1")))
            await send(message)

        try:
            await self._app(scope, receive, send_wrapper)
        finally:
            path = scope.get("path", "")
            if path not in _HEALTH_PATHS:
                access_logger.info(
                    "http_request",
                    extra={
                        "http_method": scope.get("method"),
                        "http_path": path,
                        "http_status": status_code,
                        "duration_ms": round((time.perf_counter() - start) * 1000, 2),
                    },
                )
            request_id_ctx.reset(token)
