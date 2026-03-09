"""
Config import/export & overview tests
======================================
"""

from textwrap import dedent

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


async def test_import_export_backend_fields(client: AsyncClient) -> None:
    """Import export backend fields."""

    cfg = dedent("""\
    backend test_be
        mode http
        balance roundrobin
        cookie SRVID insert indirect nocache
        timeout server 30s
        timeout connect 5s
        http-reuse aggressive
        option httplog
        server s1 10.0.0.1:80 weight 100 ssl verify none check inter 3s rise 2 fall 3 backup
    """)

    r = await client.post("/api/config/import", json={"config_text": cfg, "merge": False})
    assert r.status_code == 200

    r = await client.get("/api/config/export")
    assert r.status_code == 200
    exported = r.json()["config_text"]

    assert "cookie SRVID insert indirect nocache" in exported
    assert "timeout server 30s" in exported
    assert "timeout connect 5s" in exported
    assert "http-reuse aggressive" in exported
    assert "option httplog" in exported
    assert "weight 100" in exported
    assert "ssl" in exported
    assert "verify none" in exported
    assert "check" in exported
    assert "inter 3s" in exported
    assert "rise 2" in exported
    assert "fall 3" in exported
    assert "backup" in exported


async def test_import_export_frontend_fields(client: AsyncClient) -> None:
    """Import export frontend fields."""

    cfg = dedent("""\
    frontend test_fe
        bind *:80
        mode http
        maxconn 5000
        timeout client 30s
        timeout http-request 10s
        option httplog
        option forwardfor
        compression algo gzip
        compression type text/html text/css
    """)

    r = await client.post("/api/config/import", json={"config_text": cfg, "merge": False})
    assert r.status_code == 200

    r = await client.get("/api/config/export")
    assert r.status_code == 200
    exported = r.json()["config_text"]

    assert "maxconn 5000" in exported
    assert "timeout client 30s" in exported
    assert "timeout http-request 10s" in exported
    assert "option httplog" in exported
    assert "option forwardfor" in exported
    assert "compression algo gzip" in exported
    assert "compression type text/html text/css" in exported


async def test_import_export_resolver_new_fields(client: AsyncClient) -> None:
    """Test import/export round-trip for resolver hold_nx, hold_aa, parse-resolv-conf."""

    cfg = dedent("""\
    resolvers mydns
        parse-resolv-conf
        nameserver dns1 8.8.8.8:53
        nameserver dns2 1.1.1.1:53
        resolve_retries 3
        timeout resolve 1s
        timeout retry 1s
        hold valid 10s
        hold nx 60s
        hold aa 5s
        accepted_payload_size 8192
    """)

    r = await client.post("/api/config/import", json={"config_text": cfg, "merge": False})
    assert r.status_code == 200

    r = await client.get("/api/config/export")
    assert r.status_code == 200
    exported = r.json()["config_text"]

    assert "resolvers mydns" in exported
    assert "parse-resolv-conf" in exported
    assert "nameserver dns1 8.8.8.8:53" in exported
    assert "nameserver dns2 1.1.1.1:53" in exported
    assert "resolve_retries 3" in exported
    assert "timeout resolve 1s" in exported
    assert "timeout retry 1s" in exported
    assert "hold valid 10s" in exported
    assert "hold nx 60s" in exported
    assert "hold aa 5s" in exported
    assert "accepted_payload_size 8192" in exported


async def test_import_export_peers_new_fields(client: AsyncClient) -> None:
    """Test import/export round-trip for peer bind and default-server."""

    cfg = dedent("""\
    peers mypeers
        bind :10000 ssl crt /etc/ssl/cert.pem
        default-server ssl verify none
        peer haproxy1 10.0.0.1:10000
        peer haproxy2 10.0.0.2:10000
    """)

    r = await client.post("/api/config/import", json={"config_text": cfg, "merge": False})
    assert r.status_code == 200

    r = await client.get("/api/config/export")
    assert r.status_code == 200
    exported = r.json()["config_text"]

    assert "peers mypeers" in exported
    assert "bind :10000 ssl crt /etc/ssl/cert.pem" in exported
    assert "default-server ssl verify none" in exported
    assert "peer haproxy1 10.0.0.1:10000" in exported
    assert "peer haproxy2 10.0.0.2:10000" in exported


async def test_validate_valid_config(client: AsyncClient) -> None:
    """Validate endpoint accepts valid HAProxy config."""

    resp = await client.post("/api/config/validate", json={"config_text": SAMPLE_CONFIG})
    assert resp.status_code == 200
    assert resp.json()["valid"] is True


async def test_validate_invalid_config(client: AsyncClient) -> None:
    """Validate endpoint rejects empty config_text at schema level."""

    resp = await client.post("/api/config/validate", json={"config_text": ""})
    assert resp.status_code == 422
