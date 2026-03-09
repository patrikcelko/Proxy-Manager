"""
Backend route tests
===================
"""

from httpx import AsyncClient


async def test_list_empty(client: AsyncClient) -> None:
    """List empty."""

    resp = await client.get('/api/backends')
    assert resp.status_code == 200

    data = resp.json()
    assert data['count'] == 0
    assert data['items'] == []


async def test_create(client: AsyncClient) -> None:
    """Create."""

    resp = await client.post('/api/backends', json={'name': 'be_web', 'mode': 'http', 'balance': 'roundrobin'})
    assert resp.status_code == 201

    data = resp.json()
    assert data['name'] == 'be_web'
    assert data['balance'] == 'roundrobin'
    assert data['servers'] == []


async def test_create_duplicate(client: AsyncClient) -> None:
    """Create duplicate."""

    await client.post('/api/backends', json={'name': 'be_dup'})
    resp = await client.post('/api/backends', json={'name': 'be_dup'})
    assert resp.status_code == 409


async def test_get(client: AsyncClient) -> None:
    """Get."""

    create = await client.post('/api/backends', json={'name': 'be_get'})
    bid = create.json()['id']
    resp = await client.get(f'/api/backends/{bid}')

    assert resp.status_code == 200
    assert resp.json()['name'] == 'be_get'
    assert 'servers' in resp.json()


async def test_update(client: AsyncClient) -> None:
    """Update."""

    create = await client.post('/api/backends', json={'name': 'be_upd', 'balance': 'roundrobin'})
    bid = create.json()['id']
    resp = await client.put(f'/api/backends/{bid}', json={'balance': 'leastconn'})

    assert resp.status_code == 200
    assert resp.json()['balance'] == 'leastconn'


async def test_delete(client: AsyncClient) -> None:
    """Delete."""

    create = await client.post('/api/backends', json={'name': 'be_del'})
    bid = create.json()['id']
    resp = await client.delete(f'/api/backends/{bid}')
    assert resp.status_code == 200

    listing = await client.get('/api/backends')
    assert listing.json()['count'] == 0


async def test_list_includes_servers(client: AsyncClient) -> None:
    """List includes servers."""
    create = await client.post('/api/backends', json={'name': 'be_nested'})
    bid = create.json()['id']
    await client.post(f'/api/backends/{bid}/servers', json={'name': 'srv1', 'address': '10.0.0.1', 'port': 8080})

    resp = await client.get('/api/backends')
    items = resp.json()['items']
    assert len(items) == 1
    assert len(items[0]['servers']) == 1
    assert items[0]['servers'][0]['name'] == 'srv1'


async def test_create_server(client: AsyncClient) -> None:
    """Create server."""

    be = await client.post('/api/backends', json={'name': 'be_srv'})
    bid = be.json()['id']
    resp = await client.post(
        f'/api/backends/{bid}/servers',
        json={'name': 'web1', 'address': '192.168.1.10', 'port': 80, 'check_enabled': True},
    )

    assert resp.status_code == 201

    data = resp.json()
    assert data['name'] == 'web1'
    assert data['address'] == '192.168.1.10'
    assert data['port'] == 80
    assert data['check_enabled'] is True


async def test_update_server(client: AsyncClient) -> None:
    """Update server."""

    be = await client.post('/api/backends', json={'name': 'be_srv_upd'})
    bid = be.json()['id']

    srv = await client.post(f'/api/backends/{bid}/servers', json={'name': 'web1', 'address': '10.0.0.1', 'port': 80})
    sid = srv.json()['id']

    resp = await client.put(f'/api/backends/{bid}/servers/{sid}', json={'port': 8080})
    assert resp.status_code == 200
    assert resp.json()['port'] == 8080


