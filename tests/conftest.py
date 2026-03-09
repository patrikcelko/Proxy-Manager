"""
Test fixtures
=============
"""

import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Set SECRET_KEY before importing any proxy_manager modules
if 'SECRET_KEY' not in os.environ:
    os.environ['SECRET_KEY'] = 'test-secret-key-for-pytest-do-not-use-in-production'

from proxy_manager import app
from proxy_manager.database.connection import get_session
from proxy_manager.database.models import Base
from proxy_manager.database.models.user import User, create_user
from proxy_manager.utilities.auth import create_access_token, hash_password

TEST_DATABASE_URL = 'sqlite+aiosqlite:///:memory:'

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(autouse=True)
async def _setup_db() -> AsyncGenerator[None]:  # type: ignore
    """Create all tables before each test and drop them after."""

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _override_get_session() -> AsyncGenerator[AsyncSession]:
    """Override get session."""

    async with TestSessionFactory() as session:
        yield session


@pytest.fixture()
async def client() -> AsyncGenerator[AsyncClient]:
    """Async HTTP client wired to the FastAPI app with test DB."""

    app.dependency_overrides[get_session] = _override_get_session
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture()
async def session() -> AsyncGenerator[AsyncSession]:
    """Raw async session for direct DB operations in tests."""

    async with TestSessionFactory() as s:
        yield s


@pytest.fixture()
async def user(session: AsyncSession) -> User:
    """Create a test user in the database."""

    pw_hash = hash_password('testpassword123')
    return await create_user(session, email='test@example.com', name='Test User', password_hash=pw_hash)


@pytest.fixture()
async def auth_token(user: User) -> str:
    """Create a JWT authentication token for the test user."""

    return create_access_token(user.id)


@pytest.fixture()
async def auth_client(user: User, auth_token: str) -> AsyncGenerator[AsyncClient]:
    """Async HTTP client with authentication headers."""

    app.dependency_overrides[get_session] = _override_get_session
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url='http://test',
        headers={'Authorization': f'Bearer {auth_token}'},
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
