"""Pydantic models that define the public API contract."""

from __future__ import annotations

import datetime as dt
from typing import Any

from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    """Representation of a user returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str | None
    name: str | None
    tz: str
    apps_lib: dict[str, Any] | None
    dob: dt.date
    is_active: bool


class UserUpdate(BaseModel):
    """Full-replacement payload for ``PUT /users/{id}``.

    Every mutable field must be provided; nullable fields accept an explicit ``null``.
    """

    model_config = ConfigDict(extra="forbid")

    email: str | None
    name: str | None
    tz: str
    apps_lib: dict[str, Any] | None
    dob: dt.date
    is_active: bool


class UserPatch(BaseModel):
    """Partial-update payload for ``PATCH /users/{id}``.

    Only fields the client sends are applied. Sending ``null`` on a nullable field
    clears it; omitting a field leaves it unchanged.
    """

    model_config = ConfigDict(extra="forbid")

    email: str | None = None
    name: str | None = None
    tz: str | None = None
    apps_lib: dict[str, Any] | None = None
    dob: dt.date | None = None
    is_active: bool | None = None


class ProblemDetail(BaseModel):
    """RFC 9457 ``application/problem+json`` error representation."""

    type: str = "about:blank"
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None
