"""
Auth route tests
================
"""

from httpx import AsyncClient


async def test_register_success(client: AsyncClient) -> None:
    """Register success."""

    resp = await client.post("/auth/register", json={"email": "new@example.com", "name": "New User", "password": "strongPassword1!"})
    assert resp.status_code == 200

    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "new@example.com"
    assert data["user"]["name"] == "New User"


async def test_register_duplicate_email(client: AsyncClient) -> None:
    """Register duplicate email."""

    await client.post("/auth/register", json={"email": "dup@example.com", "name": "A", "password": "password123"})
    resp = await client.post("/auth/register", json={"email": "dup@example.com", "name": "B", "password": "password456"})

    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


async def test_login_success(client: AsyncClient) -> None:
    """Login success."""

    await client.post("/auth/register", json={"email": "login@example.com", "name": "Login", "password": "mypassword"})
    resp = await client.post("/auth/login", json={"email": "login@example.com", "password": "mypassword"})

    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_login_wrong_password(client: AsyncClient) -> None:
    """Login wrong password."""

    await client.post("/auth/register", json={"email": "u@example.com", "name": "U", "password": "correctpassword"})
    resp = await client.post("/auth/login", json={"email": "u@example.com", "password": "wrongpassword"})
    assert resp.status_code == 401


async def test_login_nonexistent_user(client: AsyncClient) -> None:
    """Login nonexistent user."""

    resp = await client.post("/auth/login", json={"email": "nobody@example.com", "password": "whatever"})
    assert resp.status_code == 401


async def test_me_authenticated(auth_client: AsyncClient) -> None:
    """Me authenticated."""

    resp = await auth_client.get("/auth/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@example.com"


async def test_me_unauthenticated(client: AsyncClient) -> None:
    """Me unauthenticated."""

    resp = await client.get("/auth/me")
    assert resp.status_code == 401


async def test_update_name(auth_client: AsyncClient) -> None:
    """Update name."""

    resp = await auth_client.patch("/auth/profile", json={"name": "Updated Name"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"


async def test_update_password(auth_client: AsyncClient) -> None:
    """Update password."""

    resp = await auth_client.patch(
        "/auth/profile",
        json={
            "current_password": "testpassword123",
            "new_password": "newpassword456",
        },
    )
    assert resp.status_code == 200


async def test_update_password_wrong_current(auth_client: AsyncClient) -> None:
    """Update password wrong current."""

    resp = await auth_client.patch(
        "/auth/profile",
        json={
            "current_password": "wrongpassword",
            "new_password": "newpassword456",
        },
    )
    assert resp.status_code == 401
