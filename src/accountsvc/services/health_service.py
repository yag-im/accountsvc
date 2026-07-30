"""Readiness workflow that verifies downstream dependencies."""

from __future__ import annotations

from accountsvc.repositories.health import HealthRepository


class HealthService:
    """Coordinate readiness checks for the service's dependencies."""

    def __init__(self, repository: HealthRepository) -> None:
        self._repository = repository

    async def check_readiness(self) -> None:
        """Verify that the database is reachable.

        Raises:
            sqlalchemy.exc.SQLAlchemyError: If the database cannot be queried.
        """
        await self._repository.check_database()
