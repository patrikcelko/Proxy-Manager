"""
HTTP Errors model
=================
"""

from sqlalchemy import ForeignKey, Integer, String, Text, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from proxy_manager.database.models.base import Base


class HttpErrorsSection(Base):
    """HAProxy 'http-errors' named section."""

    __tablename__ = "http_errors_sections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Primary key."""

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    """Unique name identifier."""

    comment: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """Optional user comment."""

    extra_options: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """Additional HAProxy directives (free-form text)."""

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""

        return f"<HttpErrorsSection(id={self.id}, name={self.name!r})>"


class HttpErrorEntry(Base):
    """A single errorfile / errorloc directive within http-errors."""

    __tablename__ = "http_error_entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Primary key."""

    section_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("http_errors_sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    """Foreign key to the parent http-errors section."""

    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    """HTTP status code."""

    type: Mapped[str] = mapped_column(String(20), nullable=False, default="errorfile")
    """Error response type (`errorfile`, `errorloc`, etc.)."""

    value: Mapped[str] = mapped_column(Text, nullable=False)  # file path or URL
    """Directive value."""

    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    """Display ordering index."""

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""

        return f"<HttpErrorEntry(id={self.id}, status={self.status_code})>"


async def list_http_errors_sections(session: AsyncSession) -> list[HttpErrorsSection]:
    """Return all http-errors sections ordered by name."""

    result = await session.execute(select(HttpErrorsSection).order_by(HttpErrorsSection.name))
    return list(result.scalars().all())


async def get_http_errors_section(session: AsyncSession, section_id: int) -> HttpErrorsSection | None:
    """Fetch a single http-errors section by primary key."""

    return await session.get(HttpErrorsSection, section_id)


async def get_http_errors_section_by_name(session: AsyncSession, name: str) -> HttpErrorsSection | None:
    """Fetch a single http-errors section by its unique name."""

    result = await session.execute(select(HttpErrorsSection).where(HttpErrorsSection.name == name))
    return result.scalar_one_or_none()


async def create_http_errors_section(session: AsyncSession, **kwargs: object) -> HttpErrorsSection:
    """Create and persist a new http-errors section."""

    obj = HttpErrorsSection(**kwargs)
    session.add(obj)

    await session.commit()
    await session.refresh(obj)

    return obj


async def update_http_errors_section(
    session: AsyncSession,
    obj: HttpErrorsSection,
    **kwargs: object,
) -> HttpErrorsSection:
    """Update an existing http-errors section."""

    allowed = {c.name for c in HttpErrorsSection.__table__.columns} - {"id"}
    for k, v in kwargs.items():
        if k in allowed:
            setattr(obj, k, v)

    await session.commit()
    await session.refresh(obj)

    return obj


async def delete_http_errors_section(session: AsyncSession, obj: HttpErrorsSection) -> None:
    """Delete an http-errors section from the database."""

    await session.delete(obj)
    await session.commit()


async def delete_all_http_errors_sections(session: AsyncSession) -> None:
    """Delete all http-errors sections and their entries."""

    await session.execute(delete(HttpErrorEntry))
    await session.execute(delete(HttpErrorsSection))
    await session.commit()


# Entries
async def get_http_error_entry(session: AsyncSession, entry_id: int) -> HttpErrorEntry | None:
    """Fetch a single http-error entry by primary key."""

    return await session.get(HttpErrorEntry, entry_id)


async def list_http_error_entries(session: AsyncSession, section_id: int) -> list[HttpErrorEntry]:
    """Return all entries for a given http-errors section."""

    result = await session.execute(
        select(HttpErrorEntry)
        .where(HttpErrorEntry.section_id == section_id)
        .order_by(HttpErrorEntry.sort_order, HttpErrorEntry.id)
    )

    return list(result.scalars().all())


async def create_http_error_entry(session: AsyncSession, **kwargs: object) -> HttpErrorEntry:
    """Create and persist a new http-error entry."""

    obj = HttpErrorEntry(**kwargs)
    session.add(obj)

    await session.commit()
    await session.refresh(obj)

    return obj


async def update_http_error_entry(session: AsyncSession, obj: HttpErrorEntry, **kwargs: object) -> HttpErrorEntry:
    """Update an existing http-error entry."""

    allowed = {c.name for c in HttpErrorEntry.__table__.columns} - {"id"}
    for k, v in kwargs.items():
        if k in allowed:
            setattr(obj, k, v)

    await session.commit()
    await session.refresh(obj)

    return obj


async def delete_http_error_entry(session: AsyncSession, obj: HttpErrorEntry) -> None:
    """Delete an http-error entry from the database."""

    await session.delete(obj)
    await session.commit()
