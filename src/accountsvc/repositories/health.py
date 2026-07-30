"""Repository that validates database connectivity for readiness checks."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class HealthRepository:
    """Lightweight database connectivity probe."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def check_database(self) -> None:
        """Execute a trivial query to confirm the database is reachable."""
        await self._session.execute(text("SELECT 1"))
