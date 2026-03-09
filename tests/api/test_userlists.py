"""
Userlist route tests
====================
"""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.database.models.userlist import get_userlist_entry
from proxy_manager.utilities.auth import verify_password


async def test_list_empty(client: AsyncClient) -> None:
    """List empty."""

    resp = await client.get('/api/userlists')
    assert resp.status_code == 200

    data = resp.json()
    assert data['count'] == 0
    assert data['items'] == []


async def test_create(client: AsyncClient) -> None:
    """Create."""

    resp = await client.post('/api/userlists', json={'name': 'myusers'})
    assert resp.status_code == 201

    data = resp.json()
    assert data['name'] == 'myusers'
    assert data['entries'] == []


async def test_create_duplicate(client: AsyncClient) -> None:
    """Create duplicate."""

    await client.post('/api/userlists', json={'name': 'dup'})
    resp = await client.post('/api/userlists', json={'name': 'dup'})

    assert resp.status_code == 409


async def test_get_detail(client: AsyncClient) -> None:
    """Get detail."""

    create = await client.post('/api/userlists', json={'name': 'test-ul'})
    uid = create.json()['id']
    resp = await client.get(f'/api/userlists/{uid}')

    assert resp.status_code == 200
    assert resp.json()['name'] == 'test-ul'


async def test_update(client: AsyncClient) -> None:
    """Update."""

    create = await client.post('/api/userlists', json={'name': 'old-name'})
    uid = create.json()['id']
    resp = await client.put(f'/api/userlists/{uid}', json={'name': 'new-name'})

    assert resp.status_code == 200
    assert resp.json()['name'] == 'new-name'


async def test_delete(client: AsyncClient) -> None:
    """Delete."""

    create = await client.post('/api/userlists', json={'name': 'to-delete'})
    uid = create.json()['id']
    resp = await client.delete(f'/api/userlists/{uid}')

    assert resp.status_code == 200


async def test_list_includes_entries(client: AsyncClient) -> None:
    """List includes entries."""

    create = await client.post('/api/userlists', json={'name': 'with-entries'})
    uid = create.json()['id']
    await client.post(f'/api/userlists/{uid}/entries', json={'username': 'admin', 'password': 'secretpass'})

    resp = await client.get('/api/userlists')
    assert resp.status_code == 200

    items = resp.json()['items']
    assert len(items) == 1
    assert len(items[0]['entries']) == 1
    assert items[0]['entries'][0]['username'] == 'admin'


async def test_create_entry(client: AsyncClient) -> None:
    """Create entry."""

    ul = await client.post('/api/userlists', json={'name': 'ul1'})
    uid = ul.json()['id']
    resp = await client.post(f'/api/userlists/{uid}/entries', json={'username': 'user1', 'password': 'mypassword'})

    assert resp.status_code == 201
    assert resp.json()['username'] == 'user1'


async def test_update_entry(client: AsyncClient) -> None:
    """Update entry."""

    ul = await client.post('/api/userlists', json={'name': 'ul2'})
    uid = ul.json()['id']
    entry = await client.post(f'/api/userlists/{uid}/entries', json={'username': 'user2', 'password': 'pass2'})
    eid = entry.json()['id']
    resp = await client.put(f'/api/userlists/{uid}/entries/{eid}', json={'username': 'updated-user2'})

    assert resp.status_code == 200
    assert resp.json()['username'] == 'updated-user2'


async def test_delete_entry(client: AsyncClient) -> None:
    """Delete entry."""

    ul = await client.post('/api/userlists', json={'name': 'ul3'})
    uid = ul.json()['id']
    entry = await client.post(f'/api/userlists/{uid}/entries', json={'username': 'user3', 'password': 'pass3'})
    eid = entry.json()['id']
    resp = await client.delete(f'/api/userlists/{uid}/entries/{eid}')

    assert resp.status_code == 200


async def test_password_is_hashed_on_create(client: AsyncClient) -> None:
    """Creating an entry hashes the password - the raw password must never be in the response."""

    ul = await client.post('/api/userlists', json={'name': 'pw-test'})
    uid = ul.json()['id']
    resp = await client.post(f'/api/userlists/{uid}/entries', json={'username': 'alice', 'password': 'supersecret'})
    data = resp.json()

    assert resp.status_code == 201
    assert 'password_hash' not in data
    assert 'password' not in data
    assert data['has_password'] is True


