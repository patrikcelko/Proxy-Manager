"""
Mailers route tests
===================
"""

from httpx import AsyncClient


async def test_list_empty(client: AsyncClient) -> None:
    """List empty."""

    resp = await client.get("/api/mailers")
    assert resp.status_code == 200

    data = resp.json()
    assert data["count"] == 0
    assert data["items"] == []


async def test_create(client: AsyncClient) -> None:
    """Create."""

    resp = await client.post(
        "/api/mailers",
        json={
            "name": "mymailers",
            "timeout_mail": "10s",
            "comment": "Alert mailers",
        },
    )

    assert resp.status_code == 201

    data = resp.json()
    assert data["name"] == "mymailers"
    assert data["timeout_mail"] == "10s"
    assert data["comment"] == "Alert mailers"
    assert data["entries"] == []


async def test_create_duplicate(client: AsyncClient) -> None:
    """Create duplicate."""

    await client.post("/api/mailers", json={"name": "dup"})
    resp = await client.post("/api/mailers", json={"name": "dup"})
    assert resp.status_code == 409


async def test_get_detail(client: AsyncClient) -> None:
    """Get detail."""

    create = await client.post("/api/mailers", json={"name": "test-m"})
    mid = create.json()["id"]
    resp = await client.get(f"/api/mailers/{mid}")

    assert resp.status_code == 200
    assert resp.json()["name"] == "test-m"


async def test_get_not_found(client: AsyncClient) -> None:
    """Get not found."""

    resp = await client.get("/api/mailers/9999")
    assert resp.status_code == 404


async def test_update(client: AsyncClient) -> None:
    """Update."""

    create = await client.post("/api/mailers", json={"name": "old"})
    mid = create.json()["id"]
    resp = await client.put(
        f"/api/mailers/{mid}",
        json={
            "name": "new",
            "timeout_mail": "20s",
        },
    )

    assert resp.status_code == 200
    assert resp.json()["name"] == "new"
    assert resp.json()["timeout_mail"] == "20s"


async def test_create_with_extra_options(client: AsyncClient) -> None:
    """Test creating mailer section with extra_options."""

    resp = await client.post(
        "/api/mailers",
        json={
            "name": "extra-mailers",
            "extra_options": "log global\ncustom-directive value",
        },
    )

    assert resp.status_code == 201
    assert resp.json()["extra_options"] == "log global\ncustom-directive value"


async def test_update_extra_options(client: AsyncClient) -> None:
    """Test updating and clearing extra_options."""

    create = await client.post(
        "/api/mailers",
        json={
            "name": "upd-extra",
            "extra_options": "initial directive",
        },
    )
    mid = create.json()["id"]
    resp = await client.put(
        f"/api/mailers/{mid}",
        json={
            "name": "upd-extra",
            "extra_options": "updated directive",
        },
    )

    assert resp.status_code == 200
    assert resp.json()["extra_options"] == "updated directive"


async def test_default_null_extra_options(client: AsyncClient) -> None:
    """extra_options defaults to null when not provided."""

    resp = await client.post("/api/mailers", json={"name": "defaults-test"})
    assert resp.status_code == 201
    assert resp.json()["extra_options"] is None


async def test_delete(client: AsyncClient) -> None:
    """Delete."""

    create = await client.post("/api/mailers", json={"name": "to-delete"})
    mid = create.json()["id"]
    resp = await client.delete(f"/api/mailers/{mid}")
    assert resp.status_code == 200


async def test_list_with_entries(client: AsyncClient) -> None:
    """List with entries."""

    create = await client.post("/api/mailers", json={"name": "with-entries"})
    mid = create.json()["id"]
    await client.post(
        f"/api/mailers/{mid}/entries",
        json={
            "name": "smtp1",
            "address": "smtp.example.com",
            "port": 25,
        },
    )
    resp = await client.get("/api/mailers")
    items = resp.json()["items"]

    assert len(items) == 1
    assert len(items[0]["entries"]) == 1
    assert items[0]["entries"][0]["name"] == "smtp1"


async def test_create_entry(client: AsyncClient) -> None:
    """Create entry."""

    m = await client.post("/api/mailers", json={"name": "m1"})
    mid = m.json()["id"]
    resp = await client.post(
        f"/api/mailers/{mid}/entries",
        json={
            "name": "smtp1",
            "address": "smtp.example.com",
            "port": 25,
        },
    )
    assert resp.status_code == 201

    data = resp.json()
    assert data["name"] == "smtp1"
    assert data["address"] == "smtp.example.com"
    assert data["port"] == 25

    # SMTP auth defaults
    assert data["smtp_auth"] is False
    assert data["smtp_user"] is None
    assert data["has_smtp_password"] is False
    assert data["use_tls"] is False
    assert data["use_starttls"] is False


