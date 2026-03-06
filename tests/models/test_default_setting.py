"""
Tests DefaultSettingModel CRUD
==============================
"""

from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.database.models.default_setting import (
    create_default_setting,
    delete_all_default_settings,
    list_default_settings,
)


async def test_create_and_list(session: AsyncSession) -> None:
    """Create default settings and list them."""

    await create_default_setting(session, directive="mode", value="http")
    await create_default_setting(session, directive="timeout connect", value="5000")

    rows = await list_default_settings(session)
    assert len(rows) == 2


async def test_delete_all(session: AsyncSession) -> None:
    """Delete all default settings at once."""

    await create_default_setting(session, directive="x", value="y")
    await delete_all_default_settings(session)
    assert len(await list_default_settings(session)) == 0
