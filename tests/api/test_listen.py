"""
Listen block route tests
========================
"""

from httpx import AsyncClient


async def test_list_empty(client: AsyncClient) -> None:
    """List empty."""

    resp = await client.get("/api/listen-blocks")
    assert resp.status_code == 200

    data = resp.json()
    assert data["count"] == 0
    assert data["items"] == []


async def test_create(client: AsyncClient) -> None:
    """Create."""

    resp = await client.post("/api/listen-blocks", json={"name": "stats", "mode": "http", "content": "stats enable\nstats uri /stats"})
    assert resp.status_code == 201

    data = resp.json()
    assert data["name"] == "stats"
    assert data["binds"] == []


async def test_create_duplicate(client: AsyncClient) -> None:
    """Create duplicate."""

    await client.post("/api/listen-blocks", json={"name": "dup_listen"})
    resp = await client.post("/api/listen-blocks", json={"name": "dup_listen"})
    assert resp.status_code == 409


async def test_get(client: AsyncClient) -> None:
    """Get."""

    create = await client.post("/api/listen-blocks", json={"name": "lb_get"})
    lid = create.json()["id"]
    resp = await client.get(f"/api/listen-blocks/{lid}")

    assert resp.status_code == 200
    assert resp.json()["name"] == "lb_get"
    assert "binds" in resp.json()


async def test_update(client: AsyncClient) -> None:
    """Update."""

    create = await client.post("/api/listen-blocks", json={"name": "lb_upd"})
    lid = create.json()["id"]
    resp = await client.put(f"/api/listen-blocks/{lid}", json={"mode": "tcp"})

    assert resp.status_code == 200
    assert resp.json()["mode"] == "tcp"


async def test_delete(client: AsyncClient) -> None:
    """Delete."""

    create = await client.post("/api/listen-blocks", json={"name": "lb_del"})
    lid = create.json()["id"]
    resp = await client.delete(f"/api/listen-blocks/{lid}")
    assert resp.status_code == 200

    listing = await client.get("/api/listen-blocks")
    assert listing.json()["count"] == 0


async def test_not_found(client: AsyncClient) -> None:
    """Not found."""

    resp = await client.get("/api/listen-blocks/9999")
    assert resp.status_code == 404

    resp = await client.put("/api/listen-blocks/9999", json={"name": "x"})
    assert resp.status_code == 404

    resp = await client.delete("/api/listen-blocks/9999")
    assert resp.status_code == 404


async def test_create_bind(client: AsyncClient) -> None:
    """Create bind."""

    lb = await client.post("/api/listen-blocks", json={"name": "bind-test"})
    lid = lb.json()["id"]
    resp = await client.post(f"/api/listen-blocks/{lid}/binds", json={"bind_line": "*:8404"})
    assert resp.status_code == 201

    data = resp.json()
    assert data["bind_line"] == "*:8404"
    assert data["listen_block_id"] == lid


async def test_bind_appears_in_detail(client: AsyncClient) -> None:
    """Bind appears in detail."""

    lb = await client.post("/api/listen-blocks", json={"name": "bind-detail"})
    lid = lb.json()["id"]
    await client.post(f"/api/listen-blocks/{lid}/binds", json={"bind_line": "*:80"})
    await client.post(f"/api/listen-blocks/{lid}/binds", json={"bind_line": "*:443 ssl crt /etc/ssl/cert.pem"})
    resp = await client.get(f"/api/listen-blocks/{lid}")
    data = resp.json()
    assert len(data["binds"]) == 2

    lines = {b["bind_line"] for b in data["binds"]}
    assert "*:80" in lines
    assert "*:443 ssl crt /etc/ssl/cert.pem" in lines


async def test_update_bind(client: AsyncClient) -> None:
    """Update bind."""

    lb = await client.post("/api/listen-blocks", json={"name": "bind-upd"})
    lid = lb.json()["id"]
    bind = await client.post(f"/api/listen-blocks/{lid}/binds", json={"bind_line": ":80"})
    bid = bind.json()["id"]
    resp = await client.put(f"/api/listen-blocks/{lid}/binds/{bid}", json={"bind_line": ":8080"})

    assert resp.status_code == 200
    assert resp.json()["bind_line"] == ":8080"


