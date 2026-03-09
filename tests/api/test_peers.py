"""
Peers route tests
=================
"""

from httpx import AsyncClient


async def test_list_empty(client: AsyncClient) -> None:
    """List empty."""

    resp = await client.get('/api/peers')
    assert resp.status_code == 200

    data = resp.json()
    assert data['count'] == 0
    assert data['items'] == []


async def test_create(client: AsyncClient) -> None:
    """Create."""

    resp = await client.post(
        '/api/peers',
        json={
            'name': 'mypeers',
            'comment': 'HA cluster peers',
        },
    )
    assert resp.status_code == 201

    data = resp.json()
    assert data['name'] == 'mypeers'
    assert data['comment'] == 'HA cluster peers'
    assert data['entries'] == []


async def test_create_duplicate(client: AsyncClient) -> None:
    """Create duplicate."""

    await client.post('/api/peers', json={'name': 'dup'})
    resp = await client.post('/api/peers', json={'name': 'dup'})
    assert resp.status_code == 409


async def test_get_detail(client: AsyncClient) -> None:
    """Get detail."""

    create = await client.post('/api/peers', json={'name': 'test-peer'})
    pid = create.json()['id']
    resp = await client.get(f'/api/peers/{pid}')

    assert resp.status_code == 200
    assert resp.json()['name'] == 'test-peer'


async def test_get_not_found(client: AsyncClient) -> None:
    """Get not found."""

    resp = await client.get('/api/peers/9999')
    assert resp.status_code == 404


async def test_update(client: AsyncClient) -> None:
    """Update."""

    create = await client.post('/api/peers', json={'name': 'old'})
    pid = create.json()['id']
    resp = await client.put(
        f'/api/peers/{pid}',
        json={
            'name': 'new',
            'comment': 'Updated',
        },
    )

    assert resp.status_code == 200
    assert resp.json()['name'] == 'new'
    assert resp.json()['comment'] == 'Updated'


async def test_create_with_default_bind(client: AsyncClient) -> None:
    """Test creating peer section with default_bind."""

    resp = await client.post(
        '/api/peers',
        json={
            'name': 'bind-peers',
            'default_bind': ':10000 ssl crt /etc/ssl/cert.pem',
        },
    )

    assert resp.status_code == 201
    assert resp.json()['default_bind'] == ':10000 ssl crt /etc/ssl/cert.pem'


async def test_create_with_default_server_options(client: AsyncClient) -> None:
    """Test creating peer section with default_server_options."""

    resp = await client.post(
        '/api/peers',
        json={
            'name': 'server-peers',
            'default_server_options': 'ssl verify none',
        },
    )

    assert resp.status_code == 201
    assert resp.json()['default_server_options'] == 'ssl verify none'


async def test_update_default_bind_and_server(client: AsyncClient) -> None:
    """Test updating default_bind and default_server_options."""

    create = await client.post('/api/peers', json={'name': 'upd-bind'})
    pid = create.json()['id']
    resp = await client.put(
        f'/api/peers/{pid}',
        json={
            'name': 'upd-bind',
            'default_bind': ':10001',
            'default_server_options': 'ssl',
        },
    )

    assert resp.status_code == 200
    assert resp.json()['default_bind'] == ':10001'
    assert resp.json()['default_server_options'] == 'ssl'


async def test_default_null_new_fields(client: AsyncClient) -> None:
    """New fields default to null when not provided."""

    resp = await client.post('/api/peers', json={'name': 'defaults-test'})
    assert resp.status_code == 201

    data = resp.json()
    assert data['default_bind'] is None
    assert data['default_server_options'] is None


async def test_delete(client: AsyncClient) -> None:
    """Delete."""

    create = await client.post('/api/peers', json={'name': 'to-delete'})
    pid = create.json()['id']
    resp = await client.delete(f'/api/peers/{pid}')
    assert resp.status_code == 200


async def test_list_with_entries(client: AsyncClient) -> None:
    """List with entries."""

    create = await client.post('/api/peers', json={'name': 'with-entries'})
    pid = create.json()['id']
    await client.post(
        f'/api/peers/{pid}/entries',
        json={
            'name': 'haproxy1',
            'address': '10.0.0.1',
            'port': 10000,
        },
    )

    resp = await client.get('/api/peers')
    items = resp.json()['items']
    assert len(items) == 1
    assert len(items[0]['entries']) == 1
    assert items[0]['entries'][0]['name'] == 'haproxy1'


async def test_create_entry(client: AsyncClient) -> None:
    """Create entry."""

    p = await client.post('/api/peers', json={'name': 'p1'})
    pid = p.json()['id']
    resp = await client.post(
        f'/api/peers/{pid}/entries',
        json={
            'name': 'haproxy1',
            'address': '10.0.0.1',
            'port': 10000,
        },
    )
    assert resp.status_code == 201

    data = resp.json()
    assert data['name'] == 'haproxy1'
    assert data['address'] == '10.0.0.1'
    assert data['port'] == 10000


async def test_update_entry(client: AsyncClient) -> None:
    """Update entry."""

    p = await client.post('/api/peers', json={'name': 'p2'})
    pid = p.json()['id']
    entry = await client.post(
        f'/api/peers/{pid}/entries',
        json={
            'name': 'haproxy1',
            'address': '10.0.0.1',
            'port': 10000,
        },
    )
    eid = entry.json()['id']
    resp = await client.put(
        f'/api/peers/{pid}/entries/{eid}',
        json={
            'address': '10.0.0.2',
            'port': 10001,
        },
    )

    assert resp.status_code == 200
    assert resp.json()['address'] == '10.0.0.2'
    assert resp.json()['port'] == 10001


async def test_delete_entry(client: AsyncClient) -> None:
    """Delete entry."""

    p = await client.post('/api/peers', json={'name': 'p3'})
    pid = p.json()['id']
    entry = await client.post(
        f'/api/peers/{pid}/entries',
        json={
            'name': 'haproxy1',
            'address': '10.0.0.1',
            'port': 10000,
        },
    )
    eid = entry.json()['id']
    resp = await client.delete(f'/api/peers/{pid}/entries/{eid}')

    assert resp.status_code == 200


async def test_cascade_delete(client: AsyncClient) -> None:
    """Cascade delete."""

    p = await client.post('/api/peers', json={'name': 'cascade'})
    pid = p.json()['id']
    await client.post(
        f'/api/peers/{pid}/entries',
        json={
            'name': 'haproxy1',
            'address': '10.0.0.1',
            'port': 10000,
        },
    )
    resp = await client.delete(f'/api/peers/{pid}')
    assert resp.status_code == 200

    resp = await client.get(f'/api/peers/{pid}')
    assert resp.status_code == 404
