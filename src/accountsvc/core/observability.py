"""Helpers that expose the active OpenTelemetry span context to the application."""

from __future__ import annotations

from opentelemetry import trace


def current_trace_context() -> tuple[str | None, str | None]:
    """Return the active ``(trace_id, span_id)`` as zero-padded hex strings.

    When no valid span is active (for example, when tracing is disabled) both
    elements are ``None``.
    """
    span_context = trace.get_current_span().get_span_context()
    if not span_context.is_valid:
        return None, None
    return format(span_context.trace_id, "032x"), format(span_context.span_id, "016x")
