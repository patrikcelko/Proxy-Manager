"""
Cache model
===========
HAProxy `cache` section - HTTP response caching.
"""

from sqlalchemy import Integer, String, Text, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from proxy_manager.database.models.base import Base


class CacheSection(Base):
    """HAProxy 'cache' section."""

    __tablename__ = "cache_sections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Primary key."""

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    """Unique name identifier."""

    total_max_size: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)  # MB
    """Total cache size in megabytes."""

    max_object_size: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)  # bytes
    """Maximum cached object size in bytes."""

    max_age: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)  # seconds
    """Maximum cache entry age in seconds."""

    max_secondary_entries: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    """Maximum number of secondary entries."""

    process_vary: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)  # 0 or 1
    """Process Vary header (1 = enabled)."""

    comment: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """Optional user comment."""

    extra_options: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """Additional HAProxy directives (free-form text)."""

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""

        return f"<CacheSection(id={self.id}, name={self.name!r})>"


async def list_cache_sections(session: AsyncSession) -> list[CacheSection]:
    """Return all cache sections ordered by name."""

    result = await session.execute(select(CacheSection).order_by(CacheSection.name))
    return list(result.scalars().all())


async def get_cache_section(session: AsyncSession, section_id: int) -> CacheSection | None:
    """Fetch a single cache section by primary key."""

    return await session.get(CacheSection, section_id)


async def get_cache_section_by_name(session: AsyncSession, name: str) -> CacheSection | None:
    """Fetch a single cache section by its unique name."""

    result = await session.execute(select(CacheSection).where(CacheSection.name == name))
    return result.scalar_one_or_none()


async def create_cache_section(session: AsyncSession, **kwargs: object) -> CacheSection:
    """Create and persist a new cache section."""

    obj = CacheSection(**kwargs)
    session.add(obj)

    await session.commit()
    await session.refresh(obj)

    return obj


async def update_cache_section(session: AsyncSession, obj: CacheSection, **kwargs: object) -> CacheSection:
    """Update an existing cache section."""

    allowed = {c.name for c in CacheSection.__table__.columns} - {"id"}
    for k, v in kwargs.items():
        if k in allowed:
            setattr(obj, k, v)

    await session.commit()
    await session.refresh(obj)

    return obj


async def delete_cache_section(session: AsyncSession, obj: CacheSection) -> None:
    """Delete a cache section from the database."""

    await session.delete(obj)
    await session.commit()


async def delete_all_cache_sections(session: AsyncSession) -> None:
    """Delete all cache sections."""

    await session.execute(delete(CacheSection))
    await session.commit()
