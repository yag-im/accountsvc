"""Unit tests for the user service using a stubbed repository."""

from __future__ import annotations

import datetime as dt
from typing import Any

import pytest

from accountsvc.exceptions import UserNotFoundError
from accountsvc.models.schemas import UserPatch, UserUpdate
from accountsvc.models.user import User
from accountsvc.services.user_service import UserService


class _StubUserRepository:
    def __init__(self, user: User | None) -> None:
        self._user = user
        self.requested_id: int | None = None
        self.updated_id: int | None = None
        self.applied_values: dict[str, Any] | None = None

    async def get_by_id(self, user_id: int) -> User | None:
        self.requested_id = user_id
        return self._user

    async def update(self, user_id: int, values: dict[str, Any]) -> User | None:
        self.updated_id = user_id
        self.applied_values = values
        if self._user is None:
            return None
        for key, value in values.items():
            setattr(self._user, key, value)
        return self._user


def _make_user() -> User:
    return User(
        id=42,
        email="grace@yag.dc",
        name="Grace Hopper",
        tz="UTC",
        apps_lib=None,
        dob=dt.date(1906, 12, 9),
        is_active=True,
    )


async def test_get_user_returns_contract() -> None:
    repository = _StubUserRepository(_make_user())
    service = UserService(repository)  # type: ignore[arg-type]

    result = await service.get_user(42)

    assert result.id == 42
    assert result.name == "Grace Hopper"
    assert repository.requested_id == 42


async def test_get_user_missing_raises() -> None:
    service = UserService(_StubUserRepository(None))  # type: ignore[arg-type]

    with pytest.raises(UserNotFoundError):
        await service.get_user(999)


async def test_replace_user_applies_all_fields() -> None:
    repository = _StubUserRepository(_make_user())
    service = UserService(repository)  # type: ignore[arg-type]

    payload = UserUpdate(
        email="ada@yag.dc",
        name="Ada Lovelace",
        tz="Europe/London",
        apps_lib={"editor": "vscode"},
        dob=dt.date(1815, 12, 10),
        is_active=False,
    )
    result = await service.replace_user(42, payload)

    assert repository.updated_id == 42
    assert repository.applied_values == {
        "email": "ada@yag.dc",
        "name": "Ada Lovelace",
        "tz": "Europe/London",
        "apps_lib": {"editor": "vscode"},
        "dob": dt.date(1815, 12, 10),
        "is_active": False,
    }
    assert result.name == "Ada Lovelace"
    assert result.is_active is False


async def test_replace_user_missing_raises() -> None:
    service = UserService(_StubUserRepository(None))  # type: ignore[arg-type]

    payload = UserUpdate(
        email=None,
        name=None,
        tz="UTC",
        apps_lib=None,
        dob=dt.date(2000, 1, 1),
        is_active=True,
    )
    with pytest.raises(UserNotFoundError):
        await service.replace_user(999, payload)


async def test_patch_user_only_sets_provided_fields() -> None:
    repository = _StubUserRepository(_make_user())
    service = UserService(repository)  # type: ignore[arg-type]

    result = await service.patch_user(42, UserPatch(name="Amazing Grace"))

    assert repository.applied_values == {"name": "Amazing Grace"}
    assert result.name == "Amazing Grace"
    # untouched fields remain their original values
    assert result.tz == "UTC"
    assert result.is_active is True


async def test_patch_user_can_clear_nullable_field() -> None:
    repository = _StubUserRepository(_make_user())
    service = UserService(repository)  # type: ignore[arg-type]

    result = await service.patch_user(42, UserPatch(email=None))

    assert repository.applied_values == {"email": None}
    assert result.email is None


async def test_patch_user_empty_body_is_noop() -> None:
    repository = _StubUserRepository(_make_user())
    service = UserService(repository)  # type: ignore[arg-type]

    result = await service.patch_user(42, UserPatch())

    assert repository.applied_values == {}
    assert result.name == "Grace Hopper"


async def test_patch_user_missing_raises() -> None:
    service = UserService(_StubUserRepository(None))  # type: ignore[arg-type]

    with pytest.raises(UserNotFoundError):
        await service.patch_user(999, UserPatch(name="Nobody"))
