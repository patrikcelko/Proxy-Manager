"""
Config version model
====================

Stores committed configuration snapshots for version control.
Each version contains a full JSON snapshot of all config entities,
a SHA-256 hash for identification, and metadata about who committed it.
"""

import datetime
import hashlib
import json
import uuid
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from proxy_manager.database.models.base import Base


class ConfigVersion(Base):
    """A committed configuration version with full snapshot."""

    __tablename__ = "config_versions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    parent_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<ConfigVersion(hash={self.hash[:8]!r}, message={self.message!r})>"


def compute_snapshot_hash(snapshot_data: dict[str, Any]) -> str:
    """Compute SHA-256 hash of a snapshot dictionary."""

    canonical = json.dumps(snapshot_data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


async def create_version(
    session: AsyncSession,
    *,
    snapshot_data: dict[str, Any],
    message: str,
    user_id: int,
    user_name: str,
    parent_hash: str | None = None,
) -> ConfigVersion:
    """Create a new config version from a snapshot.

    The hash includes metadata (parent, message, timestamp) so that
    versions with identical snapshots still get unique hashes.
    """

    snapshot_json = json.dumps(snapshot_data, sort_keys=True, default=str)

    # Include metadata in hash (like Git commits) so rollbacks get unique hashes
    hash_input = json.dumps(
        {
            "snapshot": snapshot_data,
            "parent_hash": parent_hash,
            "message": message,
            "user_id": user_id,
            "nonce": uuid.uuid4().hex,
        },
        sort_keys=True,
        default=str,
    )
    version_hash = hashlib.sha256(hash_input.encode()).hexdigest()

    version = ConfigVersion(
        hash=version_hash,
        message=message,
        user_id=user_id,
        user_name=user_name,
        snapshot=snapshot_json,
        parent_hash=parent_hash,
    )
    session.add(version)
    await session.commit()
    await session.refresh(version)
    return version


async def get_latest_version(session: AsyncSession) -> ConfigVersion | None:
    """Get the most recent committed version."""

    stmt = select(ConfigVersion).order_by(ConfigVersion.created_at.desc(), ConfigVersion.id.desc()).limit(1)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_version_by_hash(session: AsyncSession, version_hash: str) -> ConfigVersion | None:
    """Get a version by its hash."""

    stmt = select(ConfigVersion).where(ConfigVersion.hash == version_hash)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_versions(session: AsyncSession, *, limit: int = 50, offset: int = 0) -> list[ConfigVersion]:
    """List versions ordered by newest first."""

    stmt = select(ConfigVersion).order_by(ConfigVersion.created_at.desc(), ConfigVersion.id.desc()).limit(limit).offset(offset)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def count_versions(session: AsyncSession) -> int:
    """Count total number of versions."""

    stmt = select(func.count(ConfigVersion.id))
    result = await session.execute(stmt)
    return result.scalar_one()
