"""
Backend routes
==============
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.api.dependencies import DBSession
from proxy_manager.api.schemas.backends import (
    BackendCreate,
    BackendDetailResponse,
    BackendListResponse,
    BackendServerCreate,
    BackendServerResponse,
    BackendServerUpdate,
    BackendUpdate,
)
from proxy_manager.api.schemas.common import MessageResponse
from proxy_manager.database.models.backend import (
    Backend,
    create_backend,
    create_backend_server,
    delete_backend,
    delete_backend_server,
    get_backend,
    get_backend_by_name,
    get_backend_server,
    list_backend_servers,
    list_backends,
    update_backend,
    update_backend_server,
)

router = APIRouter(tags=["backends"])


async def _build_detail(session: AsyncSession, be: Backend) -> BackendDetailResponse:
    """Build a detail response with all child relations loaded."""

    servers = await list_backend_servers(session, be.id)
    return BackendDetailResponse(
        id=be.id,
        name=be.name,
        mode=be.mode,
        balance=be.balance,
        option_forwardfor=be.option_forwardfor,
        option_redispatch=be.option_redispatch,
        retries=be.retries,
        retry_on=be.retry_on,
        auth_userlist=be.auth_userlist,
        health_check_enabled=be.health_check_enabled,
        health_check_method=be.health_check_method,
        health_check_uri=be.health_check_uri,
        errorfile=be.errorfile,
        comment=be.comment,
        extra_options=be.extra_options,
        cookie=be.cookie,
        timeout_server=be.timeout_server,
        timeout_connect=be.timeout_connect,
        timeout_queue=be.timeout_queue,
        http_check_expect=be.http_check_expect,
        default_server_options=be.default_server_options,
        http_reuse=be.http_reuse,
        hash_type=be.hash_type,
        option_httplog=be.option_httplog,
        option_tcplog=be.option_tcplog,
        compression_algo=be.compression_algo,
        compression_type=be.compression_type,
        servers=[BackendServerResponse.model_validate(s) for s in servers],
    )


@router.get("/api/backends", response_model=BackendListResponse)
async def api_list_backends(session: DBSession) -> BackendListResponse:
    """List all backends with their servers."""

    rows = await list_backends(session)
    items = [await _build_detail(session, r) for r in rows]

    return BackendListResponse(count=len(items), items=items)


@router.get("/api/backends/{backend_id}", response_model=BackendDetailResponse)
async def api_get_backend(backend_id: int, session: DBSession) -> BackendDetailResponse:
    """Get a single backend by ID with servers."""

    be = await get_backend(session, backend_id)
    if not be:
        raise HTTPException(status_code=404, detail="Backend not found")

    return await _build_detail(session, be)


@router.post("/api/backends", response_model=BackendDetailResponse, status_code=201)
async def api_create_backend(body: BackendCreate, session: DBSession) -> BackendDetailResponse:
    """Create a new backend."""

    existing = await get_backend_by_name(session, body.name)
    if existing:
        raise HTTPException(status_code=409, detail=f"Backend '{body.name}' already exists")

    row = await create_backend(session, **body.model_dump())
    return await _build_detail(session, row)


@router.put("/api/backends/{backend_id}", response_model=BackendDetailResponse)
async def api_update_backend(backend_id: int, body: BackendUpdate, session: DBSession) -> BackendDetailResponse:
    """Update an existing backend."""

    be = await get_backend(session, backend_id)
    if not be:
        raise HTTPException(status_code=404, detail="Backend not found")

    if body.name is not None and body.name != be.name:
        existing = await get_backend_by_name(session, body.name)
        if existing:
            raise HTTPException(status_code=409, detail=f"Backend '{body.name}' already exists")

    data = {k: v for k, v in body.model_dump().items() if v is not None or k in body.model_fields_set}
    updated = await update_backend(session, be, **data)

    return await _build_detail(session, updated)


@router.delete("/api/backends/{backend_id}", response_model=MessageResponse)
async def api_delete_backend(backend_id: int, session: DBSession) -> MessageResponse:
    """Delete a backend and its servers."""

    be = await get_backend(session, backend_id)

    if not be:
        raise HTTPException(status_code=404, detail="Backend not found")
    await delete_backend(session, be)

    return MessageResponse(detail=f"Backend '{be.name}' deleted")


@router.post("/api/backends/{backend_id}/servers", response_model=BackendServerResponse, status_code=201)
async def api_create_server(backend_id: int, body: BackendServerCreate, session: DBSession) -> BackendServerResponse:
    """Add a server to a backend."""

    be = await get_backend(session, backend_id)
    if not be:
        raise HTTPException(status_code=404, detail="Backend not found")

    srv = await create_backend_server(session, backend_id=backend_id, **body.model_dump())
    return BackendServerResponse.model_validate(srv)


@router.put("/api/backends/{backend_id}/servers/{server_id}", response_model=BackendServerResponse)
async def api_update_server(backend_id: int, server_id: int, body: BackendServerUpdate, session: DBSession) -> BackendServerResponse:
    """Update a backend server."""

    srv = await get_backend_server(session, server_id)
    if not srv or srv.backend_id != backend_id:
        raise HTTPException(status_code=404, detail="Server not found")

    data = {k: v for k, v in body.model_dump().items() if v is not None or k in body.model_fields_set}
    updated = await update_backend_server(session, srv, **data)

    return BackendServerResponse.model_validate(updated)


@router.delete("/api/backends/{backend_id}/servers/{server_id}", response_model=MessageResponse)
async def api_delete_server(backend_id: int, server_id: int, session: DBSession) -> MessageResponse:
    """Remove a server from a backend."""

    srv = await get_backend_server(session, server_id)
    if not srv or srv.backend_id != backend_id:
        raise HTTPException(status_code=404, detail="Server not found")

    await delete_backend_server(session, srv)
    return MessageResponse(detail="Server deleted")
