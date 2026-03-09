"""
Version management route tests
================================
"""

from httpx import AsyncClient

SAMPLE_CONFIG = """\
global
    log 127.0.0.1 local0
    maxconn 4096

defaults
    mode http
    timeout connect 5000
    timeout client 50000
    timeout server 50000

frontend fe_http
    bind *:80
    mode http
    default_backend be_web

backend be_web
    mode http
    balance roundrobin
    server web1 10.0.0.1:8080 check
"""


async def test_status_not_initialized(client: AsyncClient) -> None:
    """Status returns initialized=False when no versions exist."""

    resp = await client.get('/api/versions/status')
    assert resp.status_code == 200

    data = resp.json()
    assert data['initialized'] is False
    assert data['has_pending'] is False
    assert data['current_hash'] is None


async def test_status_after_init(auth_client: AsyncClient) -> None:
    """Status returns initialized=True after init."""

    await auth_client.post('/api/versions/init/empty')

    resp = await auth_client.get('/api/versions/status')
    assert resp.status_code == 200
    data = resp.json()
    assert data['initialized'] is True
    assert data['has_pending'] is False
    assert data['current_hash'] is not None
    assert len(data['current_hash']) == 64


async def test_init_empty(auth_client: AsyncClient) -> None:
    """Init empty creates first version."""

    resp = await auth_client.post('/api/versions/init/empty')
    assert resp.status_code == 200
    assert 'initialized' in resp.json()['detail'].lower() or 'empty' in resp.json()['detail'].lower()


async def test_init_empty_duplicate(auth_client: AsyncClient) -> None:
    """Init empty fails when already initialized."""

    await auth_client.post('/api/versions/init/empty')
    resp = await auth_client.post('/api/versions/init/empty')
    assert resp.status_code == 409


async def test_init_empty_requires_auth(client: AsyncClient) -> None:
    """Init empty requires authentication."""

    resp = await client.post('/api/versions/init/empty')
    assert resp.status_code in (401, 403)


async def test_init_import(auth_client: AsyncClient) -> None:
    """Init import parses config and creates version."""

    resp = await auth_client.post('/api/versions/init/import', json={'config_text': SAMPLE_CONFIG})
    assert resp.status_code == 200

    # Verify entities were created
    status = await auth_client.get('/api/versions/status')
    assert status.json()['initialized'] is True

    # Verify frontends exist
    fe = await auth_client.get('/api/frontends')
    assert fe.json()['count'] >= 1


async def test_init_import_duplicate(auth_client: AsyncClient) -> None:
    """Init import fails when already initialized."""

    await auth_client.post('/api/versions/init/empty')
    resp = await auth_client.post('/api/versions/init/import', json={'config_text': SAMPLE_CONFIG})
    assert resp.status_code == 409


async def test_init_import_bad_config(auth_client: AsyncClient) -> None:
    """Init import with unparseable config fails gracefully."""

    resp = await auth_client.post('/api/versions/init/import', json={'config_text': ''})
    # Empty string triggers Pydantic min_length validation (422)
    assert resp.status_code == 422


async def test_init_import_requires_auth(client: AsyncClient) -> None:
    """Init import requires authentication."""

    resp = await client.post('/api/versions/init/import', json={'config_text': SAMPLE_CONFIG})
    assert resp.status_code in (401, 403)


async def test_pending_no_init(client: AsyncClient) -> None:
    """Pending changes returns empty when not initialized."""

    resp = await client.get('/api/versions/pending')
    assert resp.status_code == 200
    data = resp.json()
    assert data['has_pending'] is False


async def test_pending_no_changes(auth_client: AsyncClient) -> None:
    """Pending changes returns nothing right after init."""

    await auth_client.post('/api/versions/init/empty')

    resp = await auth_client.get('/api/versions/pending')
    assert resp.status_code == 200
    data = resp.json()
    assert data['has_pending'] is False
    assert all(v == 0 for v in data['pending_counts'].values())