async def test_delete_server(client: AsyncClient) -> None:
    """Delete server."""

    be = await client.post('/api/backends', json={'name': 'be_srv_del'})
    bid = be.json()['id']

    srv = await client.post(f'/api/backends/{bid}/servers', json={'name': 'web1', 'address': '10.0.0.1', 'port': 80})
    sid = srv.json()['id']

    resp = await client.delete(f'/api/backends/{bid}/servers/{sid}')
    assert resp.status_code == 200


async def test_server_not_found_wrong_backend(client: AsyncClient) -> None:
    """Server not found wrong backend."""

    be1 = await client.post('/api/backends', json={'name': 'be1'})
    be2 = await client.post('/api/backends', json={'name': 'be2'})
    bid1 = be1.json()['id']
    bid2 = be2.json()['id']

    srv = await client.post(f'/api/backends/{bid1}/servers', json={'name': 's', 'address': '1.2.3.4', 'port': 80})
    sid = srv.json()['id']

    resp = await client.put(f'/api/backends/{bid2}/servers/{sid}', json={'port': 9090})
    assert resp.status_code == 404


async def _create_backend_for_server(auth_client: AsyncClient) -> int:
    """Create a backend and return its ID."""

    r = await auth_client.post('/api/backends', json={'name': 'be-srv', 'balance': 'roundrobin'})
    assert r.status_code == 201
    return r.json()['id']


async def test_create_backend_with_all_new_fields(auth_client: AsyncClient) -> None:
    """Create backend with all new fields."""

    payload = {
        'name': 'be-full',
        'mode': 'http',
        'balance': 'leastconn',
        'cookie': 'SRVID insert indirect nocache',
        'timeout_server': '30s',
        'timeout_connect': '5s',
        'timeout_queue': '60s',
        'http_check_expect': 'status 200',
        'default_server_options': 'inter 3s fall 3 rise 2',
        'http_reuse': 'aggressive',
        'hash_type': 'consistent sdbm',
        'option_httplog': True,
        'option_tcplog': False,
        'compression_algo': 'gzip deflate',
        'compression_type': 'text/html text/css application/javascript',
    }

    r = await auth_client.post('/api/backends', json=payload)
    assert r.status_code == 201

    d = r.json()
    assert d['cookie'] == 'SRVID insert indirect nocache'
    assert d['timeout_server'] == '30s'
    assert d['timeout_connect'] == '5s'
    assert d['timeout_queue'] == '60s'
    assert d['http_check_expect'] == 'status 200'
    assert d['default_server_options'] == 'inter 3s fall 3 rise 2'
    assert d['http_reuse'] == 'aggressive'
    assert d['hash_type'] == 'consistent sdbm'
    assert d['option_httplog'] is True
    assert d['option_tcplog'] is False
    assert d['compression_algo'] == 'gzip deflate'
    assert d['compression_type'] == 'text/html text/css application/javascript'


async def test_update_backend_new_fields(auth_client: AsyncClient) -> None:
    """Update backend new fields."""

    r = await auth_client.post('/api/backends', json={'name': 'be-upd', 'balance': 'roundrobin'})
    assert r.status_code == 201

    bid = r.json()['id']
    r = await auth_client.put(
        f'/api/backends/{bid}',
        json={
            'name': 'be-upd',
            'balance': 'roundrobin',
            'cookie': 'SRV insert',
            'timeout_server': '10s',
            'http_reuse': 'safe',
            'option_httplog': True,
        },
    )
    assert r.status_code == 200

    d = r.json()
    assert d['cookie'] == 'SRV insert'
    assert d['timeout_server'] == '10s'
    assert d['http_reuse'] == 'safe'
    assert d['option_httplog'] is True


async def test_backend_new_fields_default_none(auth_client: AsyncClient) -> None:
    """Backend new fields default none."""

    r = await auth_client.post('/api/backends', json={'name': 'be-default', 'balance': 'roundrobin'})
    assert r.status_code == 201

    d = r.json()
    assert d['cookie'] is None
    assert d['timeout_server'] is None
    assert d['timeout_connect'] is None
    assert d['compression_algo'] is None
    assert d['option_httplog'] is False
    assert d['option_tcplog'] is False


