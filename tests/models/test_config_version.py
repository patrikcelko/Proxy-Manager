"""
Tests ConfigVersion CRUD
=========================
"""

import json

from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.database.models.config_version import (
    ConfigVersion,
    compute_snapshot_hash,
    count_versions,
    create_version,
    get_latest_version,
    get_version_by_hash,
    list_versions,
)
from proxy_manager.database.models.user import create_user
from proxy_manager.utilities.auth import hash_password


async def _make_user(session: AsyncSession) -> int:
    """Helper: create a test user and return their id."""
    pw = hash_password("secret")
    user = await create_user(session, email="v@test.com", name="Version Author", password_hash=pw)
    return user.id


async def test_compute_snapshot_hash() -> None:
    """Hash is deterministic and consistent."""

    data = {"global_settings": [], "frontends": [{"name": "fe1"}]}
    h1 = compute_snapshot_hash(data)
    h2 = compute_snapshot_hash(data)
    assert h1 == h2
    assert len(h1) == 64


async def test_compute_snapshot_hash_differs() -> None:
    """Different snapshots produce different hashes."""

    h1 = compute_snapshot_hash({"a": 1})
    h2 = compute_snapshot_hash({"a": 2})
    assert h1 != h2


async def test_create_and_get_version(session: AsyncSession) -> None:
    """Create a version and retrieve it by hash."""

    uid = await _make_user(session)
    snapshot = {"global_settings": []}
    v = await create_version(session, snapshot_data=snapshot, message="initial", user_id=uid, user_name="Tester")

    assert v.id is not None
    assert len(v.hash) == 64
    assert v.message == "initial"
    assert v.user_name == "Tester"
    assert v.parent_hash is None

    fetched = await get_version_by_hash(session, v.hash)
    assert fetched is not None
    assert fetched.id == v.id
    assert json.loads(fetched.snapshot) == snapshot


async def test_get_latest_version_none(session: AsyncSession) -> None:
    """Latest version is None when no versions exist."""

    latest = await get_latest_version(session)
    assert latest is None


async def test_get_latest_version(session: AsyncSession) -> None:
    """Latest version is the most recently created."""

    uid = await _make_user(session)
    v1 = await create_version(session, snapshot_data={"v": 1}, message="first", user_id=uid, user_name="A")
    v2 = await create_version(session, snapshot_data={"v": 2}, message="second", user_id=uid, user_name="A", parent_hash=v1.hash)

    latest = await get_latest_version(session)
    assert latest is not None
    assert latest.hash == v2.hash


async def test_list_versions(session: AsyncSession) -> None:
    """List returns versions newest-first."""

    uid = await _make_user(session)
    await create_version(session, snapshot_data={"v": 1}, message="one", user_id=uid, user_name="A")
    await create_version(session, snapshot_data={"v": 2}, message="two", user_id=uid, user_name="A")
    await create_version(session, snapshot_data={"v": 3}, message="three", user_id=uid, user_name="A")

    versions = await list_versions(session, limit=2, offset=0)
    assert len(versions) == 2
    assert versions[0].message == "three"
    assert versions[1].message == "two"


async def test_count_versions(session: AsyncSession) -> None:
    """Count returns correct total."""

    uid = await _make_user(session)
    assert await count_versions(session) == 0

    await create_version(session, snapshot_data={"a": 1}, message="v1", user_id=uid, user_name="A")
    await create_version(session, snapshot_data={"a": 2}, message="v2", user_id=uid, user_name="A")

    assert await count_versions(session) == 2


async def test_version_with_parent_hash(session: AsyncSession) -> None:
    """Parent hash is stored correctly."""

    uid = await _make_user(session)
    v1 = await create_version(session, snapshot_data={"x": 1}, message="parent", user_id=uid, user_name="A")
    v2 = await create_version(session, snapshot_data={"x": 2}, message="child", user_id=uid, user_name="A", parent_hash=v1.hash)

    assert v2.parent_hash == v1.hash
    fetched = await get_version_by_hash(session, v2.hash)
    assert fetched is not None
    assert fetched.parent_hash == v1.hash


async def test_get_version_by_hash_not_found(session: AsyncSession) -> None:
    """Nonexistent hash returns None."""

    result = await get_version_by_hash(session, "a" * 64)
    assert result is None


async def test_version_repr(session: AsyncSession) -> None:
    """ConfigVersion repr is reasonable."""

    uid = await _make_user(session)
    v = await create_version(session, snapshot_data={}, message="test repr", user_id=uid, user_name="A")
    r = repr(v)
    assert "ConfigVersion" in r
    assert v.hash[:8] in r
