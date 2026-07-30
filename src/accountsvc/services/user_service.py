"""Business logic for user retrieval and lifecycle workflows."""

from __future__ import annotations

from accountsvc.exceptions import UserNotFoundError
from accountsvc.models.schemas import UserPatch, UserRead, UserUpdate
from accountsvc.repositories.user import UserRepository


class UserService:
    """Coordinate user-related business operations."""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def get_user(self, user_id: int) -> UserRead:
        """Return the user identified by ``user_id``.

        Raises:
            UserNotFoundError: If no user exists with the given id.
        """
        user = await self._repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return UserRead.model_validate(user)

    async def replace_user(self, user_id: int, data: UserUpdate) -> UserRead:
        """Replace every mutable field of ``user_id`` with the payload values.

        Raises:
            UserNotFoundError: If no user exists with the given id.
        """
        user = await self._repository.update(user_id, data.model_dump())
        if user is None:
            raise UserNotFoundError(user_id)
        return UserRead.model_validate(user)

    async def patch_user(self, user_id: int, data: UserPatch) -> UserRead:
        """Apply only the fields explicitly present in ``data``.

        Raises:
            UserNotFoundError: If no user exists with the given id.
        """
        changes = data.model_dump(exclude_unset=True)
        user = await self._repository.update(user_id, changes)
        if user is None:
            raise UserNotFoundError(user_id)
        return UserRead.model_validate(user)