async def test_backend_detail_includes_new_fields(auth_client: AsyncClient) -> None:
    """Backend detail includes new fields."""

    r = await auth_client.post('/api/backends', json={'name': 'be-detail', 'balance': 'roundrobin', 'cookie': 'SRV insert'})
    assert r.status_code == 201

    bid = r.json()['id']
    r = await auth_client.get(f'/api/backends/{bid}')
    assert r.status_code == 200

    d = r.json()
    assert d['cookie'] == 'SRV insert'
    assert 'servers' in d


async def test_create_server_with_all_new_fields(auth_client: AsyncClient) -> None:
    """Create server with all new fields."""

    bid = await _create_backend_for_server(auth_client)
    payload = {
        'name': 'srv1',
        'address': '10.0.0.1',
        'port': 8080,
        'check_enabled': True,
        'weight': 150,
        'ssl_enabled': True,
        'ssl_verify': 'none',
        'backup': True,
        'inter': '3s',
        'fastinter': '1s',
        'downinter': '5s',
        'rise': 2,
        'fall': 3,
        'cookie_value': 'srv1cookie',
        'send_proxy': False,
        'send_proxy_v2': True,
        'slowstart': '60s',
        'resolve_prefer': 'ipv4',
        'resolvers_ref': 'mydns',
        'on_marked_down': 'shutdown-sessions',
        'disabled': False,
    }

    r = await auth_client.post(f'/api/backends/{bid}/servers', json=payload)
    assert r.status_code == 201

    d = r.json()
    assert d['weight'] == 150
    assert d['ssl_enabled'] is True
    assert d['ssl_verify'] == 'none'
    assert d['backup'] is True
    assert d['inter'] == '3s'
    assert d['fastinter'] == '1s'
    assert d['downinter'] == '5s'
    assert d['rise'] == 2
    assert d['fall'] == 3
    assert d['cookie_value'] == 'srv1cookie'
    assert d['send_proxy'] is False
    assert d['send_proxy_v2'] is True
    assert d['slowstart'] == '60s'
    assert d['resolve_prefer'] == 'ipv4'
    assert d['resolvers_ref'] == 'mydns'
    assert d['on_marked_down'] == 'shutdown-sessions'
    assert d['disabled'] is False


async def test_update_server_new_fields(auth_client: AsyncClient) -> None:
    """Update server new fields."""

    bid = await _create_backend_for_server(auth_client)
    r = await auth_client.post(
        f'/api/backends/{bid}/servers',
        json={
            'name': 'srv2',
            'address': '10.0.0.2',
            'port': 80,
        },
    )

    assert r.status_code == 201
    sid = r.json()['id']

    r = await auth_client.put(
        f'/api/backends/{bid}/servers/{sid}',
        json={
            'name': 'srv2',
            'address': '10.0.0.2',
            'port': 80,
            'weight': 50,
            'ssl_enabled': True,
            'backup': True,
            'disabled': True,
        },
    )
    assert r.status_code == 200

    d = r.json()
    assert d['weight'] == 50
    assert d['ssl_enabled'] is True
    assert d['backup'] is True
    assert d['disabled'] is True


async def test_server_defaults_false_and_none(auth_client: AsyncClient) -> None:
    """Server defaults false and none."""

    bid = await _create_backend_for_server(auth_client)
    r = await auth_client.post(
        f'/api/backends/{bid}/servers',
        json={
            'name': 'srv3',
            'address': '10.0.0.3',
            'port': 80,
        },
    )
    assert r.status_code == 201

    d = r.json()
    assert d['weight'] is None
    assert d['ssl_enabled'] is False
    assert d['backup'] is False
    assert d['send_proxy'] is False
    assert d['send_proxy_v2'] is False
    assert d['disabled'] is False
    assert d['inter'] is None
    assert d['rise'] is None
    assert d['fall'] is None
