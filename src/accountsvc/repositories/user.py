"""Repository encapsulating persistence operations for :class:`User`."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from accountsvc.models.user import User


class UserRepository:
    """Data-access operations for user records."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        """Return the user with the given id, or ``None`` if it does not exist."""
        return await self._session.get(User, user_id)

    async def update(self, user_id: int, values: dict[str, Any]) -> User | None:
        """Apply ``values`` to the user with ``user_id`` and flush.

        Returns the updated user, or ``None`` if no user exists with that id.
        Empty ``values`` is a no-op and returns the loaded user unchanged.
        """
        user = await self._session.get(User, user_id)
        if user is None:
            return None
        for key, value in values.items():
            setattr(user, key, value)
        await self._session.flush()
        return user
