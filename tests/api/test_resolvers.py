"""
Resolver route tests
====================
"""

from httpx import AsyncClient


async def test_list_empty(client: AsyncClient) -> None:
    """List empty."""

    resp = await client.get("/api/resolvers")
    assert resp.status_code == 200

    data = resp.json()
    assert data["count"] == 0
    assert data["items"] == []


async def test_create(client: AsyncClient) -> None:
    """Create."""

    resp = await client.post(
        "/api/resolvers",
        json={
            "name": "mydns",
            "resolve_retries": 3,
            "timeout_resolve": "1s",
            "timeout_retry": "1s",
        },
    )
    assert resp.status_code == 201

    data = resp.json()
    assert data["name"] == "mydns"
    assert data["resolve_retries"] == 3
    assert data["timeout_resolve"] == "1s"
    assert data["nameservers"] == []


async def test_create_duplicate(client: AsyncClient) -> None:
    """Create duplicate."""

    await client.post("/api/resolvers", json={"name": "dup"})
    resp = await client.post("/api/resolvers", json={"name": "dup"})
    assert resp.status_code == 409


async def test_get_detail(client: AsyncClient) -> None:
    """Get detail."""

    create = await client.post("/api/resolvers", json={"name": "test-res"})
    rid = create.json()["id"]
    resp = await client.get(f"/api/resolvers/{rid}")

    assert resp.status_code == 200
    assert resp.json()["name"] == "test-res"


async def test_get_not_found(client: AsyncClient) -> None:
    """Get not found."""

    resp = await client.get("/api/resolvers/9999")
    assert resp.status_code == 404


async def test_update(client: AsyncClient) -> None:
    """Update."""

    create = await client.post("/api/resolvers", json={"name": "old"})
    rid = create.json()["id"]
    resp = await client.put(
        f"/api/resolvers/{rid}",
        json={
            "name": "new",
            "resolve_retries": 5,
            "hold_valid": "30s",
        },
    )
    assert resp.status_code == 200

    data = resp.json()
    assert data["name"] == "new"
    assert data["resolve_retries"] == 5
    assert data["hold_valid"] == "30s"


async def test_delete(client: AsyncClient) -> None:
    """Delete."""

    create = await client.post("/api/resolvers", json={"name": "to-delete"})
    rid = create.json()["id"]
    resp = await client.delete(f"/api/resolvers/{rid}")
    assert resp.status_code == 200

    resp = await client.get(f"/api/resolvers/{rid}")
    assert resp.status_code == 404


async def test_create_with_all_fields(client: AsyncClient) -> None:
    """Create with all fields."""

    resp = await client.post(
        "/api/resolvers",
        json={
            "name": "full",
            "resolve_retries": 3,
            "timeout_resolve": "1s",
            "timeout_retry": "2s",
            "hold_valid": "10s",
            "hold_other": "30s",
            "hold_refused": "30s",
            "hold_timeout": "30s",
            "hold_obsolete": "30s",
            "hold_nx": "60s",
            "hold_aa": "5s",
            "accepted_payload_size": 8192,
            "parse_resolv_conf": 1,
            "comment": "Primary DNS",
            "extra_options": "some-future-directive",
        },
    )
    assert resp.status_code == 201

    data = resp.json()
    assert data["accepted_payload_size"] == 8192
    assert data["comment"] == "Primary DNS"
    assert data["extra_options"] == "some-future-directive"
    assert data["hold_nx"] == "60s"
    assert data["hold_aa"] == "5s"
    assert data["parse_resolv_conf"] == 1


async def test_create_hold_nx_aa(client: AsyncClient) -> None:
    """Test that hold_nx and hold_aa fields are stored and returned."""

    resp = await client.post(
        "/api/resolvers",
        json={
            "name": "hold-test",
            "hold_nx": "120s",
            "hold_aa": "15s",
        },
    )
    assert resp.status_code == 201

    data = resp.json()
    assert data["hold_nx"] == "120s"
    assert data["hold_aa"] == "15s"


async def test_update_hold_nx_aa(client: AsyncClient) -> None:
    """Test updating hold_nx and hold_aa fields."""

    create = await client.post("/api/resolvers", json={"name": "upd-hold"})
    rid = create.json()["id"]
    resp = await client.put(
        f"/api/resolvers/{rid}",
        json={
            "name": "upd-hold",
            "hold_nx": "30s",
            "hold_aa": "10s",
        },
    )

    assert resp.status_code == 200
    assert resp.json()["hold_nx"] == "30s"
    assert resp.json()["hold_aa"] == "10s"


