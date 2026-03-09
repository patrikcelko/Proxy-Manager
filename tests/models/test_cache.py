"""
Tests CacheSectionModel CRUD
============================
"""

from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.database.models.cache import (
    create_cache_section,
    delete_all_cache_sections,
    delete_cache_section,
    get_cache_section,
    get_cache_section_by_name,
    list_cache_sections,
    update_cache_section,
)


async def test_create_and_list(session: AsyncSession) -> None:
    """Create a cache section and list all."""

    await create_cache_section(session, name='static-cache', total_max_size=100)
    rows = await list_cache_sections(session)
    assert len(rows) == 1
    assert rows[0].total_max_size == 100


async def test_get_by_id_and_name(session: AsyncSession) -> None:
    """Get cache section by ID and by name."""

    c = await create_cache_section(session, name='cache1')
    by_id = await get_cache_section(session, c.id)
    by_name = await get_cache_section_by_name(session, 'cache1')

    assert by_id is not None and by_name is not None
    assert by_id.id == by_name.id


async def test_update(session: AsyncSession) -> None:
    """Update cache section fields."""

    c = await create_cache_section(session, name='cache')
    updated = await update_cache_section(session, c, total_max_size=200, max_object_size=65536, max_age=3600)

    assert updated.total_max_size == 200
    assert updated.max_object_size == 65536
    assert updated.max_age == 3600


async def test_delete(session: AsyncSession) -> None:
    """Delete a single cache section."""

    c = await create_cache_section(session, name='temp')
    await delete_cache_section(session, c)
    assert len(await list_cache_sections(session)) == 0


async def test_delete_all(session: AsyncSession) -> None:
    """Delete all cache sections at once."""

    await create_cache_section(session, name='cache1')
    await create_cache_section(session, name='cache2')
    await delete_all_cache_sections(session)
    assert len(await list_cache_sections(session)) == 0


async def test_all_optional_fields(session: AsyncSession) -> None:
    """Create a cache section with every optional field populated."""

    c = await create_cache_section(
        session,
        name='full-cache',
        total_max_size=256,
        max_object_size=131072,
        max_age=7200,
        max_secondary_entries=10,
        process_vary=1,
        comment='test cache',
        extra_options='some-custom-directive value',
    )

    fetched = await get_cache_section(session, c.id)
    assert fetched is not None
    assert fetched.max_secondary_entries == 10
    assert fetched.process_vary == 1
    assert fetched.comment == 'test cache'
