"""
Auth protection tests
=====================

Verifies that endpoints using get_current_user dependency
properly reject unauthenticated/invalid requests with 401.

NOTE: Only /me and /profile endpoints use auth. The config
API endpoints are open by design (internal tool assumption).
"""

import os

import jwt
import pytest
from httpx import AsyncClient

# Only these endpoints use the get_current_user dependency
_AUTH_PROTECTED_ENDPOINTS = [
    ("GET", "/auth/me"),
    ("PATCH", "/auth/profile"),
]


@pytest.mark.parametrize("method, path", _AUTH_PROTECTED_ENDPOINTS)
async def test_unauthenticated_returns_401(client: AsyncClient, method: str, path: str) -> None:
    """Unauthenticated returns 401."""

    resp = await client.request(method, path)
    assert resp.status_code in (401, 403), f"{method} {path} returned {resp.status_code}, expected 401/403"


async def test_invalid_token_returns_401(client: AsyncClient) -> None:
    """A forged/invalid token should be rejected on /me."""

    headers = {"Authorization": "Bearer invalid.token.here"}
    resp = await client.get("/auth/me", headers=headers)

    assert resp.status_code == 401


async def test_expired_token_returns_401(client: AsyncClient) -> None:
    """An expired JWT should be rejected."""


    token = jwt.encode(
        {"sub": "1", "exp": 0},
        os.environ.get("SECRET_KEY", "test-secret-key-for-pytest-do-not-use-in-production"),
        algorithm="HS256",
    )
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.get("/auth/me", headers=headers)

    assert resp.status_code == 401


async def test_valid_auth_succeeds(auth_client: AsyncClient) -> None:
    """Sanity: authenticated requests work fine."""

    resp = await auth_client.get("/auth/me")
    assert resp.status_code == 200

    data = resp.json()
    assert "email" in data