async def test_pending_after_create(auth_client: AsyncClient) -> None:
    """Pending changes detected after creating an entity."""

    await auth_client.post('/api/versions/init/empty')
    await auth_client.post('/api/backends', json={'name': 'be_test', 'balance': 'roundrobin'})

    resp = await auth_client.get('/api/versions/pending')
    assert resp.status_code == 200
    data = resp.json()
    assert data['has_pending'] is True
    assert data['pending_counts']['backends'] >= 1

    # Sections detail should include backends
    assert 'backends' in data['sections']
    be_diff = data['sections']['backends']
    assert be_diff['total'] >= 1
    assert len(be_diff['created']) >= 1


async def test_pending_after_update(auth_client: AsyncClient) -> None:
    """Pending changes detected after updating an entity."""

    await auth_client.post('/api/versions/init/import', json={'config_text': SAMPLE_CONFIG})

    # Update the backend
    be_list = await auth_client.get('/api/backends')
    bid = be_list.json()['items'][0]['id']
    await auth_client.put(f'/api/backends/{bid}', json={'balance': 'leastconn'})

    resp = await auth_client.get('/api/versions/pending')
    data = resp.json()
    assert data['has_pending'] is True
    assert data['pending_counts']['backends'] >= 1
    assert 'backends' in data['sections']
    assert len(data['sections']['backends']['updated']) >= 1


async def test_pending_after_delete(auth_client: AsyncClient) -> None:
    """Pending changes detected after deleting an entity."""

    await auth_client.post('/api/versions/init/import', json={'config_text': SAMPLE_CONFIG})

    fe_list = await auth_client.get('/api/frontends')
    fid = fe_list.json()['items'][0]['id']
    await auth_client.delete(f'/api/frontends/{fid}')

    resp = await auth_client.get('/api/versions/pending')
    data = resp.json()
    assert data['has_pending'] is True
    assert data['pending_counts']['frontends'] >= 1
    assert 'frontends' in data['sections']
    assert len(data['sections']['frontends']['deleted']) >= 1


async def test_save_version(auth_client: AsyncClient) -> None:
    """Save creates a new committed version."""

    await auth_client.post('/api/versions/init/empty')
    await auth_client.post('/api/backends', json={'name': 'be_save'})

    resp = await auth_client.post('/api/versions/save', json={'message': 'added backend'})
    assert resp.status_code == 200

    data = resp.json()
    assert len(data['hash']) == 64
    assert data['message'] == 'added backend'
    assert data['user_name'] != ''

    # Pending should now be clear
    status = await auth_client.get('/api/versions/status')
    assert status.json()['has_pending'] is False


async def test_save_clears_pending(auth_client: AsyncClient) -> None:
    """After save, pending changes go to zero."""

    await auth_client.post('/api/versions/init/empty')
    await auth_client.post('/api/backends', json={'name': 'be_clr'})

    pending = await auth_client.get('/api/versions/pending')
    assert pending.json()['has_pending'] is True

    await auth_client.post('/api/versions/save', json={'message': 'save it'})

    pending = await auth_client.get('/api/versions/pending')
    assert pending.json()['has_pending'] is False


async def test_save_requires_message(auth_client: AsyncClient) -> None:
    """Save fails without a message."""

    await auth_client.post('/api/versions/init/empty')
    resp = await auth_client.post('/api/versions/save', json={'message': ''})
    assert resp.status_code == 422


async def test_save_not_initialized(auth_client: AsyncClient) -> None:
    """Save fails if not initialized."""

    resp = await auth_client.post('/api/versions/save', json={'message': 'nope'})
    assert resp.status_code == 409


async def test_save_requires_auth(client: AsyncClient) -> None:
    """Save requires authentication."""

    resp = await client.post('/api/versions/save', json={'message': 'test'})
    assert resp.status_code in (401, 403)


async def test_discard_changes(auth_client: AsyncClient) -> None:
    """Discard restores DB to last committed state."""

    await auth_client.post('/api/versions/init/empty')
    await auth_client.post('/api/backends', json={'name': 'be_gone'})

    # Verify entity exists
    be_list = await auth_client.get('/api/backends')
    assert be_list.json()['count'] == 1

    # Discard
    resp = await auth_client.post('/api/versions/discard')
    assert resp.status_code == 200

    # Entity should be gone (reverted to empty)
    be_list = await auth_client.get('/api/backends')
    assert be_list.json()['count'] == 0


