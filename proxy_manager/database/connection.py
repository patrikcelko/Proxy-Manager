"""
Connection utilities
====================
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from proxy_manager.utilities.settings import DATABASE_URL

__all__ = ['async_session_factory', 'engine', 'get_session']

engine = create_async_engine(DATABASE_URL, echo=False)

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession]:
    """FastAPI dependency that yields an `AsyncSession`."""

    async with async_session_factory() as session:
        yield session
