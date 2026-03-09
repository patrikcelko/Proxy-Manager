"""
Tests PeerSectionModel/PeerEntryModel CRUD
==========================================
"""

from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.database.models.peer import (
    create_peer_entry,
    create_peer_section,
    delete_all_peer_sections,
    delete_peer_entry,
    delete_peer_section,
    get_peer_section,
    get_peer_section_by_name,
    list_peer_entries,
    list_peer_sections,
    update_peer_entry,
    update_peer_section,
)


async def test_create_and_list(session: AsyncSession) -> None:
    """Create a peer section and list all."""

    await create_peer_section(session, name='mycluster')
    rows = await list_peer_sections(session)

    assert len(rows) == 1
    assert rows[0].name == 'mycluster'


async def test_get_by_id_and_name(session: AsyncSession) -> None:
    """Get peer section by ID and by name."""

    p = await create_peer_section(session, name='cluster1')
    by_id = await get_peer_section(session, p.id)
    by_name = await get_peer_section_by_name(session, 'cluster1')

    assert by_id is not None and by_name is not None
    assert by_id.id == by_name.id


async def test_update(session: AsyncSession) -> None:
    """Update peer section name and fields."""

    p = await create_peer_section(session, name='old-cluster')
    updated = await update_peer_section(session, p, name='new-cluster', default_bind='*:10001', default_server_options='ssl verify none')

    assert updated.name == 'new-cluster'
    assert updated.default_bind == '*:10001'
    assert updated.default_server_options == 'ssl verify none'


async def test_delete(session: AsyncSession) -> None:
    """Delete a single peer section."""

    p = await create_peer_section(session, name='temp')
    await delete_peer_section(session, p)
    assert len(await list_peer_sections(session)) == 0


async def test_delete_all_with_entries(session: AsyncSession) -> None:
    """Delete all peer sections cascading to entries."""

    p = await create_peer_section(session, name='cluster')
    await create_peer_entry(session, peer_section_id=p.id, name='node1', address='10.0.0.1', port=10000)
    await delete_all_peer_sections(session)
    assert len(await list_peer_sections(session)) == 0


async def test_entry_create_and_list(session: AsyncSession) -> None:
    """Create peer entries and list them."""

    p = await create_peer_section(session, name='cluster')
    await create_peer_entry(session, peer_section_id=p.id, name='node1', address='10.0.0.1')
    await create_peer_entry(session, peer_section_id=p.id, name='node2', address='10.0.0.2', port=10001)

    entries = await list_peer_entries(session, p.id)
    assert len(entries) == 2


async def test_entry_update(session: AsyncSession) -> None:
    """Update peer entry address and port."""

    p = await create_peer_section(session, name='cluster')
    e = await create_peer_entry(session, peer_section_id=p.id, name='node1', address='10.0.0.1')
    updated = await update_peer_entry(session, e, address='10.0.0.99', port=20000)

    assert updated.address == '10.0.0.99'
    assert updated.port == 20000


async def test_entry_delete(session: AsyncSession) -> None:
    """Delete a single peer entry."""

    p = await create_peer_section(session, name='cluster')
    e = await create_peer_entry(session, peer_section_id=p.id, name='node1', address='10.0.0.1')

    await delete_peer_entry(session, e)
    assert len(await list_peer_entries(session, p.id)) == 0
