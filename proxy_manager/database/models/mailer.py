"""
Mailer model
============
"""

import logging

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from proxy_manager.database.models.base import Base


class MailerSection(Base):
    """HAProxy 'mailers' section."""

    __tablename__ = 'mailer_sections'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Primary key."""

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    """Unique name identifier."""

    timeout_mail: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    """Timeout for SMTP mail delivery."""

    comment: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """Optional user comment."""

    extra_options: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """Additional HAProxy directives (free-form text)."""

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""

        return f'<MailerSection(id={self.id}, name={self.name!r})>'


class MailerEntry(Base):
    """A mailer entry within a mailers section."""

    __tablename__ = 'mailer_entries'
    __table_args__ = (UniqueConstraint('mailer_section_id', 'name', name='uq_mailer_entry_name'),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Primary key."""

    mailer_section_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('mailer_sections.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    """Foreign key to the parent mailer section."""

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    """Unique name identifier."""

    address: Mapped[str] = mapped_column(String(255), nullable=False)
    """Server IP address or hostname."""

    port: Mapped[int] = mapped_column(Integer, nullable=False, default=25)
    """Server port number."""

    smtp_auth: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    """Enable SMTP authentication."""

    smtp_user: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    """SMTP authentication username."""

    smtp_password: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    """SMTP authentication password."""

    use_tls: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    """Enable TLS for SMTP connections."""

    use_starttls: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    """Enable STARTTLS upgrade for SMTP."""

    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    """Display ordering index."""

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""

        return f'<MailerEntry(id={self.id}, name={self.name!r})>'


async def list_mailer_sections(session: AsyncSession) -> list[MailerSection]:
    """Return all mailer sections ordered by name."""

    result = await session.execute(select(MailerSection).order_by(MailerSection.name))
    return list(result.scalars().all())


async def get_mailer_section(session: AsyncSession, section_id: int) -> MailerSection | None:
    """Fetch a single mailer section by primary key."""

    return await session.get(MailerSection, section_id)


async def get_mailer_section_by_name(session: AsyncSession, name: str) -> MailerSection | None:
    """Fetch a single mailer section by its unique name."""

    result = await session.execute(select(MailerSection).where(MailerSection.name == name))
    return result.scalar_one_or_none()


async def create_mailer_section(session: AsyncSession, **kwargs: object) -> MailerSection:
    """Create and persist a new mailer section."""

    obj = MailerSection(**kwargs)
    session.add(obj)

    await session.commit()
    await session.refresh(obj)

    return obj


async def update_mailer_section(session: AsyncSession, obj: MailerSection, **kwargs: object) -> MailerSection:
    """Update an existing mailer section with the given field values."""

    allowed = {c.name for c in MailerSection.__table__.columns} - {'id'}
    unknown = set(kwargs) - allowed
    if unknown:
        logging.getLogger(__name__).warning('update_mailer_section: ignoring unknown fields: %s', unknown)
    for k, v in kwargs.items():
        if k in allowed:
            setattr(obj, k, v)

    await session.commit()
    await session.refresh(obj)

    return obj


async def delete_mailer_section(session: AsyncSession, obj: MailerSection) -> None:
    """Delete a mailer section from the database."""

    await session.delete(obj)
    await session.commit()


async def delete_all_mailer_sections(session: AsyncSession) -> None:
    """Delete all mailer sections and their entries."""

    await session.execute(delete(MailerEntry))
    await session.execute(delete(MailerSection))
    await session.commit()


async def get_mailer_entry(session: AsyncSession, entry_id: int) -> MailerEntry | None:
    """Fetch a single mailer entry by primary key."""

    return await session.get(MailerEntry, entry_id)


async def list_mailer_entries(session: AsyncSession, section_id: int) -> list[MailerEntry]:
    """Return all entries for a given mailer section."""

    result = await session.execute(select(MailerEntry).where(MailerEntry.mailer_section_id == section_id).order_by(MailerEntry.sort_order, MailerEntry.id))
    return list(result.scalars().all())


async def create_mailer_entry(session: AsyncSession, **kwargs: object) -> MailerEntry:
    """Create and persist a new mailer entry."""

    obj = MailerEntry(**kwargs)
    session.add(obj)

    await session.commit()
    await session.refresh(obj)

    return obj


async def update_mailer_entry(session: AsyncSession, obj: MailerEntry, **kwargs: object) -> MailerEntry:
    """Update an existing mailer entry."""

    allowed = {c.name for c in MailerEntry.__table__.columns} - {'id', 'mailer_section_id'}
    unknown = set(kwargs) - allowed
    if unknown:
        logging.getLogger(__name__).warning('update_mailer_entry: ignoring unknown fields: %s', unknown)
    for k, v in kwargs.items():
        if k in allowed:
            setattr(obj, k, v)

    await session.commit()
    await session.refresh(obj)

    return obj


async def delete_mailer_entry(session: AsyncSession, obj: MailerEntry) -> None:
    """Delete a mailer entry from the database."""

    await session.delete(obj)
    await session.commit()
