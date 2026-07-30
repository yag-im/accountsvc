"""Unit tests for the structured JSON log formatter."""

from __future__ import annotations

import json
import logging

from accountsvc.core.logging import JsonFormatter

_REQUIRED_FIELDS = (
    "timestamp",
    "severity",
    "service",
    "environment",
    "request_id",
    "trace_id",
    "span_id",
    "message",
)


def _make_record() -> logging.LogRecord:
    return logging.LogRecord(
        name="accountsvc.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )


def test_formatter_emits_required_fields() -> None:
    formatter = JsonFormatter(service="accountsvc", environment="test")

    payload = json.loads(formatter.format(_make_record()))

    for field in _REQUIRED_FIELDS:
        assert field in payload
    assert payload["message"] == "hello world"
    assert payload["severity"] == "INFO"
    assert payload["service"] == "accountsvc"
    assert payload["environment"] == "test"


def test_formatter_includes_extra_attributes() -> None:
    formatter = JsonFormatter(service="accountsvc", environment="test")
    record = _make_record()
    record.http_status = 200

    payload = json.loads(formatter.format(record))

    assert payload["http_status"] == 200