async def test_delete_bind(client: AsyncClient) -> None:
    """Delete bind."""

    lb = await client.post("/api/listen-blocks", json={"name": "bind-del"})
    lid = lb.json()["id"]
    bind = await client.post(f"/api/listen-blocks/{lid}/binds", json={"bind_line": ":80"})
    bid = bind.json()["id"]
    resp = await client.delete(f"/api/listen-blocks/{lid}/binds/{bid}")
    assert resp.status_code == 200

    detail = await client.get(f"/api/listen-blocks/{lid}")
    assert len(detail.json()["binds"]) == 0


async def test_bind_not_found(client: AsyncClient) -> None:
    """Bind not found."""

    lb = await client.post("/api/listen-blocks", json={"name": "bind-nf"})
    lid = lb.json()["id"]
    resp = await client.put(f"/api/listen-blocks/{lid}/binds/9999", json={"bind_line": "x"})
    assert resp.status_code == 404

    resp = await client.delete(f"/api/listen-blocks/{lid}/binds/9999")
    assert resp.status_code == 404


async def test_bind_wrong_parent(client: AsyncClient) -> None:
    """Bind wrong parent."""

    lb1 = await client.post("/api/listen-blocks", json={"name": "bind-wp1"})
    lb2 = await client.post("/api/listen-blocks", json={"name": "bind-wp2"})
    lid1 = lb1.json()["id"]
    lid2 = lb2.json()["id"]
    bind = await client.post(f"/api/listen-blocks/{lid1}/binds", json={"bind_line": ":80"})
    bid = bind.json()["id"]
    resp = await client.put(f"/api/listen-blocks/{lid2}/binds/{bid}", json={"bind_line": ":81"})
    assert resp.status_code == 404

    resp = await client.delete(f"/api/listen-blocks/{lid2}/binds/{bid}")
    assert resp.status_code == 404


async def test_bind_parent_not_found(client: AsyncClient) -> None:
    """Bind parent not found."""

    resp = await client.post("/api/listen-blocks/9999/binds", json={"bind_line": ":80"})
    assert resp.status_code == 404


async def test_bind_cascade_delete(client: AsyncClient) -> None:
    """Deleting a listen block should cascade-delete its binds."""

    lb = await client.post("/api/listen-blocks", json={"name": "bind-cascade"})
    lid = lb.json()["id"]
    await client.post(f"/api/listen-blocks/{lid}/binds", json={"bind_line": ":80"})
    await client.post(f"/api/listen-blocks/{lid}/binds", json={"bind_line": ":443"})
    resp = await client.delete(f"/api/listen-blocks/{lid}")

    assert resp.status_code == 200


async def test_create_with_balance(client: AsyncClient) -> None:
    """Create with balance."""

    resp = await client.post(
        "/api/listen-blocks",
        json={
            "name": "mysql-lb",
            "mode": "tcp",
            "balance": "roundrobin",
        },
    )
    assert resp.status_code == 201

    data = resp.json()
    assert data["balance"] == "roundrobin"
    assert data["mode"] == "tcp"


async def test_create_with_all_fields(client: AsyncClient) -> None:
    """Create with all fields."""

    resp = await client.post(
        "/api/listen-blocks",
        json={
            "name": "full-listen",
            "mode": "tcp",
            "balance": "leastconn",
            "maxconn": 2000,
            "timeout_client": "30s",
            "timeout_server": "30s",
            "timeout_connect": "5s",
            "default_server_params": "inter 3s fall 3 rise 2",
            "option_httplog": False,
            "option_tcplog": True,
            "option_forwardfor": False,
            "content": "option pgsql-check user haproxy",
            "comment": "PostgreSQL load balancer",
        },
    )

    assert resp.status_code == 201
    data = resp.json()

    assert data["balance"] == "leastconn"
    assert data["maxconn"] == 2000
    assert data["timeout_client"] == "30s"
    assert data["timeout_server"] == "30s"
    assert data["timeout_connect"] == "5s"
    assert data["default_server_params"] == "inter 3s fall 3 rise 2"
    assert data["option_tcplog"] is True
    assert data["option_httplog"] is False
    assert data["option_forwardfor"] is False
    assert data["content"] == "option pgsql-check user haproxy"
    assert data["comment"] == "PostgreSQL load balancer"


