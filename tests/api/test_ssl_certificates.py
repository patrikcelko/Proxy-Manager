"""
SSL Certificates API tests
===========================
"""

from httpx import AsyncClient


async def test_list_empty(client: AsyncClient) -> None:
    """List empty."""

    resp = await client.get('/api/ssl-certificates')
    assert resp.status_code == 200

    data = resp.json()
    assert data['count'] == 0
    assert data['items'] == []


async def test_create(client: AsyncClient) -> None:
    """Create."""

    resp = await client.post(
        '/api/ssl-certificates',
        json={
            'domain': 'example.com',
            'email': 'admin@example.com',
        },
    )
    assert resp.status_code == 201

    data = resp.json()
    assert data['domain'] == 'example.com'
    assert data['email'] == 'admin@example.com'
    assert data['provider'] == 'certbot'
    assert data['status'] == 'pending'
    assert data['challenge_type'] == 'http-01'
    assert data['auto_renew'] is True
    assert data['id'] > 0


async def test_create_duplicate(client: AsyncClient) -> None:
    """Create duplicate."""

    await client.post('/api/ssl-certificates', json={'domain': 'dup.com'})
    resp = await client.post('/api/ssl-certificates', json={'domain': 'dup.com'})

    assert resp.status_code == 409
    assert 'already exists' in resp.json()['detail']


async def test_get_detail(client: AsyncClient) -> None:
    """Get detail."""

    create = await client.post(
        '/api/ssl-certificates',
        json={
            'domain': 'get.example.com',
            'email': 'a@b.com',
            'provider': 'manual',
            'status': 'active',
        },
    )
    cert_id = create.json()['id']
    resp = await client.get(f'/api/ssl-certificates/{cert_id}')
    assert resp.status_code == 200

    data = resp.json()
    assert data['domain'] == 'get.example.com'
    assert data['provider'] == 'manual'
    assert data['status'] == 'active'


async def test_get_not_found(client: AsyncClient) -> None:
    """Get not found."""

    resp = await client.get('/api/ssl-certificates/9999')
    assert resp.status_code == 404


async def test_update(client: AsyncClient) -> None:
    """Update."""

    create = await client.post('/api/ssl-certificates', json={'domain': 'up.com'})
    cert_id = create.json()['id']
    resp = await client.put(
        f'/api/ssl-certificates/{cert_id}',
        json={
            'status': 'active',
            'email': 'new@test.com',
            'comment': 'Updated cert',
        },
    )
    assert resp.status_code == 200

    data = resp.json()
    assert data['status'] == 'active'
    assert data['email'] == 'new@test.com'
    assert data['comment'] == 'Updated cert'


async def test_update_not_found(client: AsyncClient) -> None:
    """Update not found."""

    resp = await client.put('/api/ssl-certificates/9999', json={'status': 'active'})
    assert resp.status_code == 404


async def test_delete(client: AsyncClient) -> None:
    """Delete."""

    create = await client.post('/api/ssl-certificates', json={'domain': 'del.com'})
    cert_id = create.json()['id']
    resp = await client.delete(f'/api/ssl-certificates/{cert_id}')
    assert resp.status_code == 200

    # Verify gone
    get = await client.get(f'/api/ssl-certificates/{cert_id}')
    assert get.status_code == 404


async def test_delete_not_found(client: AsyncClient) -> None:
    """Delete not found."""

    resp = await client.delete('/api/ssl-certificates/9999')
    assert resp.status_code == 404


async def test_create_with_all_fields(client: AsyncClient) -> None:
    """Create with all fields."""

    resp = await client.post(
        '/api/ssl-certificates',
        json={
            'domain': 'full.example.com',
            'alt_domains': 'www.full.example.com, api.full.example.com',
            'email': 'ssl@example.com',
            'provider': 'certbot',
            'status': 'active',
            'cert_path': '/etc/letsencrypt/live/full.example.com/cert.pem',
            'key_path': '/etc/letsencrypt/live/full.example.com/privkey.pem',
            'fullchain_path': '/etc/letsencrypt/live/full.example.com/fullchain.pem',
            'issued_at': '2026-01-15T00:00:00',
            'expires_at': '2026-04-15T00:00:00',
            'auto_renew': True,
            'challenge_type': 'dns-01',
            'dns_plugin': 'cloudflare',
            'comment': 'Production wildcard cert',
        },
    )
    assert resp.status_code == 201

    data = resp.json()
    assert data['domain'] == 'full.example.com'
    assert 'www.full.example.com' in data['alt_domains']
    assert data['dns_plugin'] == 'cloudflare'
    assert data['challenge_type'] == 'dns-01'
    assert data['cert_path'] == '/etc/letsencrypt/live/full.example.com/cert.pem'
    assert data['auto_renew'] is True
    assert data['comment'] == 'Production wildcard cert'


async def test_create_self_signed(client: AsyncClient) -> None:
    """Create self signed."""

    resp = await client.post(
        '/api/ssl-certificates',
        json={
            'domain': 'self.local',
            'provider': 'self-signed',
            'status': 'active',
            'auto_renew': False,
        },
    )
    assert resp.status_code == 201

    data = resp.json()
    assert data['provider'] == 'self-signed'
    assert data['auto_renew'] is False


