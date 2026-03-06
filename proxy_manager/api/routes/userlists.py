"""
Userlists routes
================
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.api.dependencies import DBSession
from proxy_manager.api.schemas.common import MessageResponse
from proxy_manager.api.schemas.userlists import (
    UserlistCreate,
    UserlistDetailResponse,
    UserlistEntryCreate,
    UserlistEntryResponse,
    UserlistEntryUpdate,
    UserlistListResponse,
    UserlistUpdate,
)
from proxy_manager.database.models.userlist import (
    Userlist,
    UserlistEntry,
    create_userlist,
    create_userlist_entry,
    delete_userlist,
    delete_userlist_entry,
    get_userlist,
    get_userlist_by_name,
    get_userlist_entry,
    list_userlist_entries,
    list_userlists,
    update_userlist,
    update_userlist_entry,
)
from proxy_manager.utilities.auth import hash_password

router = APIRouter(tags=["userlists"])


def _entry_response(e: UserlistEntry) -> UserlistEntryResponse:
    """Build entry response with has_password flag, never exposing hash."""

    return UserlistEntryResponse(
        id=e.id,
        userlist_id=e.userlist_id,
        username=e.username,
        has_password=bool(e.password_hash),
        sort_order=e.sort_order,
    )


async def _build_detail(session: AsyncSession, ul: Userlist) -> UserlistDetailResponse:
    """Build a detail response with all child relations loaded."""

    entries = await list_userlist_entries(session, ul.id)
    return UserlistDetailResponse(
        id=ul.id,
        name=ul.name,
        entries=[_entry_response(e) for e in entries],
    )


@router.get("/api/userlists", response_model=UserlistListResponse)
async def api_list_userlists(session: DBSession) -> UserlistListResponse:
    """List all userlists with their entries."""

    rows = await list_userlists(session)
    items = [await _build_detail(session, r) for r in rows]
    return UserlistListResponse(count=len(items), items=items)


@router.get("/api/userlists/{userlist_id}", response_model=UserlistDetailResponse)
async def api_get_userlist(userlist_id: int, session: DBSession) -> UserlistDetailResponse:
    """Get a single userlist by ID."""

    ul = await get_userlist(session, userlist_id)
    if not ul:
        raise HTTPException(status_code=404, detail="Userlist not found")

    return await _build_detail(session, ul)


@router.post("/api/userlists", response_model=UserlistDetailResponse, status_code=201)
async def api_create_userlist(body: UserlistCreate, session: DBSession) -> UserlistDetailResponse:
    """Create a new userlist."""

    existing = await get_userlist_by_name(session, body.name)
    if existing:
        raise HTTPException(status_code=409, detail=f"Userlist '{body.name}' already exists")

    row = await create_userlist(session, name=body.name)
    return await _build_detail(session, row)


@router.put("/api/userlists/{userlist_id}", response_model=UserlistDetailResponse)
async def api_update_userlist(userlist_id: int, body: UserlistUpdate, session: DBSession) -> UserlistDetailResponse:
    """Update an existing userlist."""

    ul = await get_userlist(session, userlist_id)
    if not ul:
        raise HTTPException(status_code=404, detail="Userlist not found")

    updated = await update_userlist(session, ul, name=body.name)
    return await _build_detail(session, updated)


@router.delete("/api/userlists/{userlist_id}", response_model=MessageResponse)
async def api_delete_userlist(userlist_id: int, session: DBSession) -> MessageResponse:
    """Delete a userlist and its entries."""

    ul = await get_userlist(session, userlist_id)
    if not ul:
        raise HTTPException(status_code=404, detail="Userlist not found")

    await delete_userlist(session, ul)
    return MessageResponse(detail=f"Userlist '{ul.name}' deleted")


@router.post("/api/userlists/{userlist_id}/entries", response_model=UserlistEntryResponse, status_code=201)
async def api_create_entry(userlist_id: int, body: UserlistEntryCreate, session: DBSession) -> UserlistEntryResponse:
    """Add an entry to a userlist."""

    ul = await get_userlist(session, userlist_id)
    if not ul:
        raise HTTPException(status_code=404, detail="Userlist not found")

    hashed = hash_password(body.password)
    entry = await create_userlist_entry(
        session,
        userlist_id=userlist_id,
        username=body.username,
        password_hash=hashed,
        sort_order=body.sort_order,
    )

    return _entry_response(entry)


@router.put("/api/userlists/{userlist_id}/entries/{entry_id}", response_model=UserlistEntryResponse)
async def api_update_entry(userlist_id: int, entry_id: int, body: UserlistEntryUpdate, session: DBSession) -> UserlistEntryResponse:
    """Update a userlist entry password or name."""

    entry = await get_userlist_entry(session, entry_id)
    if not entry or entry.userlist_id != userlist_id:
        raise HTTPException(status_code=404, detail="Entry not found")

    pw_hash = hash_password(body.password) if body.password else None
    updated = await update_userlist_entry(
        session,
        entry,
        username=body.username,
        password_hash=pw_hash,
        sort_order=body.sort_order,
    )

    return _entry_response(updated)


@router.delete("/api/userlists/{userlist_id}/entries/{entry_id}", response_model=MessageResponse)
async def api_delete_entry(userlist_id: int, entry_id: int, session: DBSession) -> MessageResponse:
    """Delete a userlist entry."""

    entry = await get_userlist_entry(session, entry_id)
    if not entry or entry.userlist_id != userlist_id:
        raise HTTPException(status_code=404, detail="Entry not found")

    await delete_userlist_entry(session, entry)
    return MessageResponse(detail="Entry deleted")
