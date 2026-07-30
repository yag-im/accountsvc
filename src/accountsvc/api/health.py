"""Liveness and readiness probe endpoints.

Liveness reflects process responsiveness only and never touches external
dependencies. Readiness additionally verifies database connectivity so that a
database outage drains traffic instead of triggering pod restarts.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Response, status
from sqlalchemy.exc import SQLAlchemyError

from accountsvc.api.dependencies import HealthServiceDep

logger = logging.getLogger("accountsvc.health")

router = APIRouter(tags=["health"])


@router.get("/healthz", summary="Liveness probe", status_code=status.HTTP_200_OK)
async def liveness() -> dict[str, str]:
    """Report process liveness without checking external dependencies."""
    return {"status": "ok"}


@router.get("/readyz", summary="Readiness probe")
async def readiness(service: HealthServiceDep, response: Response) -> dict[str, str]:
    """Report readiness, including database connectivity."""
    try:
        await service.check_readiness()
    except SQLAlchemyError:
        logger.warning("readiness_check_failed", extra={"dependency": "database"})
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable", "database": "unavailable"}
    return {"status": "ok", "database": "ok"}
