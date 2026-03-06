"""
Backend route tests
===================
"""

from httpx import AsyncClient


async def test_list_empty(client: AsyncClient) -> None:
    """List empty."""

    resp = await client.get("/api/backends")
    assert resp.status_code == 200

    data = resp.json()
    assert data["count"] == 0
    assert data["items"] == []


async def test_create(client: AsyncClient) -> None:
    """Create."""

    resp = await client.post("/api/backends", json={"name": "be_web", "mode": "http", "balance": "roundrobin"})
    assert resp.status_code == 201

    data = resp.json()
    assert data["name"] == "be_web"
    assert data["balance"] == "roundrobin"
    assert data["servers"] == []


async def test_create_duplicate(client: AsyncClient) -> None:
    """Create duplicate."""

    await client.post("/api/backends", json={"name": "be_dup"})
    resp = await client.post("/api/backends", json={"name": "be_dup"})
    assert resp.status_code == 409


async def test_get(client: AsyncClient) -> None:
    """Get."""

    create = await client.post("/api/backends", json={"name": "be_get"})
    bid = create.json()["id"]
    resp = await client.get(f"/api/backends/{bid}")

    assert resp.status_code == 200
    assert resp.json()["name"] == "be_get"
    assert "servers" in resp.json()


async def test_update(client: AsyncClient) -> None:
    """Update."""

    create = await client.post("/api/backends", json={"name": "be_upd", "balance": "roundrobin"})
    bid = create.json()["id"]
    resp = await client.put(f"/api/backends/{bid}", json={"balance": "leastconn"})

    assert resp.status_code == 200
    assert resp.json()["balance"] == "leastconn"


async def test_delete(client: AsyncClient) -> None:
    """Delete."""

    create = await client.post("/api/backends", json={"name": "be_del"})
    bid = create.json()["id"]
    resp = await client.delete(f"/api/backends/{bid}")
    assert resp.status_code == 200

    listing = await client.get("/api/backends")
    assert listing.json()["count"] == 0


async def test_list_includes_servers(client: AsyncClient) -> None:
    """List includes servers."""
    create = await client.post("/api/backends", json={"name": "be_nested"})
    bid = create.json()["id"]
    await client.post(f"/api/backends/{bid}/servers", json={"name": "srv1", "address": "10.0.0.1", "port": 8080})

    resp = await client.get("/api/backends")
    items = resp.json()["items"]
    assert len(items) == 1
    assert len(items[0]["servers"]) == 1
    assert items[0]["servers"][0]["name"] == "srv1"


async def test_create_server(client: AsyncClient) -> None:
    """Create server."""

    be = await client.post("/api/backends", json={"name": "be_srv"})
    bid = be.json()["id"]
    resp = await client.post(
        f"/api/backends/{bid}/servers",
        json={"name": "web1", "address": "192.168.1.10", "port": 80, "check_enabled": True},
    )

    assert resp.status_code == 201

    data = resp.json()
    assert data["name"] == "web1"
    assert data["address"] == "192.168.1.10"
    assert data["port"] == 80
    assert data["check_enabled"] is True


async def test_update_server(client: AsyncClient) -> None:
    """Update server."""

    be = await client.post("/api/backends", json={"name": "be_srv_upd"})
    bid = be.json()["id"]

    srv = await client.post(f"/api/backends/{bid}/servers", json={"name": "web1", "address": "10.0.0.1", "port": 80})
    sid = srv.json()["id"]

    resp = await client.put(f"/api/backends/{bid}/servers/{sid}", json={"port": 8080})
    assert resp.status_code == 200
    assert resp.json()["port"] == 8080


async def test_delete_server(client: AsyncClient) -> None:
    """Delete server."""

    be = await client.post("/api/backends", json={"name": "be_srv_del"})
    bid = be.json()["id"]

    srv = await client.post(f"/api/backends/{bid}/servers", json={"name": "web1", "address": "10.0.0.1", "port": 80})
    sid = srv.json()["id"]

    resp = await client.delete(f"/api/backends/{bid}/servers/{sid}")
    assert resp.status_code == 200


async def test_server_not_found_wrong_backend(client: AsyncClient) -> None:
    """Server not found wrong backend."""

    be1 = await client.post("/api/backends", json={"name": "be1"})
    be2 = await client.post("/api/backends", json={"name": "be2"})
    bid1 = be1.json()["id"]
    bid2 = be2.json()["id"]

    srv = await client.post(f"/api/backends/{bid1}/servers", json={"name": "s", "address": "1.2.3.4", "port": 80})
    sid = srv.json()["id"]

    resp = await client.put(f"/api/backends/{bid2}/servers/{sid}", json={"port": 9090})
    assert resp.status_code == 404
