"""
Tests ResolverModel/ResolverNameserverModel CRUD
================================================
"""

from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.database.models.resolver import (
    create_resolver,
    create_resolver_nameserver,
    delete_all_resolvers,
    delete_resolver,
    delete_resolver_nameserver,
    get_resolver,
    get_resolver_by_name,
    list_resolver_nameservers,
    list_resolvers,
    update_resolver,
    update_resolver_nameserver,
)


async def test_create_and_list(session: AsyncSession) -> None:
    """Create a resolver and list all."""

    await create_resolver(session, name='dns-primary', resolve_retries=3)

    rows = await list_resolvers(session)
    assert len(rows) == 1
    assert rows[0].name == 'dns-primary'
    assert rows[0].resolve_retries == 3


async def test_get_by_id_and_name(session: AsyncSession) -> None:
    """Get resolver by ID and by name."""

    r = await create_resolver(session, name='my-dns')
    by_id = await get_resolver(session, r.id)
    by_name = await get_resolver_by_name(session, 'my-dns')

    assert by_id is not None
    assert by_name is not None
    assert by_id.id == by_name.id


async def test_get_nonexistent(session: AsyncSession) -> None:
    """Get nonexistent resolver returns None."""

    assert await get_resolver(session, 999) is None
    assert await get_resolver_by_name(session, 'nope') is None


async def test_update(session: AsyncSession) -> None:
    """Update resolver fields."""

    r = await create_resolver(session, name='dns-old', timeout_resolve='1s')
    updated = await update_resolver(session, r, timeout_resolve='5s', hold_valid='30s')
    assert updated.timeout_resolve == '5s'
    assert updated.hold_valid == '30s'


async def test_delete(session: AsyncSession) -> None:
    """Delete a single resolver."""

    r = await create_resolver(session, name='temp')
    await delete_resolver(session, r)
    assert len(await list_resolvers(session)) == 0


async def test_delete_all(session: AsyncSession) -> None:
    """Delete all resolvers including their nameservers."""

    await create_resolver(session, name='dns1')
    await create_resolver(session, name='dns2')

    ns = await create_resolver(session, name='dns3')
    await create_resolver_nameserver(session, resolver_id=ns.id, name='ns1', address='8.8.8.8', port=53)
    await delete_all_resolvers(session)
    assert len(await list_resolvers(session)) == 0


async def test_create_all_optional_fields(session: AsyncSession) -> None:
    """Create a resolver with every optional field populated."""

    r = await create_resolver(
        session,
        name='full-resolver',
        resolve_retries=5,
        timeout_resolve='2s',
        timeout_retry='1s',
        hold_valid='30s',
        hold_other='10s',
        hold_refused='5s',
        hold_timeout='5s',
        hold_obsolete='5s',
        hold_nx='10s',
        hold_aa='5s',
        accepted_payload_size=8192,
        parse_resolv_conf=1,
        comment='test resolver',
        extra_options='some-extra option',
    )
    fetched = await get_resolver(session, r.id)

    assert fetched is not None

    assert fetched.hold_nx == '10s'
    assert fetched.hold_aa == '5s'
    assert fetched.accepted_payload_size == 8192
    assert fetched.parse_resolv_conf == 1


async def test_nameserver_create_and_list(session: AsyncSession) -> None:
    """Create nameservers and list them for a resolver."""

    r = await create_resolver(session, name='dns')
    await create_resolver_nameserver(session, resolver_id=r.id, name='ns1', address='8.8.8.8', port=53)
    await create_resolver_nameserver(session, resolver_id=r.id, name='ns2', address='1.1.1.1', port=53)

    entries = await list_resolver_nameservers(session, r.id)
    assert len(entries) == 2


async def test_nameserver_update(session: AsyncSession) -> None:
    """Update nameserver address and port."""

    r = await create_resolver(session, name='dns')
    ns = await create_resolver_nameserver(session, resolver_id=r.id, name='ns1', address='8.8.8.8')
    updated = await update_resolver_nameserver(session, ns, address='9.9.9.9', port=5353)

    assert updated.address == '9.9.9.9'
    assert updated.port == 5353


async def test_nameserver_delete(session: AsyncSession) -> None:
    """Delete a single nameserver."""
    r = await create_resolver(session, name='dns')
    ns = await create_resolver_nameserver(session, resolver_id=r.id, name='ns1', address='8.8.8.8')

    await delete_resolver_nameserver(session, ns)
    assert len(await list_resolver_nameservers(session, r.id)) == 0
