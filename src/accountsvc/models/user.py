"""ORM model for the ``accounts.users`` table."""

from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import Boolean, Date, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from accountsvc.models.base import Base


class User(Base):
    """A user account managed by the service."""

    __tablename__ = "users"
    __table_args__ = {"schema": "accounts"}  # noqa: RUF012 -- SQLAlchemy special attribute

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    tz: Mapped[str] = mapped_column(Text, server_default="UTC")
    apps_lib: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    dob: Mapped[dt.date] = mapped_column(Date, server_default=func.current_date())
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="TRUE")