async def test_discard_preserves_committed(auth_client: AsyncClient) -> None:
    """Discard keeps data that was in the committed version."""

    await auth_client.post('/api/versions/init/import', json={'config_text': SAMPLE_CONFIG})

    # Add another backend (pending change)
    await auth_client.post('/api/backends', json={'name': 'be_extra'})
    be_list = await auth_client.get('/api/backends')
    assert be_list.json()['count'] == 2

    # Discard
    await auth_client.post('/api/versions/discard')

    # Only original backend remains
    be_list = await auth_client.get('/api/backends')
    assert be_list.json()['count'] == 1
    assert be_list.json()['items'][0]['name'] == 'be_web'


async def test_discard_not_initialized(auth_client: AsyncClient) -> None:
    """Discard fails if not initialized."""

    resp = await auth_client.post('/api/versions/discard')
    assert resp.status_code == 409


async def test_discard_requires_auth(client: AsyncClient) -> None:
    """Discard requires authentication."""

    resp = await client.post('/api/versions/discard')
    assert resp.status_code in (401, 403)


async def test_list_versions_empty(client: AsyncClient) -> None:
    """List returns empty when no versions exist."""

    resp = await client.get('/api/versions')
    assert resp.status_code == 200
    data = resp.json()
    assert data['items'] == []
    assert data['total'] == 0


async def test_list_versions_after_saves(auth_client: AsyncClient) -> None:
    """List returns all committed versions."""

    await auth_client.post('/api/versions/init/empty')
    await auth_client.post('/api/backends', json={'name': 'be1'})
    await auth_client.post('/api/versions/save', json={'message': 'first change'})
    await auth_client.post('/api/backends', json={'name': 'be2'})
    await auth_client.post('/api/versions/save', json={'message': 'second change'})

    resp = await auth_client.get('/api/versions')
    data = resp.json()
    assert data['total'] == 3  # init + 2 saves
    assert data['items'][0]['message'] == 'second change'
    assert data['items'][1]['message'] == 'first change'


async def test_list_versions_pagination(auth_client: AsyncClient) -> None:
    """List supports limit and offset."""

    await auth_client.post('/api/versions/init/empty')
    await auth_client.post('/api/backends', json={'name': 'be_page'})
    await auth_client.post('/api/versions/save', json={'message': 'page test'})

    resp = await auth_client.get('/api/versions?limit=1&offset=0')
    data = resp.json()
    assert len(data['items']) == 1
    assert data['total'] == 2


async def test_version_detail(auth_client: AsyncClient) -> None:
    """Detail returns version with diff."""

    await auth_client.post('/api/versions/init/import', json={'config_text': SAMPLE_CONFIG})

    versions = await auth_client.get('/api/versions')
    vh = versions.json()['items'][0]['hash']

    resp = await auth_client.get(f'/api/versions/{vh}')
    assert resp.status_code == 200

    data = resp.json()
    assert data['hash'] == vh
    assert 'diff' in data


async def test_version_detail_first_version(auth_client: AsyncClient) -> None:
    """First version's diff is against empty snapshot."""

    await auth_client.post('/api/versions/init/import', json={'config_text': SAMPLE_CONFIG})
    versions = await auth_client.get('/api/versions')
    vh = versions.json()['items'][0]['hash']

    resp = await auth_client.get(f'/api/versions/{vh}')
    data = resp.json()
    assert data['parent_hash'] is None

    # Should show created entities
    diff = data['diff']
    assert any(len(diff.get(s, {}).get('created', [])) > 0 for s in diff)


async def test_version_detail_not_found(client: AsyncClient) -> None:
    """Detail returns 404 for unknown hash."""

    resp = await client.get(f'/api/versions/{"a" * 64}')
    assert resp.status_code == 404