async def test_create_defaults_for_new_fields(client: AsyncClient) -> None:
    """New fields should default to None/False when not provided."""

    resp = await client.post(
        "/api/listen-blocks",
        json={
            "name": "minimal",
        },
    )
    assert resp.status_code == 201

    data = resp.json()
    assert data["balance"] is None
    assert data["maxconn"] is None
    assert data["timeout_client"] is None
    assert data["timeout_server"] is None
    assert data["timeout_connect"] is None
    assert data["default_server_params"] is None
    assert data["option_httplog"] is False
    assert data["option_tcplog"] is False
    assert data["option_forwardfor"] is False


async def test_update_new_fields(client: AsyncClient) -> None:
    """Update new fields."""

    create = await client.post(
        "/api/listen-blocks",
        json={
            "name": "upd-fields",
        },
    )
    lid = create.json()["id"]
    resp = await client.put(
        f"/api/listen-blocks/{lid}",
        json={
            "balance": "source",
            "maxconn": 500,
            "timeout_client": "10s",
            "timeout_server": "20s",
            "option_forwardfor": True,
        },
    )
    assert resp.status_code == 200

    data = resp.json()
    assert data["balance"] == "source"
    assert data["maxconn"] == 500
    assert data["timeout_client"] == "10s"
    assert data["timeout_server"] == "20s"
    assert data["option_forwardfor"] is True


async def test_update_clears_optional_fields(client: AsyncClient) -> None:
    """Setting optional fields to None should clear them."""

    create = await client.post(
        "/api/listen-blocks",
        json={
            "name": "clear-fields",
            "balance": "roundrobin",
            "timeout_client": "30s",
        },
    )
    lid = create.json()["id"]
    resp = await client.put(
        f"/api/listen-blocks/{lid}",
        json={
            "balance": None,
            "timeout_client": None,
        },
    )
    assert resp.status_code == 200

    data = resp.json()
    assert data["balance"] is None
    assert data["timeout_client"] is None


async def test_update_boolean_options(client: AsyncClient) -> None:
    """Update boolean options."""

    create = await client.post(
        "/api/listen-blocks",
        json={
            "name": "bool-opts",
        },
    )
    lid = create.json()["id"]
    # Enable options
    resp = await client.put(
        f"/api/listen-blocks/{lid}",
        json={
            "option_httplog": True,
            "option_tcplog": True,
            "option_forwardfor": True,
        },
    )

    data = resp.json()
    assert data["option_httplog"] is True
    assert data["option_tcplog"] is True
    assert data["option_forwardfor"] is True

    # Disable options
    resp = await client.put(
        f"/api/listen-blocks/{lid}",
        json={
            "option_httplog": False,
            "option_tcplog": False,
            "option_forwardfor": False,
        },
    )
    data = resp.json()
    assert data["option_httplog"] is False
    assert data["option_tcplog"] is False
    assert data["option_forwardfor"] is False


async def test_response_includes_all_fields(client: AsyncClient) -> None:
    """Verify the response schema includes all expanded fields."""

    create = await client.post(
        "/api/listen-blocks",
        json={
            "name": "schema-check",
            "mode": "http",
            "balance": "roundrobin",
            "maxconn": 1000,
            "timeout_client": "30s",
            "timeout_server": "60s",
            "timeout_connect": "5s",
            "default_server_params": "inter 3s fall 3",
            "option_httplog": True,
            "content": "stats enable\nstats uri /stats",
            "comment": "Test schema",
        },
    )
    lid = create.json()["id"]
    resp = await client.get(f"/api/listen-blocks/{lid}")
    data = resp.json()
    expected_keys = {
        "id",
        "name",
        "mode",
        "balance",
        "maxconn",
        "timeout_client",
        "timeout_server",
        "timeout_connect",
        "default_server_params",
        "option_httplog",
        "option_tcplog",
        "option_forwardfor",
        "content",
        "comment",
        "sort_order",
        "binds",
    }

    assert expected_keys.issubset(set(data.keys()))


async def test_list_with_expanded_fields(client: AsyncClient) -> None:
    """List with expanded fields."""

    await client.post(
        "/api/listen-blocks",
        json={
            "name": "lb-list-1",
            "balance": "roundrobin",
        },
    )
    await client.post(
        "/api/listen-blocks",
        json={
            "name": "lb-list-2",
            "balance": "leastconn",
            "option_tcplog": True,
        },
    )

    resp = await client.get("/api/listen-blocks")
    data = resp.json()
    assert data["count"] == 2

    balances = {item["balance"] for item in data["items"]}
    assert balances == {"roundrobin", "leastconn"}
