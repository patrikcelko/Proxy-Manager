"""
Peers routes
============
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.api.dependencies import DBSession
from proxy_manager.api.schemas.common import MessageResponse
from proxy_manager.api.schemas.peers import (
    PeerEntryCreate,
    PeerEntryResponse,
    PeerEntryUpdate,
    PeerSectionCreate,
    PeerSectionDetailResponse,
    PeerSectionListResponse,
    PeerSectionUpdate,
)
from proxy_manager.database.models.peer import (
    PeerSection,
    create_peer_entry,
    create_peer_section,
    delete_peer_entry,
    delete_peer_section,
    get_peer_entry,
    get_peer_section,
    get_peer_section_by_name,
    list_peer_entries,
    list_peer_sections,
    update_peer_entry,
    update_peer_section,
)

router = APIRouter(tags=["peers"])


async def _build_detail(session: AsyncSession, p: PeerSection) -> PeerSectionDetailResponse:
    """Build a detail response with all child relations loaded."""

    entries = await list_peer_entries(session, p.id)
    return PeerSectionDetailResponse(
        id=p.id,
        name=p.name,
        comment=p.comment,
        extra_options=p.extra_options,
        default_bind=p.default_bind,
        default_server_options=p.default_server_options,
        entries=[PeerEntryResponse.model_validate(e) for e in entries],
    )


@router.get("/api/peers", response_model=PeerSectionListResponse)
async def api_list_peers(session: DBSession) -> PeerSectionListResponse:
    """List all peer sections."""

    items = await list_peer_sections(session)
    result = [await _build_detail(session, p) for p in items]

    return PeerSectionListResponse(count=len(result), items=result)


@router.get("/api/peers/{peer_id}", response_model=PeerSectionDetailResponse)
async def api_get_peer(peer_id: int, session: DBSession) -> PeerSectionDetailResponse:
    """Retrieve a single peer section by ID."""

    p = await get_peer_section(session, peer_id)
    if not p:
        raise HTTPException(status_code=404, detail="Peer section not found")

    return await _build_detail(session, p)


@router.post("/api/peers", response_model=PeerSectionDetailResponse, status_code=201)
async def api_create_peer(body: PeerSectionCreate, session: DBSession) -> PeerSectionDetailResponse:
    """Create a new peer section."""

    existing = await get_peer_section_by_name(session, body.name)
    if existing:
        raise HTTPException(status_code=409, detail=f"Peer section '{body.name}' already exists")

    p = await create_peer_section(session, **body.model_dump(exclude_unset=True))
    return await _build_detail(session, p)


@router.put("/api/peers/{peer_id}", response_model=PeerSectionDetailResponse)
async def api_update_peer(peer_id: int, body: PeerSectionUpdate, session: DBSession) -> PeerSectionDetailResponse:
    """Update an existing peer section."""

    p = await get_peer_section(session, peer_id)
    if not p:
        raise HTTPException(status_code=404, detail="Peer section not found")

    if body.name is not None and body.name != p.name:
        conflict = await get_peer_section_by_name(session, body.name)
        if conflict:
            raise HTTPException(status_code=409, detail=f"Peer section '{body.name}' already exists")

    p = await update_peer_section(session, p, **body.model_dump(exclude_unset=True))
    return await _build_detail(session, p)


@router.delete("/api/peers/{peer_id}", response_model=MessageResponse)
async def api_delete_peer(peer_id: int, session: DBSession) -> MessageResponse:
    """Delete a peer section."""

    p = await get_peer_section(session, peer_id)
    if not p:
        raise HTTPException(status_code=404, detail="Peer section not found")

    await delete_peer_section(session, p)
    return MessageResponse(detail="Peer section deleted")


@router.post("/api/peers/{peer_id}/entries", response_model=PeerEntryResponse, status_code=201)
async def api_add_peer_entry(peer_id: int, body: PeerEntryCreate, session: DBSession) -> PeerEntryResponse:
    """Add an entry to a peer section."""

    p = await get_peer_section(session, peer_id)
    if not p:
        raise HTTPException(status_code=404, detail="Peer section not found")

    e = await create_peer_entry(session, peer_section_id=peer_id, **body.model_dump(exclude_unset=True))
    return PeerEntryResponse.model_validate(e)


@router.put("/api/peers/{peer_id}/entries/{entry_id}", response_model=PeerEntryResponse)
async def api_update_peer_entry(
    peer_id: int,
    entry_id: int,
    body: PeerEntryUpdate,
    session: DBSession,
) -> PeerEntryResponse:
    """Update a peer entry."""

    e = await get_peer_entry(session, entry_id)
    if not e or e.peer_section_id != peer_id:
        raise HTTPException(status_code=404, detail="Peer entry not found")

    e = await update_peer_entry(session, e, **body.model_dump(exclude_unset=True))
    return PeerEntryResponse.model_validate(e)


@router.delete("/api/peers/{peer_id}/entries/{entry_id}", response_model=MessageResponse)
async def api_delete_peer_entry(peer_id: int, entry_id: int, session: DBSession) -> MessageResponse:
    """Remove a peer entry from a section."""

    e = await get_peer_entry(session, entry_id)
    if not e or e.peer_section_id != peer_id:
        raise HTTPException(status_code=404, detail="Peer entry not found")

    await delete_peer_entry(session, e)
    return MessageResponse(detail="Peer entry deleted")
