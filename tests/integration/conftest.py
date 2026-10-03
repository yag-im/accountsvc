"""Fixtures for integration tests.

Integration tests run against the yag database on sqldb.yag.dc. The schema
is expected to already exist; tests only add and remove data. Each test executes inside
a transaction that is rolled back on teardown to guarantee isolation.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from dotenv import dotenv_values
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession, create_async_engine

from accountsvc.api.dependencies import get_db_session
from accountsvc.core.config import Settings
from accountsvc.main import create_app
from accountsvc.models.user import User


def _load_env() -> tuple[dict[str, str | None], dict[str, str | None]]:
    """Load ``.env`` and ``secrets.env`` and validate the required keys.

    Called lazily from fixtures so that merely importing this module (e.g. during
    pytest collection in environments without the env files) does not fail.
    """
    env = dotenv_values(".env")
    secrets = dotenv_values("secrets.env")
    required_env = ("APP_DB_USER", "APP_DB_HOST", "APP_DB_NAME")
    required_secrets = ("APP_DB_PASSWORD",)
    missing = [k for k in required_env if not env.get(k)] + [k for k in required_secrets if not secrets.get(k)]
    if missing:
        pytest.skip(
            "Integration tests require the following variables in .env/secrets.env: " + ", ".join(missing),
            allow_module_level=True,
        )
    return env, secrets


@pytest.fixture
def settings() -> Settings:
    env, secrets = _load_env()
    return Settings(
        _env_file=None,  # pyright: ignore[reportCallIssue]
        environment="local",
        db_host=env["APP_DB_HOST"],
        db_user=env["APP_DB_USER"],
        db_password=secrets["APP_DB_PASSWORD"],
        db_name=env["APP_DB_NAME"],
    )


@pytest_asyncio.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    env, secrets = _load_env()
    url = (
        f"postgresql+psycopg://{env['APP_DB_USER']}:{secrets['APP_DB_PASSWORD']}"
        f"@{env['APP_DB_HOST']}/{env['APP_DB_NAME']}"
    )
    engine = create_async_engine(url)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def db_connection(engine: AsyncEngine) -> AsyncIterator[AsyncConnection]:
    connection = await engine.connect()
    transaction = await connection.begin()
    try:
        yield connection
    finally:
        if transaction.is_active:
            await transaction.rollback()
        await connection.close()


@pytest_asyncio.fixture
async def db_session(db_connection: AsyncConnection) -> AsyncIterator[AsyncSession]:
    session = AsyncSession(
        bind=db_connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield session
    finally:
        await session.close()


@pytest_asyncio.fixture
async def client(settings: Settings, db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    app = create_app(settings)

    async def _override_get_db_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db_session] = _override_get_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http_client:
        yield http_client


@pytest_asyncio.fixture
async def seeded_user(db_session: AsyncSession) -> User:
    user = User(email="ada@yag.dc", name="Ada Lovelace")
    db_session.add(user)
    await db_session.flush()
    return user
