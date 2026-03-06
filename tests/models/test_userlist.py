"""
Test UserlistModel CRUD
=======================
"""

from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.database.models.userlist import (
    create_userlist,
    create_userlist_entry,
    list_userlist_entries,
    update_userlist,
)


async def test_create_with_entries(session: AsyncSession) -> None:
    """Create a userlist with an entry."""

    ul = await create_userlist(session, name="testusers")
    await create_userlist_entry(session, userlist_id=ul.id, username="admin", password_hash="$6$hash")

    entries = await list_userlist_entries(session, ul.id)
    assert len(entries) == 1
    assert entries[0].username == "admin"


async def test_update_name(session: AsyncSession) -> None:
    """Update userlist name."""

    ul = await create_userlist(session, name="old")
    updated = await update_userlist(session, ul, name="new")
    assert updated.name == "new"
