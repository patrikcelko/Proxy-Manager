"""
Version management routes
==========================

Endpoints for configuration version control: initialization,
save/discard, history, rollback, and pending change tracking.
"""

import json
from typing import Any

from fastapi import APIRouter, HTTPException

from proxy_manager.api.dependencies import CurrentUser, DBSession
from proxy_manager.api.schemas.common import MessageResponse
from proxy_manager.api.schemas.versions import (
    PendingChangesResponse,
    SectionRevertRequest,
    VersionDetail,
    VersionInitImportRequest,
    VersionListResponse,
    VersionSaveRequest,
    VersionStatusResponse,
    VersionSummary,
)
from proxy_manager.config_parser.parser import parse_config
from proxy_manager.config_parser.snapshot import (
    SECTION_SIDEBAR_MAP,
    compute_diff,
    compute_pending_counts,
    restore_snapshot,
    take_snapshot,
)
from proxy_manager.database.models.config_version import (
    count_versions,
    create_version,
    get_latest_version,
    get_version_by_hash,
    list_versions,
)

router = APIRouter(tags=["versions"])


@router.get("/api/versions/status", response_model=VersionStatusResponse)
async def api_version_status(session: DBSession) -> VersionStatusResponse:
    """Check initialization status and pending change summary."""

    latest = await get_latest_version(session)

    if latest is None:
        return VersionStatusResponse(initialized=False, has_pending=False, pending_counts={}, current_hash=None)

    committed_snapshot = json.loads(latest.snapshot)
    current_snapshot = await take_snapshot(session)
    counts = compute_pending_counts(committed_snapshot, current_snapshot)
    has_pending = any(v > 0 for v in counts.values())

    return VersionStatusResponse(
        initialized=True,
        has_pending=has_pending,
        pending_counts=counts,
        current_hash=latest.hash,
        current_message=latest.message,
        current_user_name=latest.user_name,
        current_created_at=latest.created_at.isoformat() if latest.created_at else None,
    )


@router.post("/api/versions/init/empty", response_model=MessageResponse)
async def api_init_empty(session: DBSession, user: CurrentUser) -> MessageResponse:
    """Initialize with an empty configuration (first-time setup)."""

    existing = await get_latest_version(session)
    if existing is not None:
        raise HTTPException(status_code=409, detail="Already initialized")

    snapshot = await take_snapshot(session)
    await create_version(
        session,
        snapshot_data=snapshot,
        message="Initial configuration",
        user_id=user.id,
        user_name=user.name or user.email,
    )

    return MessageResponse(detail="Initialized with empty configuration")