async def test_version_detail_diff_between_versions(auth_client: AsyncClient) -> None:
    """Diff between two consecutive versions shows the changes."""

    await auth_client.post('/api/versions/init/empty')
    await auth_client.post('/api/backends', json={'name': 'be_diff'})
    await auth_client.post('/api/versions/save', json={'message': 'added be'})

    versions = await auth_client.get('/api/versions')
    newest = versions.json()['items'][0]

    resp = await auth_client.get(f'/api/versions/{newest["hash"]}')
    data = resp.json()
    assert 'backends' in data['diff']
    assert data['diff']['backends']['total'] >= 1


async def test_rollback(auth_client: AsyncClient) -> None:
    """Rollback restores a previous version's state."""

    await auth_client.post('/api/versions/init/empty')

    # Create a backend and save
    await auth_client.post('/api/backends', json={'name': 'be_keep'})
    save1 = await auth_client.post('/api/versions/save', json={'message': 'with backend'})
    target_hash = save1.json()['hash']

    # Create another and save
    await auth_client.post('/api/backends', json={'name': 'be_extra'})
    await auth_client.post('/api/versions/save', json={'message': 'two backends'})

    be_list = await auth_client.get('/api/backends')
    assert be_list.json()['count'] == 2

    # Rollback to version with only one backend
    resp = await auth_client.post(f'/api/versions/{target_hash}/rollback')
    assert resp.status_code == 200
    assert 'rollback' in resp.json()['message'].lower()

    be_list = await auth_client.get('/api/backends')
    assert be_list.json()['count'] == 1
    assert be_list.json()['items'][0]['name'] == 'be_keep'


async def test_rollback_creates_new_version(auth_client: AsyncClient) -> None:
    """Rollback adds a new version to history."""

    await auth_client.post('/api/versions/init/empty')
    save1 = await auth_client.post('/api/versions/save', json={'message': 'v1'})

    # Get initial total count - should be 2 (init + v1)
    versions_before = await auth_client.get('/api/versions')
    assert versions_before.json()['total'] == 2

    # Need a different snapshot to avoid hash collision - create, save, then rollback
    await auth_client.post('/api/backends', json={'name': 'be_temp'})
    await auth_client.post('/api/versions/save', json={'message': 'v2'})

    init_hash = save1.json()['hash']
    await auth_client.post(f'/api/versions/{init_hash}/rollback')

    versions_after = await auth_client.get('/api/versions')
    assert versions_after.json()['total'] == 4  # init + v1 + v2 + rollback


async def test_rollback_not_found(auth_client: AsyncClient) -> None:
    """Rollback returns 404 for unknown hash."""

    resp = await auth_client.post(f'/api/versions/{"b" * 64}/rollback')
    assert resp.status_code == 404


async def test_rollback_requires_auth(client: AsyncClient) -> None:
    """Rollback requires authentication."""

    resp = await client.post(f'/api/versions/{"c" * 64}/rollback')
    assert resp.status_code in (401, 403)


async def test_revert_section(auth_client: AsyncClient) -> None:
    """Revert section restores only that section."""

    await auth_client.post('/api/versions/init/import', json={'config_text': SAMPLE_CONFIG})

    # Add a backend (pending change)
    await auth_client.post('/api/backends', json={'name': 'be_revert'})
    be_list = await auth_client.get('/api/backends')
    assert be_list.json()['count'] == 2

    # Also add a frontend (pending change in different section)
    await auth_client.post('/api/frontends', json={'name': 'fe_new', 'mode': 'http'})

    # Revert only backends
    resp = await auth_client.post('/api/versions/revert-section', json={'section': 'backends'})
    assert resp.status_code == 200

    # Backends reverted to 1
    be_list = await auth_client.get('/api/backends')
    assert be_list.json()['count'] == 1

    # Frontends still has the new one
    fe_list = await auth_client.get('/api/frontends')
    assert fe_list.json()['count'] == 2


async def test_revert_section_unknown(auth_client: AsyncClient) -> None:
    """Revert unknown section returns 400."""

    await auth_client.post('/api/versions/init/empty')
    resp = await auth_client.post('/api/versions/revert-section', json={'section': 'nonexistent'})
    assert resp.status_code == 400