async def test_response_never_contains_hash(client: AsyncClient) -> None:
    """Neither list nor detail endpoints expose password_hash."""

    ul = await client.post('/api/userlists', json={'name': 'nohash'})
    uid = ul.json()['id']
    await client.post(f'/api/userlists/{uid}/entries', json={'username': 'bob', 'password': 's3cret'})

    # Check list endpoint
    list_resp = await client.get('/api/userlists')
    entry_from_list = list_resp.json()['items'][0]['entries'][0]
    assert 'password_hash' not in entry_from_list
    assert 'password' not in entry_from_list
    assert entry_from_list['has_password'] is True

    # Check detail endpoint
    detail_resp = await client.get(f'/api/userlists/{uid}')
    entry_from_detail = detail_resp.json()['entries'][0]
    assert 'password_hash' not in entry_from_detail
    assert 'password' not in entry_from_detail


async def test_password_stored_as_bcrypt_hash(client: AsyncClient, session: AsyncSession) -> None:
    """Verify the password is stored as a bcrypt hash in the database."""

    ul = await client.post('/api/userlists', json={'name': 'hashcheck'})
    uid = ul.json()['id']
    entry_resp = await client.post(f'/api/userlists/{uid}/entries', json={'username': 'charlie', 'password': 'testpass123'})
    eid = entry_resp.json()['id']

    # Read directly from database
    entry = await get_userlist_entry(session, eid)
    assert entry is not None
    assert entry.password_hash.startswith('$2b$')
    assert verify_password('testpass123', entry.password_hash)
    assert not verify_password('wrongpassword', entry.password_hash)


async def test_change_password(client: AsyncClient, session: AsyncSession) -> None:
    """Updating an entry with a new password re-hashes it."""

    ul = await client.post('/api/userlists', json={'name': 'pwchange'})
    uid = ul.json()['id']
    entry_resp = await client.post(f'/api/userlists/{uid}/entries', json={'username': 'dave', 'password': 'oldpassword'})
    eid = entry_resp.json()['id']

    # Get old hash
    entry = await get_userlist_entry(session, eid)
    assert entry is not None

    old_hash = entry.password_hash

    # Change password
    resp = await client.put(f'/api/userlists/{uid}/entries/{eid}', json={'password': 'newpassword'})
    assert resp.status_code == 200

    # Verify new hash is different and correct
    await session.refresh(entry)
    assert entry.password_hash != old_hash
    assert verify_password('newpassword', entry.password_hash)
    assert not verify_password('oldpassword', entry.password_hash)


async def test_update_username_without_password(client: AsyncClient, session: AsyncSession) -> None:
    """Updating username without providing password preserves the existing hash."""

    ul = await client.post('/api/userlists', json={'name': 'nopwchange'})
    uid = ul.json()['id']
    entry_resp = await client.post(f'/api/userlists/{uid}/entries', json={'username': 'eve', 'password': 'keepthis'})
    eid = entry_resp.json()['id']

    entry = await get_userlist_entry(session, eid)
    assert entry is not None

    old_hash = entry.password_hash

    # Update only username
    resp = await client.put(f'/api/userlists/{uid}/entries/{eid}', json={'username': 'eve-updated'})
    assert resp.status_code == 200
    assert resp.json()['username'] == 'eve-updated'

    # Hash should remain unchanged
    await session.refresh(entry)
    assert entry.password_hash == old_hash
    assert verify_password('keepthis', entry.password_hash)


async def test_create_entry_requires_password(client: AsyncClient) -> None:
    """Creating an entry without a password should fail validation."""

    ul = await client.post('/api/userlists', json={'name': 'nopw'})
    uid = ul.json()['id']
    resp = await client.post(f'/api/userlists/{uid}/entries', json={'username': 'frank'})

    assert resp.status_code == 422


async def test_create_entry_empty_password_fails(client: AsyncClient) -> None:
    """Creating an entry with an empty password should fail validation."""

    ul = await client.post('/api/userlists', json={'name': 'emptypw'})
    uid = ul.json()['id']
    resp = await client.post(f'/api/userlists/{uid}/entries', json={'username': 'grace', 'password': ''})

    assert resp.status_code == 422


async def test_has_password_flag(client: AsyncClient) -> None:
    """The has_password field should be True when the user has a password."""

    ul = await client.post('/api/userlists', json={'name': 'hasflag'})
    uid = ul.json()['id']
    resp = await client.post(f'/api/userlists/{uid}/entries', json={'username': 'henry', 'password': 'pw123'})

    assert resp.json()['has_password'] is True
