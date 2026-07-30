"""FastAPI dependency-injection providers.

These wire the persistence and service layers together and expose database
sessions and settings to the API through ``Depends`` without any global state.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from accountsvc.core.config import Settings, get_settings
from accountsvc.repositories.health import HealthRepository
from accountsvc.repositories.user import UserRepository
from accountsvc.services.health_service import HealthService
from accountsvc.services.user_service import UserService


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield a database session bound to the application's session factory.

    Commits on success so writes performed by the request handler are persisted.
    Rolls back if the handler raises, then re-raises the exception.
    """
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.db_sessionmaker
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()


SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


def get_user_repository(session: SessionDep) -> UserRepository:
    return UserRepository(session)


def get_user_service(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(repository)


def get_health_repository(session: SessionDep) -> HealthRepository:
    return HealthRepository(session)


def get_health_service(
    repository: Annotated[HealthRepository, Depends(get_health_repository)],
) -> HealthService:
    return HealthService(repository)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
HealthServiceDep = Annotated[HealthService, Depends(get_health_service)]