async def test_revert_section_not_initialized(auth_client: AsyncClient) -> None:
    """Revert section fails if not initialized."""

    resp = await auth_client.post('/api/versions/revert-section', json={'section': 'backends'})
    assert resp.status_code == 409


async def test_revert_section_requires_auth(client: AsyncClient) -> None:
    """Revert section requires authentication."""

    resp = await client.post('/api/versions/revert-section', json={'section': 'backends'})
    assert resp.status_code in (401, 403)


async def test_status_pending_counts(auth_client: AsyncClient) -> None:
    """Status includes per-section pending counts."""

    await auth_client.post('/api/versions/init/empty')
    await auth_client.post('/api/backends', json={'name': 'be_cnt'})
    await auth_client.post('/api/frontends', json={'name': 'fe_cnt', 'mode': 'http'})

    resp = await auth_client.get('/api/versions/status')
    data = resp.json()
    assert data['has_pending'] is True
    assert data['pending_counts']['backends'] >= 1
    assert data['pending_counts']['frontends'] >= 1

    # Sections without changes should be 0
    assert data['pending_counts']['caches'] == 0


async def test_full_workflow(auth_client: AsyncClient) -> None:
    """Full version control workflow: init, modify, save, modify, discard."""

    # 1. Init
    await auth_client.post('/api/versions/init/import', json={'config_text': SAMPLE_CONFIG})
    status = await auth_client.get('/api/versions/status')
    assert status.json()['initialized'] is True
    assert status.json()['has_pending'] is False

    # 2. Modify
    await auth_client.post('/api/backends', json={'name': 'be_new'})
    status = await auth_client.get('/api/versions/status')
    assert status.json()['has_pending'] is True

    # 3. Save
    await auth_client.post('/api/versions/save', json={'message': 'added be_new'})
    be_list = await auth_client.get('/api/backends')
    assert be_list.json()['count'] == 2

    # 4. Modify again
    await auth_client.post('/api/backends', json={'name': 'be_temp'})
    status = await auth_client.get('/api/versions/status')
    assert status.json()['has_pending'] is True

    # 5. Discard
    await auth_client.post('/api/versions/discard')
    be_list = await auth_client.get('/api/backends')
    assert be_list.json()['count'] == 2  # back to saved state

    status = await auth_client.get('/api/versions/status')
    assert status.json()['has_pending'] is False


async def test_ssl_fields_preserved_after_discard(auth_client: AsyncClient) -> None:
    """SSL certificate fields (email, dns_plugin, etc.) survive discard."""

    await auth_client.post('/api/versions/init/empty')

    # Create an SSL cert with all metadata fields
    cert_data = {
        'domain': 'example.com',
        'email': 'admin@example.com',
        'provider': 'certbot',
        'status': 'active',
        'challenge_type': 'dns-01',
        'dns_plugin': 'cloudflare',
        'auto_renew': True,
        'comment': 'main cert',
    }
    resp = await auth_client.post('/api/ssl-certificates', json=cert_data)
    assert resp.status_code == 201

    # Save version (snapshot captures current state)
    await auth_client.post('/api/versions/save', json={'message': 'with ssl cert'})

    # Make a pending change (add another entity)
    await auth_client.post('/api/backends', json={'name': 'be_temp'})

    # Discard pending changes -> restore_snapshot is called
    await auth_client.post('/api/versions/discard')

    # Verify SSL cert still has all its fields intact
    certs = await auth_client.get('/api/ssl-certificates')
    assert certs.json()['count'] == 1
    cert = certs.json()['items'][0]
    assert cert['domain'] == 'example.com'
    assert cert['email'] == 'admin@example.com'
    assert cert['dns_plugin'] == 'cloudflare'
    assert cert['challenge_type'] == 'dns-01'
    assert cert['provider'] == 'certbot'
    assert cert['status'] == 'active'
    assert cert['auto_renew'] is True
    assert cert['comment'] == 'main cert'