@router.post("/api/versions/init/import", response_model=MessageResponse)
async def api_init_import(
    body: VersionInitImportRequest,
    session: DBSession,
    user: CurrentUser,
) -> MessageResponse:
    """Initialize by importing an HAProxy configuration (first-time setup)."""

    existing = await get_latest_version(session)
    if existing is not None:
        raise HTTPException(status_code=409, detail="Already initialized")

    try:
        parse_config(body.config_text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {e}") from e

    # Use the existing import logic from config_io
    from proxy_manager.api.routes.config_io import api_import_config
    from proxy_manager.api.schemas.config_io import ConfigImportRequest

    import_req = ConfigImportRequest(config_text=body.config_text, merge=False)
    await api_import_config(import_req, session)

    snapshot = await take_snapshot(session)
    await create_version(
        session,
        snapshot_data=snapshot,
        message="Imported configuration",
        user_id=user.id,
        user_name=user.name or user.email,
    )

    return MessageResponse(detail="Initialized with imported configuration")


@router.get("/api/versions/pending", response_model=PendingChangesResponse)
async def api_pending_changes(session: DBSession) -> PendingChangesResponse:
    """Get detailed pending changes compared to last committed version."""

    latest = await get_latest_version(session)
    if latest is None:
        return PendingChangesResponse(has_pending=False, pending_counts={}, sections={})

    committed_snapshot = json.loads(latest.snapshot)
    current_snapshot = await take_snapshot(session)
    counts = compute_pending_counts(committed_snapshot, current_snapshot)
    has_pending = any(v > 0 for v in counts.values())

    diff = compute_diff(committed_snapshot, current_snapshot) if has_pending else {}

    return PendingChangesResponse(
        has_pending=has_pending,
        pending_counts=counts,
        sections=diff,
    )


@router.post("/api/versions/save", response_model=VersionSummary)
async def api_save_version(
    body: VersionSaveRequest,
    session: DBSession,
    user: CurrentUser,
) -> VersionSummary:
    """Commit current state as a new version."""

    latest = await get_latest_version(session)
    if latest is None:
        raise HTTPException(status_code=409, detail="Not initialized. Use init endpoint first.")

    current_snapshot = await take_snapshot(session)
    parent_hash = latest.hash

    version = await create_version(
        session,
        snapshot_data=current_snapshot,
        message=body.message,
        user_id=user.id,
        user_name=user.name or user.email,
        parent_hash=parent_hash,
    )

    return VersionSummary(
        hash=version.hash,
        message=version.message,
        user_name=version.user_name,
        created_at=version.created_at.isoformat(),
        parent_hash=version.parent_hash,
    )


@router.post("/api/versions/discard", response_model=MessageResponse)
async def api_discard_changes(session: DBSession, _user: CurrentUser) -> MessageResponse:
    """Discard all pending changes by restoring the last committed version."""

    latest = await get_latest_version(session)
    if latest is None:
        raise HTTPException(status_code=409, detail="Not initialized")

    committed_snapshot = json.loads(latest.snapshot)
    await restore_snapshot(session, committed_snapshot)

    return MessageResponse(detail="All pending changes discarded")


@router.get("/api/versions", response_model=VersionListResponse)
async def api_list_versions(session: DBSession, limit: int = 50, offset: int = 0) -> VersionListResponse:
    """List committed versions (newest first)."""

    versions = await list_versions(session, limit=limit, offset=offset)
    total = await count_versions(session)

    return VersionListResponse(
        items=[
            VersionSummary(
                hash=v.hash,
                message=v.message,
                user_name=v.user_name,
                created_at=v.created_at.isoformat(),
                parent_hash=v.parent_hash,
            )
            for v in versions
        ],
        total=total,
    )


@router.get("/api/versions/{version_hash}", response_model=VersionDetail)
async def api_version_detail(version_hash: str, session: DBSession) -> VersionDetail:
    """Get version details including diff from parent."""

    version = await get_version_by_hash(session, version_hash)
    if version is None:
        raise HTTPException(status_code=404, detail="Version not found")

    version_snapshot = json.loads(version.snapshot)

    # Compute diff from parent
    diff: dict[str, Any] = {}
    if version.parent_hash:
        parent = await get_version_by_hash(session, version.parent_hash)
        if parent:
            parent_snapshot = json.loads(parent.snapshot)
            diff = compute_diff(parent_snapshot, version_snapshot)
    else:
        # First version: diff against empty snapshot
        empty: dict[str, list[Any]] = {k: [] for k in SECTION_SIDEBAR_MAP}
        diff = compute_diff(empty, version_snapshot)

    return VersionDetail(
        hash=version.hash,
        message=version.message,
        user_name=version.user_name,
        created_at=version.created_at.isoformat(),
        parent_hash=version.parent_hash,
        diff=diff,
    )


@router.post("/api/versions/{version_hash}/rollback", response_model=VersionSummary)
async def api_rollback_version(
    version_hash: str,
    session: DBSession,
    user: CurrentUser,
) -> VersionSummary:
    """Rollback to a specific version by restoring its snapshot and creating a new version."""

    target = await get_version_by_hash(session, version_hash)
    if target is None:
        raise HTTPException(status_code=404, detail="Version not found")

    latest = await get_latest_version(session)
    parent_hash = latest.hash if latest else None

    target_snapshot = json.loads(target.snapshot)
    await restore_snapshot(session, target_snapshot)

    # Create a new version recording the rollback
    fresh_snapshot = await take_snapshot(session)
    version = await create_version(
        session,
        snapshot_data=fresh_snapshot,
        message=f"Rollback to {target.hash[:8]}: {target.message}",
        user_id=user.id,
        user_name=user.name or user.email,
        parent_hash=parent_hash,
    )

    return VersionSummary(
        hash=version.hash,
        message=version.message,
        user_name=version.user_name,
        created_at=version.created_at.isoformat(),
        parent_hash=version.parent_hash,
    )


@router.post("/api/versions/revert-section", response_model=MessageResponse)
async def api_revert_section(body: SectionRevertRequest, session: DBSession, _user: CurrentUser) -> MessageResponse:
    """Revert a specific section to its last committed state."""

    if body.section not in SECTION_SIDEBAR_MAP:
        raise HTTPException(status_code=400, detail=f"Unknown section: {body.section}")

    latest = await get_latest_version(session)
    if latest is None:
        raise HTTPException(status_code=409, detail="Not initialized")

    committed_snapshot = json.loads(latest.snapshot)
    current_snapshot = await take_snapshot(session)

    # Build a hybrid snapshot: current state for all sections except the reverted one
    hybrid = dict(current_snapshot)
    hybrid[body.section] = committed_snapshot.get(body.section, [])

    await restore_snapshot(session, hybrid)

    return MessageResponse(detail=f"Section '{body.section}' reverted to last committed state")
