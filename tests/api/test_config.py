"""
Config import/export & overview tests
======================================
"""

from httpx import AsyncClient

SAMPLE_CONFIG = """
global
    log 127.0.0.1 local0
    maxconn 4096
    daemon

defaults
    mode http
    timeout connect 5000
    timeout client 50000
    timeout server 50000

userlist myusers
    user admin password $6$rounds=5000$salt$hash

listen stats
    bind *:8404
    mode http
    stats enable
    stats uri /stats

frontend fe_http
    bind *:80
    mode http
    default_backend be_web

backend be_web
    mode http
    balance roundrobin
    server web1 10.0.0.1:8080 check
    server web2 10.0.0.2:8080 check
"""


async def test_overview_empty(client: AsyncClient) -> None:
    """Overview empty."""

    resp = await client.get("/api/overview")
    assert resp.status_code == 200

    data = resp.json()
    assert data["global_settings"] == 0
    assert data["default_settings"] == 0
    assert data["userlists"] == 0
    assert data["frontends"] == 0
    assert data["acl_rules"] == 0
    assert data["backends"] == 0
    assert data["backend_servers"] == 0
    assert data["listen_blocks"] == 0


async def test_overview_after_import(client: AsyncClient) -> None:
    """Overview after import."""

    await client.post("/api/config/import", json={"config_text": SAMPLE_CONFIG, "merge": False})
    resp = await client.get("/api/overview")

    data = resp.json()
    assert data["global_settings"] >= 2  # log, maxconn, daemon
    assert data["default_settings"] >= 3
    assert data["userlists"] == 1
    assert data["frontends"] == 1
    assert data["backends"] == 1
    assert data["backend_servers"] == 2
    assert data["listen_blocks"] == 1


async def test_import_replace(client: AsyncClient) -> None:
    """Import replace."""

    resp = await client.post("/api/config/import", json={"config_text": SAMPLE_CONFIG, "merge": False})
    assert resp.status_code == 200
    assert "imported" in resp.json()["detail"].lower() or "Config" in resp.json()["detail"]


async def test_import_merge(client: AsyncClient) -> None:
    """Import merge."""

    # First import
    await client.post("/api/config/import", json={"config_text": SAMPLE_CONFIG, "merge": False})

    # Get counts
    ov1 = await client.get("/api/overview")

    # Merge import
    resp = await client.post("/api/config/import", json={"config_text": "global\n    log 127.0.0.1 local1\n", "merge": True})
    assert resp.status_code == 200

    # Global settings should have grown
    ov2 = await client.get("/api/overview")
    assert ov2.json()["global_settings"] > ov1.json()["global_settings"]


async def test_import_invalid_config(client: AsyncClient) -> None:
    """Import invalid config."""

    # An empty string should fail validation
    resp = await client.post("/api/config/import", json={"config_text": "", "merge": False})
    assert resp.status_code == 422


async def test_import_and_verify_data(client: AsyncClient) -> None:
    """Import and verify data."""

    await client.post("/api/config/import", json={"config_text": SAMPLE_CONFIG, "merge": False})

    # Check backends created with servers
    be_resp = await client.get("/api/backends")
    backends = be_resp.json()["items"]
    assert len(backends) >= 1

    be_web = [b for b in backends if b["name"] == "be_web"]
    assert len(be_web) == 1
    assert len(be_web[0]["servers"]) == 2

    # Check frontends created
    fe_resp = await client.get("/api/frontends")
    frontends = fe_resp.json()["items"]
    assert len(frontends) >= 1

    # Check userlists created with entries
    ul_resp = await client.get("/api/userlists")
    userlists = ul_resp.json()["items"]
    assert len(userlists) >= 1


async def test_export_empty(client: AsyncClient) -> None:
    """Export empty."""

    resp = await client.get("/api/config/export")
    assert resp.status_code == 200
    assert "config_text" in resp.json()


async def test_roundtrip(client: AsyncClient) -> None:
    """Import config, export it, verify key content is preserved."""

    await client.post("/api/config/import", json={"config_text": SAMPLE_CONFIG, "merge": False})
    resp = await client.get("/api/config/export")

    assert resp.status_code == 200
    exported = resp.json()["config_text"]

    # Key directives should survive the roundtrip
    assert "global" in exported.lower()
    assert "maxconn" in exported
    assert "be_web" in exported
    assert "fe_http" in exported
    assert "stats" in exported
