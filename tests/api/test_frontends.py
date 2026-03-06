"""
Frontend route tests
====================
"""

from httpx import AsyncClient


async def test_list_empty(client: AsyncClient) -> None:
    """List empty."""

    resp = await client.get("/api/frontends")
    assert resp.status_code == 200

    data = resp.json()
    assert data["count"] == 0
    assert data["items"] == []


async def test_create(client: AsyncClient) -> None:
    """Create."""

    resp = await client.post("/api/frontends", json={"name": "fe_http", "default_backend": "be_web", "mode": "http"})
    assert resp.status_code == 201

    data = resp.json()
    assert data["name"] == "fe_http"
    assert data["default_backend"] == "be_web"
    assert data["binds"] == []
    assert data["options"] == []


async def test_create_duplicate(client: AsyncClient) -> None:
    """Create duplicate."""

    await client.post("/api/frontends", json={"name": "fe_dup"})
    resp = await client.post("/api/frontends", json={"name": "fe_dup"})

    assert resp.status_code == 409


async def test_get(client: AsyncClient) -> None:
    """Get."""

    create = await client.post("/api/frontends", json={"name": "fe_get"})
    fid = create.json()["id"]
    resp = await client.get(f"/api/frontends/{fid}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "fe_get"


async def test_update(client: AsyncClient) -> None:
    """Update."""

    create = await client.post("/api/frontends", json={"name": "fe_old"})
    fid = create.json()["id"]
    resp = await client.put(f"/api/frontends/{fid}", json={"name": "fe_new"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "fe_new"


async def test_delete(client: AsyncClient) -> None:
    """Delete."""

    create = await client.post("/api/frontends", json={"name": "fe_del"})
    fid = create.json()["id"]
    resp = await client.delete(f"/api/frontends/{fid}")
    assert resp.status_code == 200


async def test_list_includes_binds_and_options(client: AsyncClient) -> None:
    """List includes binds and options."""

    create = await client.post("/api/frontends", json={"name": "fe_nested"})
    fid = create.json()["id"]
    await client.post(f"/api/frontends/{fid}/binds", json={"bind_line": "*:80"})
    await client.post(f"/api/frontends/{fid}/options", json={"directive": "option httplog"})

    resp = await client.get("/api/frontends")
    items = resp.json()["items"]
    assert len(items) == 1
    assert len(items[0]["binds"]) == 1
    assert len(items[0]["options"]) == 1


async def test_create_bind(client: AsyncClient) -> None:
    """Create bind."""

    fe = await client.post("/api/frontends", json={"name": "fe_bind"})
    fid = fe.json()["id"]
    resp = await client.post(f"/api/frontends/{fid}/binds", json={"bind_line": "*:443 ssl crt /etc/ssl/cert.pem"})
    assert resp.status_code == 201
    assert resp.json()["bind_line"] == "*:443 ssl crt /etc/ssl/cert.pem"


async def test_update_bind(client: AsyncClient) -> None:
    """Update bind."""

    fe = await client.post("/api/frontends", json={"name": "fe_bind_upd"})
    fid = fe.json()["id"]
    bind = await client.post(f"/api/frontends/{fid}/binds", json={"bind_line": "*:80"})
    bid = bind.json()["id"]
    resp = await client.put(f"/api/frontends/{fid}/binds/{bid}", json={"bind_line": "*:8080"})

    assert resp.status_code == 200
    assert resp.json()["bind_line"] == "*:8080"


async def test_delete_bind(client: AsyncClient) -> None:
    """Delete bind."""

    fe = await client.post("/api/frontends", json={"name": "fe_bind_del"})
    fid = fe.json()["id"]
    bind = await client.post(f"/api/frontends/{fid}/binds", json={"bind_line": "*:80"})
    bid = bind.json()["id"]
    resp = await client.delete(f"/api/frontends/{fid}/binds/{bid}")
    assert resp.status_code == 200


async def test_create_option(client: AsyncClient) -> None:
    """Create option."""
    fe = await client.post("/api/frontends", json={"name": "fe_opt"})
    fid = fe.json()["id"]
    resp = await client.post(f"/api/frontends/{fid}/options", json={"directive": "option httplog"})

    assert resp.status_code == 201
    assert resp.json()["directive"] == "option httplog"


async def test_update_option(client: AsyncClient) -> None:
    """Update option."""

    fe = await client.post("/api/frontends", json={"name": "fe_opt_upd"})
    fid = fe.json()["id"]
    opt = await client.post(f"/api/frontends/{fid}/options", json={"directive": "option httplog"})
    oid = opt.json()["id"]
    resp = await client.put(f"/api/frontends/{fid}/options/{oid}", json={"directive": "option forwardfor"})

    assert resp.status_code == 200
    assert resp.json()["directive"] == "option forwardfor"


async def test_delete_option(client: AsyncClient) -> None:
    """Delete option."""

    fe = await client.post("/api/frontends", json={"name": "fe_opt_del"})
    fid = fe.json()["id"]
    opt = await client.post(f"/api/frontends/{fid}/options", json={"directive": "option httplog"})
    oid = opt.json()["id"]
    resp = await client.delete(f"/api/frontends/{fid}/options/{oid}")
    assert resp.status_code == 200


async def test_list_all_empty(client: AsyncClient) -> None:
    """List all empty."""

    resp = await client.get("/api/acl-rules")
    assert resp.status_code == 200
    assert resp.json()["count"] == 0
    assert resp.json()["items"] == []


async def test_create_acl_rule(client: AsyncClient) -> None:
    """Create acl rule."""

    fe = await client.post("/api/frontends", json={"name": "fe_acl"})
    fid = fe.json()["id"]
    resp = await client.post("/api/acl-rules", json={"frontend_id": fid, "domain": "example.com", "backend_name": "be_example"})
    assert resp.status_code == 201

    data = resp.json()
    assert data["domain"] == "example.com"
    assert data["backend_name"] == "be_example"


async def test_create_acl_no_frontend(client: AsyncClient) -> None:
    """Create acl no frontend."""

    resp = await client.post("/api/acl-rules", json={"domain": "example.com", "backend_name": "be_example"})
    assert resp.status_code == 201
    assert resp.json()["frontend_id"] is None


async def test_update_acl_rule(client: AsyncClient) -> None:
    """Update acl rule."""

    fe = await client.post("/api/frontends", json={"name": "fe_acl_upd"})
    fid = fe.json()["id"]
    acl = await client.post("/api/acl-rules", json={"frontend_id": fid, "domain": "old.com", "backend_name": "be_old"})
    rid = acl.json()["id"]
    resp = await client.put(f"/api/acl-rules/{rid}", json={"domain": "new.com"})

    assert resp.status_code == 200
    assert resp.json()["domain"] == "new.com"


async def test_delete_acl_rule(client: AsyncClient) -> None:
    """Delete acl rule."""

    acl = await client.post("/api/acl-rules", json={"domain": "del.com", "backend_name": "be_del"})
    rid = acl.json()["id"]
    resp = await client.delete(f"/api/acl-rules/{rid}")

    assert resp.status_code == 200


async def test_list_by_frontend(client: AsyncClient) -> None:
    """List by frontend."""

    fe = await client.post("/api/frontends", json={"name": "fe_acl_list"})
    fid = fe.json()["id"]
    await client.post("/api/acl-rules", json={"frontend_id": fid, "domain": "a.com", "backend_name": "be_a"})
    await client.post("/api/acl-rules", json={"frontend_id": fid, "domain": "b.com", "backend_name": "be_b"})

    resp = await client.get(f"/api/frontends/{fid}/acl-rules")
    assert resp.status_code == 200
    assert resp.json()["count"] == 2
