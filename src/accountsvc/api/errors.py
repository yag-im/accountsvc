"""Centralized exception handling producing ``application/problem+json`` responses."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from accountsvc.exceptions import UserNotFoundError
from accountsvc.models.schemas import ProblemDetail

logger = logging.getLogger("accountsvc.errors")

PROBLEM_JSON_MEDIA_TYPE = "application/problem+json"
_ERROR_BASE_URI = "https://errors.yag.dc"


def _problem_response(problem: ProblemDetail, extra: dict[str, Any] | None = None) -> JSONResponse:
    content = problem.model_dump(exclude_none=True)
    if extra:
        content.update(extra)
    return JSONResponse(
        status_code=problem.status,
        content=content,
        media_type=PROBLEM_JSON_MEDIA_TYPE,
    )


def _serialize_validation_errors(errors: Sequence[Any]) -> list[dict[str, Any]]:
    return [
        {
            "location": list(error.get("loc", ())),
            "message": error.get("msg", ""),
            "type": error.get("type", ""),
        }
        for error in errors
    ]


async def handle_user_not_found(request: Request, exc: UserNotFoundError) -> JSONResponse:
    problem = ProblemDetail(
        type=f"{_ERROR_BASE_URI}/user-not-found",
        title="User not found",
        status=status.HTTP_404_NOT_FOUND,
        detail=str(exc),
        instance=request.url.path,
    )
    return _problem_response(problem)


async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    problem = ProblemDetail(
        type=f"{_ERROR_BASE_URI}/validation-error",
        title="Request validation failed",
        status=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="One or more request parameters failed validation.",
        instance=request.url.path,
    )
    return _problem_response(problem, {"errors": _serialize_validation_errors(exc.errors())})


async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    problem = ProblemDetail(
        title=HTTPStatus(exc.status_code).phrase,
        status=exc.status_code,
        detail=exc.detail if isinstance(exc.detail, str) else None,
        instance=request.url.path,
    )
    return _problem_response(problem)


async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception", extra={"http_path": request.url.path})
    problem = ProblemDetail(
        title="Internal Server Error",
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred while processing the request.",
        instance=request.url.path,
    )
    return _problem_response(problem)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all problem+json exception handlers on the application."""
    app.add_exception_handler(UserNotFoundError, handle_user_not_found)  # pyright: ignore[reportArgumentType]
    app.add_exception_handler(RequestValidationError, handle_validation_error)  # pyright: ignore[reportArgumentType]
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)  # pyright: ignore[reportArgumentType]
    app.add_exception_handler(Exception, handle_unexpected_error)
