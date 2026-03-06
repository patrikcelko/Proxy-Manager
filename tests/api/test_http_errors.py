"""
HTTP Errors route tests
=======================
"""

from httpx import AsyncClient


async def test_list_empty(client: AsyncClient) -> None:
    """List empty."""

    resp = await client.get("/api/http-errors")
    assert resp.status_code == 200

    data = resp.json()
    assert data["count"] == 0
    assert data["items"] == []


async def test_create(client: AsyncClient) -> None:
    """Create."""

    resp = await client.post(
        "/api/http-errors",
        json={
            "name": "myerrors",
            "comment": "Custom error pages",
        },
    )
    assert resp.status_code == 201

    data = resp.json()
    assert data["name"] == "myerrors"
    assert data["comment"] == "Custom error pages"
    assert data["entries"] == []


async def test_create_duplicate(client: AsyncClient) -> None:
    """Create duplicate."""

    await client.post("/api/http-errors", json={"name": "dup"})
    resp = await client.post("/api/http-errors", json={"name": "dup"})

    assert resp.status_code == 409


async def test_get_detail(client: AsyncClient) -> None:
    """Get detail."""

    create = await client.post("/api/http-errors", json={"name": "test-he"})
    hid = create.json()["id"]
    resp = await client.get(f"/api/http-errors/{hid}")

    assert resp.status_code == 200
    assert resp.json()["name"] == "test-he"


async def test_get_not_found(client: AsyncClient) -> None:
    """Get not found."""

    resp = await client.get("/api/http-errors/9999")
    assert resp.status_code == 404


async def test_update(client: AsyncClient) -> None:
    """Update."""

    create = await client.post("/api/http-errors", json={"name": "old"})
    hid = create.json()["id"]
    resp = await client.put(
        f"/api/http-errors/{hid}",
        json={
            "name": "new",
            "comment": "Updated",
        },
    )

    assert resp.status_code == 200
    assert resp.json()["name"] == "new"
    assert resp.json()["comment"] == "Updated"


async def test_create_with_extra_options(client: AsyncClient) -> None:
    """Test creating http-errors with extra_options."""

    resp = await client.post(
        "/api/http-errors",
        json={
            "name": "extra-errors",
            "extra_options": "log global\ncustom-directive value",
        },
    )

    assert resp.status_code == 201
    assert resp.json()["extra_options"] == "log global\ncustom-directive value"


async def test_update_extra_options(client: AsyncClient) -> None:
    """Test updating extra_options."""

    create = await client.post(
        "/api/http-errors",
        json={
            "name": "upd-extra",
            "extra_options": "initial",
        },
    )
    hid = create.json()["id"]
    resp = await client.put(
        f"/api/http-errors/{hid}",
        json={
            "name": "upd-extra",
            "extra_options": "updated",
        },
    )

    assert resp.status_code == 200
    assert resp.json()["extra_options"] == "updated"


async def test_default_null_extra_options(client: AsyncClient) -> None:
    """extra_options defaults to null when not provided."""

    resp = await client.post("/api/http-errors", json={"name": "defaults-test"})
    assert resp.status_code == 201
    assert resp.json()["extra_options"] is None


async def test_delete(client: AsyncClient) -> None:
    """Delete."""

    create = await client.post("/api/http-errors", json={"name": "to-delete"})
    hid = create.json()["id"]
    resp = await client.delete(f"/api/http-errors/{hid}")
    assert resp.status_code == 200


async def test_list_with_entries(client: AsyncClient) -> None:
    """List with entries."""

    create = await client.post("/api/http-errors", json={"name": "with-entries"})
    hid = create.json()["id"]
    await client.post(
        f"/api/http-errors/{hid}/entries",
        json={
            "status_code": 503,
            "type": "errorfile",
            "value": "/etc/haproxy/errors/503.http",
        },
    )

    resp = await client.get("/api/http-errors")
    items = resp.json()["items"]

    assert len(items) == 1
    assert len(items[0]["entries"]) == 1
    assert items[0]["entries"][0]["status_code"] == 503


async def test_create_entry(client: AsyncClient) -> None:
    """Create entry."""

    h = await client.post("/api/http-errors", json={"name": "he1"})
    hid = h.json()["id"]
    resp = await client.post(
        f"/api/http-errors/{hid}/entries",
        json={
            "status_code": 503,
            "type": "errorfile",
            "value": "/etc/haproxy/errors/503.http",
        },
    )
    assert resp.status_code == 201

    data = resp.json()
    assert data["status_code"] == 503
    assert data["type"] == "errorfile"
    assert data["value"] == "/etc/haproxy/errors/503.http"


async def test_create_errorloc(client: AsyncClient) -> None:
    """Create errorloc."""

    h = await client.post("/api/http-errors", json={"name": "he2"})
    hid = h.json()["id"]
    resp = await client.post(
        f"/api/http-errors/{hid}/entries",
        json={
            "status_code": 503,
            "type": "errorloc302",
            "value": "http://maintenance.example.com",
        },
    )

    assert resp.status_code == 201
    assert resp.json()["type"] == "errorloc302"


async def test_update_entry(client: AsyncClient) -> None:
    """Update entry."""

    h = await client.post("/api/http-errors", json={"name": "he3"})
    hid = h.json()["id"]
    entry = await client.post(
        f"/api/http-errors/{hid}/entries",
        json={
            "status_code": 503,
            "type": "errorfile",
            "value": "/etc/haproxy/errors/503.http",
        },
    )
    eid = entry.json()["id"]
    resp = await client.put(
        f"/api/http-errors/{hid}/entries/{eid}",
        json={
            "status_code": 502,
            "value": "/etc/haproxy/errors/502.http",
        },
    )

    assert resp.status_code == 200
    assert resp.json()["status_code"] == 502


async def test_delete_entry(client: AsyncClient) -> None:
    """Delete entry."""

    h = await client.post("/api/http-errors", json={"name": "he4"})
    hid = h.json()["id"]
    entry = await client.post(
        f"/api/http-errors/{hid}/entries",
        json={
            "status_code": 503,
            "type": "errorfile",
            "value": "/etc/haproxy/errors/503.http",
        },
    )
    eid = entry.json()["id"]
    resp = await client.delete(f"/api/http-errors/{hid}/entries/{eid}")

    assert resp.status_code == 200


async def test_cascade_delete(client: AsyncClient) -> None:
    """Cascade delete."""

    h = await client.post("/api/http-errors", json={"name": "cascade"})
    hid = h.json()["id"]
    await client.post(
        f"/api/http-errors/{hid}/entries",
        json={
            "status_code": 503,
            "type": "errorfile",
            "value": "/etc/haproxy/errors/503.http",
        },
    )
    resp = await client.delete(f"/api/http-errors/{hid}")
    assert resp.status_code == 200

    resp = await client.get(f"/api/http-errors/{hid}")
    assert resp.status_code == 404
