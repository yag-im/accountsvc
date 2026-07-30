"""Domain exceptions raised by the service and repository layers."""

from __future__ import annotations


class AccountsvcError(Exception):
    """Base class for all domain errors raised by the application."""


class UserNotFoundError(AccountsvcError):
    """Raised when a requested user does not exist."""

    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        super().__init__(f"User '{user_id}' was not found.")
