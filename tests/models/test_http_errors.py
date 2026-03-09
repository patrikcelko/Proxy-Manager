"""
Tests HttpErrorsSectionModel/HttpErrorEntryModel CRUD
=====================================================
"""

from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.database.models.http_errors import (
    create_http_error_entry,
    create_http_errors_section,
    delete_all_http_errors_sections,
    delete_http_error_entry,
    delete_http_errors_section,
    get_http_errors_section,
    get_http_errors_section_by_name,
    list_http_error_entries,
    list_http_errors_sections,
    update_http_error_entry,
    update_http_errors_section,
)


async def test_create_and_list(session: AsyncSession) -> None:
    """Create an HTTP errors section and list all."""

    await create_http_errors_section(session, name='custom-errors')
    rows = await list_http_errors_sections(session)

    assert len(rows) == 1
    assert rows[0].name == 'custom-errors'


async def test_get_by_id_and_name(session: AsyncSession) -> None:
    """Get section by ID and by name."""

    s = await create_http_errors_section(session, name='errors1')
    by_id = await get_http_errors_section(session, s.id)
    by_name = await get_http_errors_section_by_name(session, 'errors1')

    assert by_id is not None and by_name is not None
    assert by_id.id == by_name.id


async def test_update(session: AsyncSession) -> None:
    """Update section name and extra options."""

    s = await create_http_errors_section(session, name='old-errors')
    updated = await update_http_errors_section(session, s, name='new-errors', extra_options='log global')

    assert updated.name == 'new-errors'
    assert updated.extra_options == 'log global'


async def test_delete(session: AsyncSession) -> None:
    """Delete a single HTTP errors section."""

    s = await create_http_errors_section(session, name='temp')
    await delete_http_errors_section(session, s)
    assert len(await list_http_errors_sections(session)) == 0


async def test_delete_all_with_entries(session: AsyncSession) -> None:
    """Delete all sections cascading to entries."""

    s = await create_http_errors_section(session, name='errors')
    await create_http_error_entry(session, section_id=s.id, status_code=503, type='errorfile', value='/etc/haproxy/errors/503.http')
    await delete_all_http_errors_sections(session)
    assert len(await list_http_errors_sections(session)) == 0


async def test_entry_create_and_list(session: AsyncSession) -> None:
    """Create error entries and list them."""

    s = await create_http_errors_section(session, name='errors')
    await create_http_error_entry(session, section_id=s.id, status_code=400, type='errorfile', value='/errors/400.http')
    await create_http_error_entry(session, section_id=s.id, status_code=503, type='errorloc302', value='https://sorry.example.com')

    entries = await list_http_error_entries(session, s.id)
    assert len(entries) == 2


async def test_entry_update(session: AsyncSession) -> None:
    """Update error entry type and value."""

    s = await create_http_errors_section(session, name='errors')
    e = await create_http_error_entry(session, section_id=s.id, status_code=500, type='errorfile', value='/errors/500.http')

    updated = await update_http_error_entry(session, e, type='errorloc303', value='https://maint.example.com')
    assert updated.type == 'errorloc303'
    assert updated.value == 'https://maint.example.com'


async def test_entry_delete(session: AsyncSession) -> None:
    """Delete a single error entry."""
    s = await create_http_errors_section(session, name='errors')
    e = await create_http_error_entry(session, section_id=s.id, status_code=404, type='errorfile', value='/errors/404.http')

    await delete_http_error_entry(session, e)
    assert len(await list_http_error_entries(session, s.id)) == 0