async def test_create_standalone_challenge(client: AsyncClient) -> None:
    """Create standalone challenge."""

    resp = await client.post(
        '/api/ssl-certificates',
        json={
            'domain': 'standalone.test',
            'challenge_type': 'standalone',
            'email': 'a@b.com',
        },
    )

    assert resp.status_code == 201
    assert resp.json()['challenge_type'] == 'standalone'


async def test_list_after_create(client: AsyncClient) -> None:
    """List after create."""

    await client.post('/api/ssl-certificates', json={'domain': 'a.com'})
    await client.post('/api/ssl-certificates', json={'domain': 'b.com'})
    resp = await client.get('/api/ssl-certificates')
    data = resp.json()
    assert data['count'] == 2

    domains = [c['domain'] for c in data['items']]
    assert 'a.com' in domains
    assert 'b.com' in domains


async def test_update_dates(client: AsyncClient) -> None:
    """Update dates."""

    create = await client.post('/api/ssl-certificates', json={'domain': 'dates.com'})
    cert_id = create.json()['id']
    resp = await client.put(
        f'/api/ssl-certificates/{cert_id}',
        json={
            'issued_at': '2026-03-01T00:00:00',
            'expires_at': '2026-06-01T00:00:00',
            'last_renewal_at': '2026-03-01T12:00:00',
        },
    )
    assert resp.status_code == 200

    data = resp.json()
    assert data['issued_at'] is not None
    assert data['expires_at'] is not None
    assert data['last_renewal_at'] is not None


async def test_update_error_status(client: AsyncClient) -> None:
    """Update error status."""

    create = await client.post('/api/ssl-certificates', json={'domain': 'err.com'})
    cert_id = create.json()['id']
    resp = await client.put(
        f'/api/ssl-certificates/{cert_id}',
        json={
            'status': 'error',
            'last_error': 'DNS validation failed: NXDOMAIN for _acme-challenge.err.com',
        },
    )
    assert resp.status_code == 200

    data = resp.json()
    assert data['status'] == 'error'
    assert 'DNS validation failed' in data['last_error']


async def test_certbot_command_http01(client: AsyncClient) -> None:
    """Certbot command http01."""

    create = await client.post(
        '/api/ssl-certificates',
        json={
            'domain': 'http.example.com',
            'email': 'admin@http.example.com',
            'challenge_type': 'http-01',
        },
    )
    cert_id = create.json()['id']
    resp = await client.get(f'/api/ssl-certificates/{cert_id}/certbot-command')
    assert resp.status_code == 200

    data = resp.json()
    cmd = data['command']
    assert 'certbot' in cmd
    assert 'certonly' in cmd
    assert '--webroot' in cmd
    assert 'http.example.com' in cmd
    assert '--email' in cmd
    assert '--agree-tos' in cmd
    assert '--non-interactive' in cmd


async def test_certbot_command_dns01(client: AsyncClient) -> None:
    """Certbot command dns01."""

    create = await client.post(
        '/api/ssl-certificates',
        json={
            'domain': 'dns.example.com',
            'email': 'admin@dns.example.com',
            'challenge_type': 'dns-01',
            'dns_plugin': 'cloudflare',
        },
    )
    cert_id = create.json()['id']
    resp = await client.get(f'/api/ssl-certificates/{cert_id}/certbot-command')
    assert resp.status_code == 200

    cmd = resp.json()['command']
    assert '--dns-cloudflare' in cmd
    assert 'dns.example.com' in cmd


async def test_certbot_command_dns01_manual(client: AsyncClient) -> None:
    """DNS-01 without a plugin should use --manual with --preferred-challenges=dns."""

    create = await client.post(
        '/api/ssl-certificates',
        json={
            'domain': 'manualdns.example.com',
            'email': 'admin@example.com',
            'challenge_type': 'dns-01',
        },
    )
    cert_id = create.json()['id']
    resp = await client.get(f'/api/ssl-certificates/{cert_id}/certbot-command')
    assert resp.status_code == 200

    cmd = resp.json()['command']
    assert '--manual' in cmd
    assert '--preferred-challenges=dns' in cmd


async def test_certbot_command_standalone(client: AsyncClient) -> None:
    """Certbot command standalone."""

    create = await client.post(
        '/api/ssl-certificates',
        json={
            'domain': 'standalone.example.com',
            'email': 'admin@standalone.example.com',
            'challenge_type': 'standalone',
        },
    )
    cert_id = create.json()['id']
    resp = await client.get(f'/api/ssl-certificates/{cert_id}/certbot-command')
    assert resp.status_code == 200

    cmd = resp.json()['command']
    assert '--standalone' in cmd
    assert 'standalone.example.com' in cmd


