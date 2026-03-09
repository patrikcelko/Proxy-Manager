"""
Global setting model
====================
"""

from sqlalchemy import Integer, String, Text, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from proxy_manager.database.models.base import Base


class GlobalSetting(Base):
    """A single directive in the HAProxy 'global' section."""

    __tablename__ = 'global_settings'

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

        return f'<GlobalSetting(id={self.id}, directive={self.directive!r})>'


async def list_global_settings(session: AsyncSession) -> list[GlobalSetting]:
    """Return all global settings ordered by sort_order."""

    stmt = select(GlobalSetting).order_by(GlobalSetting.sort_order, GlobalSetting.id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_global_setting(session: AsyncSession, setting_id: int) -> GlobalSetting | None:
    """Fetch a single global setting by primary key."""

    return await session.get(GlobalSetting, setting_id)


async def create_global_setting(session: AsyncSession, *, directive: str, value: str, comment: str | None = None, sort_order: int = 0) -> GlobalSetting:
    """Create and persist a new global setting."""

    setting = GlobalSetting(directive=directive, value=value, comment=comment, sort_order=sort_order)
    session.add(setting)

    await session.commit()
    await session.refresh(setting)

    return setting


async def update_global_setting(
    session: AsyncSession,
    setting: GlobalSetting,
    *,
    directive: str | None = None,
    value: str | None = None,
    comment: str | None = None,
    sort_order: int | None = None,
    fields_set: frozenset[str] | None = None,
) -> GlobalSetting:
    """Update an existing global setting."""

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


async def delete_global_setting(session: AsyncSession, setting: GlobalSetting) -> None:
    """Delete a global setting from the database."""

    await session.delete(setting)
    await session.commit()


async def delete_all_global_settings(session: AsyncSession) -> None:
    """Delete all global settings."""

    await session.execute(delete(GlobalSetting))
    await session.commit()
