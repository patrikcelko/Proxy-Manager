"""
Userlist models
===============
"""

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from proxy_manager.database.models.base import Base


class Userlist(Base):
    """HAProxy userlist definition."""

    __tablename__ = 'userlists'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Primary key."""

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    """Unique name identifier."""

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""

        return f'<Userlist(id={self.id}, name={self.name!r})>'


class UserlistEntry(Base):
    """A user entry within a HAProxy userlist."""

    __tablename__ = 'userlist_entries'
    __table_args__ = (UniqueConstraint('userlist_id', 'username', name='uq_userlist_entry_username'),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Primary key."""

    userlist_id: Mapped[int] = mapped_column(ForeignKey('userlists.id', ondelete='CASCADE'), nullable=False, index=True)
    """Foreign key to the parent userlist."""

    username: Mapped[str] = mapped_column(String(255), nullable=False)
    """HAProxy userlist username."""

    password_hash: Mapped[str] = mapped_column(String(500), nullable=False)
    """Bcrypt-hashed password."""

    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    """Display ordering index."""

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""

        return f'<UserlistEntry(id={self.id}, username={self.username!r})>'


async def list_userlists(session: AsyncSession) -> list[Userlist]:
    """Return all userlists ordered by name."""

    stmt = select(Userlist).order_by(Userlist.name)
    result = await session.execute(stmt)

    return list(result.scalars().all())


async def get_userlist(session: AsyncSession, userlist_id: int) -> Userlist | None:
    """Fetch a single userlist by primary key."""

    return await session.get(Userlist, userlist_id)


async def get_userlist_by_name(session: AsyncSession, name: str) -> Userlist | None:
    """Fetch a single userlist by its unique name."""

    stmt = select(Userlist).where(Userlist.name == name)
    result = await session.execute(stmt)

    return result.scalar_one_or_none()


async def create_userlist(session: AsyncSession, *, name: str) -> Userlist:
    """Create and persist a new userlist."""

    ul = Userlist(name=name)
    session.add(ul)

    await session.commit()
    await session.refresh(ul)

    return ul


async def update_userlist(session: AsyncSession, ul: Userlist, *, name: str | None = None) -> Userlist:
    """Update an existing userlist."""

    if name is not None:
        ul.name = name

    await session.commit()
    await session.refresh(ul)

    return ul


async def delete_userlist(session: AsyncSession, ul: Userlist) -> None:
    """Delete a userlist from the database."""

    await session.delete(ul)
    await session.commit()


async def list_userlist_entries(session: AsyncSession, userlist_id: int) -> list[UserlistEntry]:
    """Return all entries for a given userlist."""

    stmt = select(UserlistEntry).where(UserlistEntry.userlist_id == userlist_id).order_by(UserlistEntry.sort_order, UserlistEntry.id)
    result = await session.execute(stmt)

    return list(result.scalars().all())


async def get_userlist_entry(session: AsyncSession, entry_id: int) -> UserlistEntry | None:
    """Fetch a single userlist entry by primary key."""

    return await session.get(UserlistEntry, entry_id)


async def create_userlist_entry(session: AsyncSession, *, userlist_id: int, username: str, password_hash: str, sort_order: int = 0) -> UserlistEntry:
    """Create and persist a new userlist entry."""

    entry = UserlistEntry(
        userlist_id=userlist_id,
        username=username,
        password_hash=password_hash,
        sort_order=sort_order,
    )
    session.add(entry)

    await session.commit()
    await session.refresh(entry)

    return entry


async def update_userlist_entry(
    session: AsyncSession,
    entry: UserlistEntry,
    *,
    username: str | None = None,
    password_hash: str | None = None,
    sort_order: int | None = None,
) -> UserlistEntry:
    """Update an existing userlist entry."""

    if username is not None:
        entry.username = username

    if password_hash is not None:
        entry.password_hash = password_hash

    if sort_order is not None:
        entry.sort_order = sort_order

    await session.commit()
    await session.refresh(entry)

    return entry


async def delete_userlist_entry(session: AsyncSession, entry: UserlistEntry) -> None:
    """Delete a userlist entry from the database."""

    await session.delete(entry)
    await session.commit()


async def delete_all_userlists(session: AsyncSession) -> None:
    """Delete all userlists and their entries."""

    await session.execute(delete(UserlistEntry))
    await session.execute(delete(Userlist))
    await session.commit()
