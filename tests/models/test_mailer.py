"""
Tests MailerSectionModel/MailerEntryModel CRUD
==============================================
"""

from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.database.models.mailer import (
    create_mailer_entry,
    create_mailer_section,
    delete_all_mailer_sections,
    delete_mailer_entry,
    delete_mailer_section,
    get_mailer_section,
    get_mailer_section_by_name,
    list_mailer_entries,
    list_mailer_sections,
    update_mailer_entry,
    update_mailer_section,
)


async def test_create_and_list(session: AsyncSession) -> None:
    """Create a mailer section and list all."""

    await create_mailer_section(session, name='alert-mailers', timeout_mail='10s')
    rows = await list_mailer_sections(session)

    assert len(rows) == 1
    assert rows[0].timeout_mail == '10s'


async def test_get_by_id_and_name(session: AsyncSession) -> None:
    """Get mailer section by ID and by name."""

    m = await create_mailer_section(session, name='mailers1')
    by_id = await get_mailer_section(session, m.id)
    by_name = await get_mailer_section_by_name(session, 'mailers1')

    assert by_id is not None and by_name is not None
    assert by_id.id == by_name.id


async def test_update(session: AsyncSession) -> None:
    """Update mailer section name and timeout."""

    m = await create_mailer_section(session, name='old-mailers')
    updated = await update_mailer_section(session, m, name='new-mailers', timeout_mail='30s')

    assert updated.name == 'new-mailers'
    assert updated.timeout_mail == '30s'


async def test_delete(session: AsyncSession) -> None:
    """Delete a single mailer section."""

    m = await create_mailer_section(session, name='temp')
    await delete_mailer_section(session, m)
    assert len(await list_mailer_sections(session)) == 0


async def test_delete_all_with_entries(session: AsyncSession) -> None:
    """Delete all mailer sections cascading to entries."""

    m = await create_mailer_section(session, name='mailers')
    await create_mailer_entry(session, mailer_section_id=m.id, name='smtp1', address='smtp.example.com', port=25)
    await delete_all_mailer_sections(session)
    assert len(await list_mailer_sections(session)) == 0


async def test_entry_create_and_list(session: AsyncSession) -> None:
    """Create mailer entries and list them."""

    m = await create_mailer_section(session, name='mailers')
    await create_mailer_entry(session, mailer_section_id=m.id, name='smtp1', address='smtp.example.com')
    await create_mailer_entry(session, mailer_section_id=m.id, name='smtp2', address='backup.example.com', port=587)

    entries = await list_mailer_entries(session, m.id)
    assert len(entries) == 2


async def test_entry_update(session: AsyncSession) -> None:
    """Update mailer entry address and port."""

    m = await create_mailer_section(session, name='mailers')
    e = await create_mailer_entry(session, mailer_section_id=m.id, name='smtp1', address='old.example.com')
    updated = await update_mailer_entry(session, e, address='new.example.com', port=2525)

    assert updated.address == 'new.example.com'
    assert updated.port == 2525


async def test_entry_delete(session: AsyncSession) -> None:
    """Delete a single mailer entry."""

    m = await create_mailer_section(session, name='mailers')
    e = await create_mailer_entry(session, mailer_section_id=m.id, name='smtp1', address='smtp.example.com')

    await delete_mailer_entry(session, e)
    assert len(await list_mailer_entries(session, m.id)) == 0


async def test_entry_with_smtp_auth(session: AsyncSession) -> None:
    """Create entry with full SMTP auth settings."""

    m = await create_mailer_section(session, name='auth-mailers')
    e = await create_mailer_entry(
        session,
        mailer_section_id=m.id,
        name='smtp-auth',
        address='smtp.gmail.com',
        port=587,
        smtp_auth=True,
        smtp_user='user@gmail.com',
        smtp_password='app-password',
        use_tls=False,
        use_starttls=True,
    )

    assert e.smtp_auth is True
    assert e.smtp_user == 'user@gmail.com'
    assert e.smtp_password == 'app-password'
    assert e.use_tls is False
    assert e.use_starttls is True


async def test_entry_smtp_auth_defaults(session: AsyncSession) -> None:
    """SMTP auth fields default to disabled."""

    m = await create_mailer_section(session, name='default-mailers')
    e = await create_mailer_entry(session, mailer_section_id=m.id, name='smtp1', address='smtp.local')

    assert e.smtp_auth is False
    assert e.smtp_user is None
    assert e.smtp_password is None
    assert e.use_tls is False
    assert e.use_starttls is False


async def test_entry_update_smtp_auth_fields(session: AsyncSession) -> None:
    """Update SMTP auth fields on an existing entry."""

    m = await create_mailer_section(session, name='upd-auth')
    e = await create_mailer_entry(session, mailer_section_id=m.id, name='smtp1', address='smtp.local')
    updated = await update_mailer_entry(
        session,
        e,
        smtp_auth=True,
        smtp_user='admin',
        smtp_password='secret',
        use_tls=True,
    )

    assert updated.smtp_auth is True
    assert updated.smtp_user == 'admin'
    assert updated.smtp_password == 'secret'
    assert updated.use_tls is True