async def test_create_entry_with_smtp_auth(client: AsyncClient) -> None:
    """Create entry with smtp auth."""

    m = await client.post("/api/mailers", json={"name": "auth-m"})
    mid = m.json()["id"]
    resp = await client.post(
        f"/api/mailers/{mid}/entries",
        json={
            "name": "gmail",
            "address": "smtp.gmail.com",
            "port": 587,
            "smtp_auth": True,
            "smtp_user": "user@gmail.com",
            "smtp_password": "app-password",
            "use_tls": False,
            "use_starttls": True,
        },
    )
    assert resp.status_code == 201

    data = resp.json()
    assert data["smtp_auth"] is True
    assert data["smtp_user"] == "user@gmail.com"
    assert data["has_smtp_password"] is True
    assert data["use_tls"] is False
    assert data["use_starttls"] is True


async def test_update_entry_smtp_auth(client: AsyncClient) -> None:
    """Update entry smtp auth."""

    m = await client.post("/api/mailers", json={"name": "upd-auth-m"})
    mid = m.json()["id"]
    entry = await client.post(
        f"/api/mailers/{mid}/entries",
        json={
            "name": "smtp1",
            "address": "smtp.example.com",
            "port": 25,
        },
    )
    eid = entry.json()["id"]
    resp = await client.put(
        f"/api/mailers/{mid}/entries/{eid}",
        json={
            "smtp_auth": True,
            "smtp_user": "admin",
            "smtp_password": "secret",
            "use_tls": True,
        },
    )
    assert resp.status_code == 200

    data = resp.json()
    assert data["smtp_auth"] is True
    assert data["smtp_user"] == "admin"
    assert data["has_smtp_password"] is True
    assert data["use_tls"] is True


async def test_smtp_auth_in_section_detail(client: AsyncClient) -> None:
    """SMTP auth fields show up in section detail response."""

    m = await client.post("/api/mailers", json={"name": "detail-m"})
    mid = m.json()["id"]
    await client.post(
        f"/api/mailers/{mid}/entries",
        json={
            "name": "smtp1",
            "address": "smtp.example.com",
            "port": 587,
            "smtp_auth": True,
            "smtp_user": "user",
            "smtp_password": "pass",
            "use_starttls": True,
        },
    )
    resp = await client.get(f"/api/mailers/{mid}")
    assert resp.status_code == 200

    entries = resp.json()["entries"]
    assert len(entries) == 1
    assert entries[0]["smtp_auth"] is True
    assert entries[0]["smtp_user"] == "user"
    assert entries[0]["use_starttls"] is True


async def test_update_entry(client: AsyncClient) -> None:
    """Update entry."""

    m = await client.post("/api/mailers", json={"name": "m2"})
    mid = m.json()["id"]
    entry = await client.post(
        f"/api/mailers/{mid}/entries",
        json={
            "name": "smtp1",
            "address": "smtp.example.com",
            "port": 25,
        },
    )
    eid = entry.json()["id"]
    resp = await client.put(
        f"/api/mailers/{mid}/entries/{eid}",
        json={
            "address": "smtp2.example.com",
            "port": 587,
        },
    )

    assert resp.status_code == 200
    assert resp.json()["address"] == "smtp2.example.com"
    assert resp.json()["port"] == 587


async def test_delete_entry(client: AsyncClient) -> None:
    """Delete entry."""

    m = await client.post("/api/mailers", json={"name": "m3"})
    mid = m.json()["id"]
    entry = await client.post(
        f"/api/mailers/{mid}/entries",
        json={
            "name": "smtp1",
            "address": "smtp.example.com",
            "port": 25,
        },
    )
    eid = entry.json()["id"]
    resp = await client.delete(f"/api/mailers/{mid}/entries/{eid}")

    assert resp.status_code == 200


async def test_cascade_delete(client: AsyncClient) -> None:
    """Cascade delete."""

    m = await client.post("/api/mailers", json={"name": "cascade"})
    mid = m.json()["id"]
    await client.post(
        f"/api/mailers/{mid}/entries",
        json={
            "name": "smtp1",
            "address": "smtp.example.com",
            "port": 25,
        },
    )
    resp = await client.delete(f"/api/mailers/{mid}")
    assert resp.status_code == 200

    resp = await client.get(f"/api/mailers/{mid}")
    assert resp.status_code == 404
