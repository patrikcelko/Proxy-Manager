"""
Peer model
==========
"""

from sqlalchemy import ForeignKey, Integer, String, Text, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from proxy_manager.database.models.base import Base


class PeerSection(Base):
    """HAProxy 'peers' section."""

    __tablename__ = "peer_sections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Primary key."""

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    """Unique name identifier."""

    comment: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """Optional user comment."""

    extra_options: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """Additional HAProxy directives (free-form text)."""

    default_bind: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """Default bind address for peer connections."""

    default_server_options: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """Default server parameters applied to all servers."""

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""

        return f"<PeerSection(id={self.id}, name={self.name!r})>"


class PeerEntry(Base):
    """A peer entry within a peers section."""

    __tablename__ = "peer_entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Primary key."""

    peer_section_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("peer_sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    """Foreign key to the parent peer section."""

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    """Unique name identifier."""

    address: Mapped[str] = mapped_column(String(255), nullable=False)
    """Server IP address or hostname."""

    port: Mapped[int] = mapped_column(Integer, nullable=False, default=10000)
    """Server port number."""

    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    """Display ordering index."""

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""

        return f"<PeerEntry(id={self.id}, name={self.name!r})>"


async def list_peer_sections(session: AsyncSession) -> list[PeerSection]:
    """Return all peer sections ordered by name."""

    result = await session.execute(select(PeerSection).order_by(PeerSection.name))
    return list(result.scalars().all())


async def get_peer_section(session: AsyncSession, section_id: int) -> PeerSection | None:
    """Fetch a single peer section by primary key."""

    return await session.get(PeerSection, section_id)


async def get_peer_section_by_name(session: AsyncSession, name: str) -> PeerSection | None:
    """Fetch a single peer section by its unique name."""

    result = await session.execute(select(PeerSection).where(PeerSection.name == name))
    return result.scalar_one_or_none()


async def create_peer_section(session: AsyncSession, **kwargs: object) -> PeerSection:
    """Create and persist a new peer section."""

    obj = PeerSection(**kwargs)
    session.add(obj)

    await session.commit()
    await session.refresh(obj)

    return obj


async def update_peer_section(session: AsyncSession, obj: PeerSection, **kwargs: object) -> PeerSection:
    """Update an existing peer section with the given field values."""

    allowed = {c.name for c in PeerSection.__table__.columns} - {"id"}
    for k, v in kwargs.items():
        if k in allowed:
            setattr(obj, k, v)

    await session.commit()
    await session.refresh(obj)

    return obj


async def delete_peer_section(session: AsyncSession, obj: PeerSection) -> None:
    """Delete a peer section from the database."""

    await session.delete(obj)
    await session.commit()


async def delete_all_peer_sections(session: AsyncSession) -> None:
    """Delete all peer sections and their entries."""

    await session.execute(delete(PeerEntry))
    await session.execute(delete(PeerSection))
    await session.commit()


async def get_peer_entry(session: AsyncSession, entry_id: int) -> PeerEntry | None:
    """Fetch a single peer entry by primary key."""

    return await session.get(PeerEntry, entry_id)


async def list_peer_entries(session: AsyncSession, section_id: int) -> list[PeerEntry]:
    """Return all entries for a given peer section."""

    result = await session.execute(select(PeerEntry).where(PeerEntry.peer_section_id == section_id).order_by(PeerEntry.sort_order, PeerEntry.id))

    return list(result.scalars().all())


async def create_peer_entry(session: AsyncSession, **kwargs: object) -> PeerEntry:
    """Create and persist a new peer entry."""

    obj = PeerEntry(**kwargs)
    session.add(obj)

    await session.commit()
    await session.refresh(obj)

    return obj


async def update_peer_entry(session: AsyncSession, obj: PeerEntry, **kwargs: object) -> PeerEntry:
    """Update an existing peer entry."""

    allowed = {c.name for c in PeerEntry.__table__.columns} - {"id"}
    for k, v in kwargs.items():
        if k in allowed:
            setattr(obj, k, v)

    await session.commit()
    await session.refresh(obj)

    return obj


async def delete_peer_entry(session: AsyncSession, obj: PeerEntry) -> None:
    """Delete a peer entry from the database."""

    await session.delete(obj)
    await session.commit()
