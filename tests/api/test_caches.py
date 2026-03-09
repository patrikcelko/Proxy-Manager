"""
Cache route tests
=================
"""

from httpx import AsyncClient


async def test_list_empty(client: AsyncClient) -> None:
    """List empty."""

    resp = await client.get('/api/caches')
    assert resp.status_code == 200

    data = resp.json()
    assert data['count'] == 0
    assert data['items'] == []


async def test_create(client: AsyncClient) -> None:
    """Create."""

    resp = await client.post(
        '/api/caches',
        json={
            'name': 'my_cache',
            'total_max_size': 4,
            'max_object_size': 524288,
            'max_age': 60,
        },
    )
    assert resp.status_code == 201

    data = resp.json()
    assert data['name'] == 'my_cache'
    assert data['total_max_size'] == 4
    assert data['max_object_size'] == 524288
    assert data['max_age'] == 60


async def test_create_duplicate(client: AsyncClient) -> None:
    """Create duplicate."""

    await client.post('/api/caches', json={'name': 'dup'})
    resp = await client.post('/api/caches', json={'name': 'dup'})
    assert resp.status_code == 409


async def test_get_detail(client: AsyncClient) -> None:
    """Get detail."""

    create = await client.post('/api/caches', json={'name': 'test-c'})
    cid = create.json()['id']
    resp = await client.get(f'/api/caches/{cid}')

    assert resp.status_code == 200
    assert resp.json()['name'] == 'test-c'


async def test_get_not_found(client: AsyncClient) -> None:
    """Get not found."""

    resp = await client.get('/api/caches/9999')
    assert resp.status_code == 404


async def test_update(client: AsyncClient) -> None:
    """Update."""

    create = await client.post('/api/caches', json={'name': 'old'})
    cid = create.json()['id']
    resp = await client.put(
        f'/api/caches/{cid}',
        json={
            'name': 'new',
            'total_max_size': 8,
            'max_age': 120,
        },
    )
    assert resp.status_code == 200

    data = resp.json()
    assert data['name'] == 'new'
    assert data['total_max_size'] == 8
    assert data['max_age'] == 120


async def test_delete(client: AsyncClient) -> None:
    """Delete."""

    create = await client.post('/api/caches', json={'name': 'to-delete'})
    cid = create.json()['id']
    resp = await client.delete(f'/api/caches/{cid}')

    assert resp.status_code == 200
    resp = await client.get(f'/api/caches/{cid}')

    assert resp.status_code == 404


async def test_create_with_all_fields(client: AsyncClient) -> None:
    """Create with all fields."""

    resp = await client.post(
        '/api/caches',
        json={
            'name': 'full',
            'total_max_size': 4,
            'max_object_size': 524288,
            'max_age': 60,
            'max_secondary_entries': 10,
            'process_vary': 1,
            'comment': 'Test cache',
            'extra_options': '# custom option',
        },
    )

    assert resp.status_code == 201

    data = resp.json()
    assert data['max_secondary_entries'] == 10
    assert data['process_vary'] == 1
    assert data['comment'] == 'Test cache'
    assert data['extra_options'] == '# custom option'


async def test_create_minimal(client: AsyncClient) -> None:
    """Create minimal."""

    resp = await client.post('/api/caches', json={'name': 'minimal'})
    assert resp.status_code == 201

    data = resp.json()
    assert data['name'] == 'minimal'
    assert data['total_max_size'] is None
    assert data['max_object_size'] is None
    assert data['max_age'] is None
