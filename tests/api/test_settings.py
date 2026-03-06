"""
Global & default setting route tests
=====================================
"""

from httpx import AsyncClient


async def test_global_settings_list_empty(client: AsyncClient) -> None:
    """Global settings list empty."""

    resp = await client.get("/api/global-settings")
    assert resp.status_code == 200

    data = resp.json()
    assert data["count"] == 0
    assert data["items"] == []


async def test_create(client: AsyncClient) -> None:
    """Create."""

    resp = await client.post("/api/global-settings", json={"directive": "maxconn", "value": "4096"})
    assert resp.status_code == 201

    data = resp.json()
    assert data["directive"] == "maxconn"
    assert data["value"] == "4096"
    assert "id" in data


async def test_create_and_list(client: AsyncClient) -> None:
    """Create and list."""

    await client.post("/api/global-settings", json={"directive": "log", "value": "127.0.0.1 local0"})
    await client.post("/api/global-settings", json={"directive": "maxconn", "value": "4096"})

    resp = await client.get("/api/global-settings")
    assert resp.status_code == 200
    assert resp.json()["count"] == 2


async def test_update(client: AsyncClient) -> None:
    """Update."""

    create = await client.post("/api/global-settings", json={"directive": "maxconn", "value": "1024"})
    sid = create.json()["id"]
    resp = await client.put(f"/api/global-settings/{sid}", json={"value": "8192"})

    assert resp.status_code == 200
    assert resp.json()["value"] == "8192"


async def test_update_not_found(client: AsyncClient) -> None:
    """Update not found."""

    resp = await client.put("/api/global-settings/9999", json={"value": "x"})
    assert resp.status_code == 404


async def test_delete(client: AsyncClient) -> None:
    """Delete."""

    create = await client.post("/api/global-settings", json={"directive": "test", "value": "v"})
    sid = create.json()["id"]
    resp = await client.delete(f"/api/global-settings/{sid}")

    assert resp.status_code == 200
    listing = await client.get("/api/global-settings")

    assert listing.json()["count"] == 0


async def test_delete_not_found(client: AsyncClient) -> None:
    """Delete not found."""

    resp = await client.delete("/api/global-settings/9999")
    assert resp.status_code == 404


async def test_default_settings_list_empty(client: AsyncClient) -> None:
    """Default settings list empty."""

    resp = await client.get("/api/default-settings")
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


async def test_crud_flow(client: AsyncClient) -> None:
    """Crud flow."""

    # Create
    create = await client.post("/api/default-settings", json={"directive": "timeout connect", "value": "5000"})
    assert create.status_code == 201
    sid = create.json()["id"]

    # Update
    update = await client.put(f"/api/default-settings/{sid}", json={"value": "10000"})
    assert update.status_code == 200
    assert update.json()["value"] == "10000"

    # Delete
    delete = await client.delete(f"/api/default-settings/{sid}")
    assert delete.status_code == 200

    # Verify gone
    listing = await client.get("/api/default-settings")
    assert listing.json()["count"] == 0
