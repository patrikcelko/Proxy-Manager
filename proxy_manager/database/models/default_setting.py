"""
Default setting model
=====================
"""

from sqlalchemy import Integer, String, Text, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from proxy_manager.database.models.base import Base


class DefaultSetting(Base):
    """A single directive in the HAProxy 'defaults' section."""

    __tablename__ = 'default_settings'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Primary key."""

    directive: Mapped[str] = mapped_column(String(255), nullable=False)
    """HAProxy directive name."""

    value: Mapped[str] = mapped_column(Text, nullable=False, default='')
    """Directive value."""

    comment: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """Optional user comment."""

    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    """Display ordering index."""

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""

        return f'<DefaultSetting(id={self.id}, directive={self.directive!r})>'


async def list_default_settings(session: AsyncSession) -> list[DefaultSetting]:
    """Return all default settings ordered by sort_order."""

    stmt = select(DefaultSetting).order_by(DefaultSetting.sort_order, DefaultSetting.id)
    result = await session.execute(stmt)

    return list(result.scalars().all())


async def get_default_setting(session: AsyncSession, setting_id: int) -> DefaultSetting | None:
    """Fetch a single default setting by primary key."""

    return await session.get(DefaultSetting, setting_id)


async def create_default_setting(session: AsyncSession, *, directive: str, value: str, comment: str | None = None, sort_order: int = 0) -> DefaultSetting:
    """Create and persist a new default setting."""

    setting = DefaultSetting(directive=directive, value=value, comment=comment, sort_order=sort_order)
    session.add(setting)

    await session.commit()
    await session.refresh(setting)

    return setting


async def update_default_setting(
    session: AsyncSession,
    setting: DefaultSetting,
    *,
    directive: str | None = None,
    value: str | None = None,
    comment: str | None = None,
    sort_order: int | None = None,
    fields_set: frozenset[str] | None = None,
) -> DefaultSetting:
    """Update an existing default setting."""

    if directive is not None:
        setting.directive = directive

    if value is not None:
        setting.value = value

    if fields_set and 'comment' in fields_set or comment is not None:
        setting.comment = comment

    if sort_order is not None:
        setting.sort_order = sort_order

    await session.commit()
    await session.refresh(setting)

    return setting


async def delete_default_setting(session: AsyncSession, setting: DefaultSetting) -> None:
    """Delete a default setting from the database."""

    await session.delete(setting)
    await session.commit()


async def delete_all_default_settings(session: AsyncSession) -> None:
    """Delete all default settings."""

    await session.execute(delete(DefaultSetting))
    await session.commit()
