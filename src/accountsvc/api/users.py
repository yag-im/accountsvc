"""User-facing endpoints for the v1 API."""

from __future__ import annotations

from fastapi import APIRouter, status

from accountsvc.api.dependencies import UserServiceDep
from accountsvc.models.schemas import UserPatch, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a user by identifier",
)
async def get_user(user_id: int, service: UserServiceDep) -> UserRead:
    """Return the user identified by ``user_id``."""
    return await service.get_user(user_id)


@router.put(
    "/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Replace a user in full",
)
async def replace_user(user_id: int, payload: UserUpdate, service: UserServiceDep) -> UserRead:
    """Replace every mutable field of ``user_id`` with the request body."""
    return await service.replace_user(user_id, payload)


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Partially update a user",
)
async def patch_user(user_id: int, payload: UserPatch, service: UserServiceDep) -> UserRead:
    """Apply only the fields present in the request body to ``user_id``."""
    return await service.patch_user(user_id, payload)