async def test_certbot_command_no_email(client: AsyncClient) -> None:
    """Certbot command no email."""

    create = await client.post(
        '/api/ssl-certificates',
        json={
            'domain': 'noemail.example.com',
        },
    )
    cert_id = create.json()['id']
    resp = await client.get(f'/api/ssl-certificates/{cert_id}/certbot-command')
    assert resp.status_code == 200

    cmd = resp.json()['command']
    assert '--register-unsafely-without-email' in cmd


async def test_certbot_command_with_alt_domains(client: AsyncClient) -> None:
    """Certbot command with alt domains."""

    create = await client.post(
        '/api/ssl-certificates',
        json={
            'domain': 'main.example.com',
            'alt_domains': 'www.main.example.com, api.main.example.com',
            'email': 'admin@example.com',
        },
    )
    cert_id = create.json()['id']
    resp = await client.get(f'/api/ssl-certificates/{cert_id}/certbot-command')
    assert resp.status_code == 200

    cmd = resp.json()['command']
    assert 'main.example.com' in cmd
    assert 'www.main.example.com' in cmd
    assert 'api.main.example.com' in cmd


async def test_certbot_command_with_custom_paths(client: AsyncClient) -> None:
    """Certbot command with custom paths."""

    create = await client.post(
        '/api/ssl-certificates',
        json={
            'domain': 'paths.example.com',
            'email': 'admin@example.com',
            'cert_path': '/custom/cert.pem',
            'key_path': '/custom/key.pem',
            'fullchain_path': '/custom/fullchain.pem',
        },
    )
    cert_id = create.json()['id']
    resp = await client.get(f'/api/ssl-certificates/{cert_id}/certbot-command')
    assert resp.status_code == 200

    cmd = resp.json()['command']
    assert '--cert-path' in cmd
    assert '/custom/cert.pem' in cmd
    assert '--key-path' in cmd
    assert '--fullchain-path' in cmd


async def test_certbot_command_not_found(client: AsyncClient) -> None:
    """Certbot command not found."""

    resp = await client.get('/api/ssl-certificates/9999/certbot-command')
    assert resp.status_code == 404


async def test_renew_command(client: AsyncClient) -> None:
    """Renew command."""

    create = await client.post(
        '/api/ssl-certificates',
        json={
            'domain': 'renew.example.com',
            'email': 'admin@example.com',
        },
    )
    cert_id = create.json()['id']
    resp = await client.get(f'/api/ssl-certificates/{cert_id}/renew-command')
    assert resp.status_code == 200

    data = resp.json()
    cmd = data['command']
    assert 'certbot' in cmd
    assert 'renew' in cmd
    assert '--cert-name' in cmd
    assert 'renew.example.com' in cmd
    assert '--non-interactive' in cmd


async def test_renew_command_not_found(client: AsyncClient) -> None:
    """Renew command not found."""

    resp = await client.get('/api/ssl-certificates/9999/renew-command')
    assert resp.status_code == 404


async def test_revoke_command(client: AsyncClient) -> None:
    """Revoke command."""

    create = await client.post(
        '/api/ssl-certificates',
        json={
            'domain': 'revoke.example.com',
            'email': 'admin@example.com',
            'fullchain_path': '/etc/letsencrypt/live/revoke.example.com/fullchain.pem',
        },
    )
    cert_id = create.json()['id']
    resp = await client.get(f'/api/ssl-certificates/{cert_id}/revoke-command')
    assert resp.status_code == 200

    data = resp.json()
    cmd = data['command']
    assert 'certbot' in cmd
    assert 'revoke' in cmd
    assert '--cert-path' in cmd
    assert '/etc/letsencrypt/live/revoke.example.com/fullchain.pem' in cmd
    assert '--non-interactive' in cmd


async def test_revoke_command_default_path(client: AsyncClient) -> None:
    """When no fullchain_path is set, revoke uses default Let's Encrypt path."""

    create = await client.post(
        '/api/ssl-certificates',
        json={
            'domain': 'revdef.example.com',
            'email': 'admin@example.com',
        },
    )
    cert_id = create.json()['id']
    resp = await client.get(f'/api/ssl-certificates/{cert_id}/revoke-command')
    assert resp.status_code == 200

    cmd = resp.json()['command']
    assert '/etc/letsencrypt/live/revdef.example.com/fullchain.pem' in cmd


async def test_revoke_command_not_found(client: AsyncClient) -> None:
    """Revoke command not found."""

    resp = await client.get('/api/ssl-certificates/9999/revoke-command')
    assert resp.status_code == 404


async def test_overview_has_ssl_count(client: AsyncClient) -> None:
    """Overview has ssl count."""

    resp = await client.get('/api/overview')
    assert resp.status_code == 200

    data = resp.json()
    assert 'ssl_certificates' in data
    assert data['ssl_certificates'] == 0


async def test_overview_counts_ssl(client: AsyncClient) -> None:
    """Overview counts ssl."""

    await client.post('/api/ssl-certificates', json={'domain': 'count1.com'})
    await client.post('/api/ssl-certificates', json={'domain': 'count2.com'})

    resp = await client.get('/api/overview')
    data = resp.json()
    assert data['ssl_certificates'] == 2