async def test_create_parse_resolv_conf(client: AsyncClient) -> None:
    """Test parse_resolv_conf field."""

    resp = await client.post(
        "/api/resolvers",
        json={
            "name": "resolv-test",
            "parse_resolv_conf": 1,
        },
    )

    assert resp.status_code == 201
    assert resp.json()["parse_resolv_conf"] == 1


async def test_update_parse_resolv_conf(client: AsyncClient) -> None:
    """Test clearing parse_resolv_conf."""

    create = await client.post(
        "/api/resolvers",
        json={
            "name": "resolv-upd",
            "parse_resolv_conf": 1,
        },
    )
    rid = create.json()["id"]
    resp = await client.put(
        f"/api/resolvers/{rid}",
        json={
            "name": "resolv-upd",
            "parse_resolv_conf": None,
        },
    )

    assert resp.status_code == 200
    assert resp.json()["parse_resolv_conf"] is None


async def test_default_null_new_fields(client: AsyncClient) -> None:
    """New fields default to null when not provided."""

    resp = await client.post("/api/resolvers", json={"name": "defaults-test"})
    assert resp.status_code == 201

    data = resp.json()
    assert data["hold_nx"] is None
    assert data["hold_aa"] is None
    assert data["parse_resolv_conf"] is None


async def test_list_with_nameservers(client: AsyncClient) -> None:
    """List with nameservers."""

    create = await client.post("/api/resolvers", json={"name": "with-ns"})
    rid = create.json()["id"]
    await client.post(
        f"/api/resolvers/{rid}/nameservers",
        json={
            "name": "dns1",
            "address": "8.8.8.8",
            "port": 53,
        },
    )
    resp = await client.get("/api/resolvers")
    assert resp.status_code == 200

    items = resp.json()["items"]
    assert len(items) == 1
    assert len(items[0]["nameservers"]) == 1
    assert items[0]["nameservers"][0]["name"] == "dns1"


async def test_create_nameserver(client: AsyncClient) -> None:
    """Create nameserver."""

    r = await client.post("/api/resolvers", json={"name": "res1"})
    rid = r.json()["id"]
    resp = await client.post(
        f"/api/resolvers/{rid}/nameservers",
        json={
            "name": "dns1",
            "address": "8.8.8.8",
            "port": 53,
        },
    )
    assert resp.status_code == 201

    data = resp.json()
    assert data["name"] == "dns1"
    assert data["address"] == "8.8.8.8"
    assert data["port"] == 53


async def test_update_nameserver(client: AsyncClient) -> None:
    """Update nameserver."""

    r = await client.post("/api/resolvers", json={"name": "res2"})
    rid = r.json()["id"]
    ns = await client.post(
        f"/api/resolvers/{rid}/nameservers",
        json={
            "name": "dns1",
            "address": "8.8.8.8",
            "port": 53,
        },
    )
    nid = ns.json()["id"]
    resp = await client.put(
        f"/api/resolvers/{rid}/nameservers/{nid}",
        json={
            "address": "1.1.1.1",
            "port": 5353,
        },
    )

    assert resp.status_code == 200
    assert resp.json()["address"] == "1.1.1.1"
    assert resp.json()["port"] == 5353


async def test_delete_nameserver(client: AsyncClient) -> None:
    """Delete nameserver."""

    r = await client.post("/api/resolvers", json={"name": "res3"})
    rid = r.json()["id"]
    ns = await client.post(
        f"/api/resolvers/{rid}/nameservers",
        json={
            "name": "dns1",
            "address": "8.8.8.8",
            "port": 53,
        },
    )
    nid = ns.json()["id"]
    resp = await client.delete(f"/api/resolvers/{rid}/nameservers/{nid}")

    assert resp.status_code == 200


async def test_cascade_delete(client: AsyncClient) -> None:
    """Cascade delete."""

    r = await client.post("/api/resolvers", json={"name": "cascade"})
    rid = r.json()["id"]
    await client.post(
        f"/api/resolvers/{rid}/nameservers",
        json={
            "name": "dns1",
            "address": "8.8.8.8",
            "port": 53,
        },
    )
    resp = await client.delete(f"/api/resolvers/{rid}")
    assert resp.status_code == 200

    # Verify resolver is gone
    resp = await client.get(f"/api/resolvers/{rid}")
    assert resp.status_code == 404
