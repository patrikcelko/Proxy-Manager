"""
Tests GlobalSettingModel CRUD
=============================
"""

from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.database.models.global_setting import (
    create_global_setting,
    delete_all_global_settings,
    delete_global_setting,
    list_global_settings,
    update_global_setting,
)


async def test_create_and_list(session: AsyncSession) -> None:
    """Create two global settings and list them."""

    s1 = await create_global_setting(session, directive="log", value="127.0.0.1 local0")
    s2 = await create_global_setting(session, directive="maxconn", value="4096")
    rows = await list_global_settings(session)
    assert len(rows) == 2
    assert s1.directive == "log"
    assert s2.value == "4096"


async def test_update(session: AsyncSession) -> None:
    """Update a global setting value."""

    s = await create_global_setting(session, directive="maxconn", value="1024")
    updated = await update_global_setting(session, s, value="8192")
    assert updated.value == "8192"


async def test_delete(session: AsyncSession) -> None:
    """Delete a single global setting."""

    s = await create_global_setting(session, directive="test", value="v")
    await delete_global_setting(session, s)
    rows = await list_global_settings(session)
    assert len(rows) == 0


async def test_delete_all(session: AsyncSession) -> None:
    """Delete all global settings at once."""

    await create_global_setting(session, directive="a", value="1")
    await create_global_setting(session, directive="b", value="2")
    await delete_all_global_settings(session)
    assert len(await list_global_settings(session)) == 0
