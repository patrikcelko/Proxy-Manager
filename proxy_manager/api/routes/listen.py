"""
Listen block routes
===================
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.api.dependencies import DBSession
from proxy_manager.api.schemas.common import MessageResponse
from proxy_manager.api.schemas.listen import (
    ListenBlockBindCreate,
    ListenBlockBindResponse,
    ListenBlockBindUpdate,
    ListenBlockCreate,
    ListenBlockDetailResponse,
    ListenBlockListResponse,
    ListenBlockUpdate,
)
from proxy_manager.database.models.listen_block import (
    ListenBlock,
    create_listen_block,
    create_listen_block_bind,
    delete_listen_block,
    delete_listen_block_bind,
    get_listen_block,
    get_listen_block_bind,
    get_listen_block_by_name,
    list_listen_block_binds,
    list_listen_blocks,
    update_listen_block,
    update_listen_block_bind,
)

router = APIRouter(tags=["listen"])


async def _build_detail(session: AsyncSession, lb: ListenBlock) -> ListenBlockDetailResponse:
    """Build a detail response with all child relations loaded."""

    binds = await list_listen_block_binds(session, lb.id)
    return ListenBlockDetailResponse(
        id=lb.id,
        name=lb.name,
        mode=lb.mode,
        balance=lb.balance,
        maxconn=lb.maxconn,
        timeout_client=lb.timeout_client,
        timeout_server=lb.timeout_server,
        timeout_connect=lb.timeout_connect,
        default_server_params=lb.default_server_params,
        option_httplog=lb.option_httplog,
        option_tcplog=lb.option_tcplog,
        option_forwardfor=lb.option_forwardfor,
        content=lb.content,
        comment=lb.comment,
        sort_order=lb.sort_order,
        binds=[ListenBlockBindResponse.model_validate(b) for b in binds],
    )


@router.get("/api/listen-blocks", response_model=ListenBlockListResponse)
async def api_list_listen_blocks(session: DBSession) -> ListenBlockListResponse:
    """List all listen blocks with their binds."""

    rows = await list_listen_blocks(session)
    items = [await _build_detail(session, r) for r in rows]

    return ListenBlockListResponse(count=len(items), items=items)


@router.get("/api/listen-blocks/{block_id}", response_model=ListenBlockDetailResponse)
async def api_get_listen_block(block_id: int, session: DBSession) -> ListenBlockDetailResponse:
    """Get a single listen block by ID."""

    row = await get_listen_block(session, block_id)
    if not row:
        raise HTTPException(status_code=404, detail="Listen block not found")

    return await _build_detail(session, row)


@router.post("/api/listen-blocks", response_model=ListenBlockDetailResponse, status_code=201)
async def api_create_listen_block(body: ListenBlockCreate, session: DBSession) -> ListenBlockDetailResponse:
    """Create a new listen block."""

    existing = await get_listen_block_by_name(session, body.name)
    if existing:
        raise HTTPException(status_code=409, detail=f"Listen block '{body.name}' already exists")

    row = await create_listen_block(session, **body.model_dump())
    return await _build_detail(session, row)


@router.put("/api/listen-blocks/{block_id}", response_model=ListenBlockDetailResponse)
async def api_update_listen_block(
    block_id: int,
    body: ListenBlockUpdate,
    session: DBSession,
) -> ListenBlockDetailResponse:
    """Update an existing listen block."""

    row = await get_listen_block(session, block_id)
    if not row:
        raise HTTPException(status_code=404, detail="Listen block not found")

    data = {k: v for k, v in body.model_dump().items() if v is not None or k in body.model_fields_set}
    updated = await update_listen_block(session, row, **data)
    return await _build_detail(session, updated)


@router.delete("/api/listen-blocks/{block_id}", response_model=MessageResponse)
async def api_delete_listen_block(block_id: int, session: DBSession) -> MessageResponse:
    """Delete a listen block and its binds."""

    row = await get_listen_block(session, block_id)
    if not row:
        raise HTTPException(status_code=404, detail="Listen block not found")

    await delete_listen_block(session, row)
    return MessageResponse(detail=f"Listen block '{row.name}' deleted")


@router.post("/api/listen-blocks/{block_id}/binds", response_model=ListenBlockBindResponse, status_code=201)
async def api_create_listen_bind(
    block_id: int,
    body: ListenBlockBindCreate,
    session: DBSession,
) -> ListenBlockBindResponse:
    """Add a bind to a listen block."""

    lb = await get_listen_block(session, block_id)
    if not lb:
        raise HTTPException(status_code=404, detail="Listen block not found")

    bind = await create_listen_block_bind(
        session,
        listen_block_id=block_id,
        bind_line=body.bind_line,
        sort_order=body.sort_order,
    )
    return ListenBlockBindResponse.model_validate(bind)


@router.put("/api/listen-blocks/{block_id}/binds/{bind_id}", response_model=ListenBlockBindResponse)
async def api_update_listen_bind(
    block_id: int,
    bind_id: int,
    body: ListenBlockBindUpdate,
    session: DBSession,
) -> ListenBlockBindResponse:
    """Update a listen block bind."""

    bind = await get_listen_block_bind(session, bind_id)
    if not bind or bind.listen_block_id != block_id:
        raise HTTPException(status_code=404, detail="Bind not found")

    updated = await update_listen_block_bind(session, bind, bind_line=body.bind_line, sort_order=body.sort_order)
    return ListenBlockBindResponse.model_validate(updated)


@router.delete("/api/listen-blocks/{block_id}/binds/{bind_id}", response_model=MessageResponse)
async def api_delete_listen_bind(block_id: int, bind_id: int, session: DBSession) -> MessageResponse:
    """Remove a bind from a listen block."""

    bind = await get_listen_block_bind(session, bind_id)
    if not bind or bind.listen_block_id != block_id:
        raise HTTPException(status_code=404, detail="Bind not found")

    await delete_listen_block_bind(session, bind)
    return MessageResponse(detail="Bind deleted")
