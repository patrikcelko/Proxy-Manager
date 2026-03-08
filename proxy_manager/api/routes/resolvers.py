"""
Resolver routes
===============
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.api.dependencies import DBSession
from proxy_manager.api.schemas.common import MessageResponse
from proxy_manager.api.schemas.resolvers import (
    ResolverCreate,
    ResolverDetailResponse,
    ResolverListResponse,
    ResolverNameserverCreate,
    ResolverNameserverResponse,
    ResolverNameserverUpdate,
    ResolverUpdate,
)
from proxy_manager.database.models.resolver import (
    Resolver,
    create_resolver,
    create_resolver_nameserver,
    delete_resolver,
    delete_resolver_nameserver,
    get_resolver,
    get_resolver_by_name,
    get_resolver_nameserver,
    list_resolver_nameservers,
    list_resolvers,
    update_resolver,
    update_resolver_nameserver,
)

router = APIRouter(tags=["resolvers"])


async def _build_detail(session: AsyncSession, r: Resolver) -> ResolverDetailResponse:
    """Build a detail response with all child relations loaded."""

    ns = await list_resolver_nameservers(session, r.id)
    return ResolverDetailResponse(
        id=r.id,
        name=r.name,
        resolve_retries=r.resolve_retries,
        timeout_resolve=r.timeout_resolve,
        timeout_retry=r.timeout_retry,
        hold_valid=r.hold_valid,
        hold_other=r.hold_other,
        hold_refused=r.hold_refused,
        hold_timeout=r.hold_timeout,
        hold_obsolete=r.hold_obsolete,
        hold_nx=r.hold_nx,
        hold_aa=r.hold_aa,
        accepted_payload_size=r.accepted_payload_size,
        parse_resolv_conf=r.parse_resolv_conf,
        comment=r.comment,
        extra_options=r.extra_options,
        nameservers=[ResolverNameserverResponse.model_validate(n) for n in ns],
    )


@router.get("/api/resolvers", response_model=ResolverListResponse)
async def api_list_resolvers(session: DBSession) -> ResolverListResponse:
    """List all resolvers with nameservers."""

    items = await list_resolvers(session)
    result = [await _build_detail(session, r) for r in items]
    return ResolverListResponse(count=len(result), items=result)


@router.get("/api/resolvers/{resolver_id}", response_model=ResolverDetailResponse)
async def api_get_resolver(resolver_id: int, session: DBSession) -> ResolverDetailResponse:
    """Get a single resolver by ID."""

    r = await get_resolver(session, resolver_id)
    if not r:
        raise HTTPException(status_code=404, detail="Resolver not found")

    return await _build_detail(session, r)


@router.post("/api/resolvers", response_model=ResolverDetailResponse, status_code=201)
async def api_create_resolver(body: ResolverCreate, session: DBSession) -> ResolverDetailResponse:
    """Create a new resolver."""

    existing = await get_resolver_by_name(session, body.name)
    if existing:
        raise HTTPException(status_code=409, detail=f"Resolver '{body.name}' already exists")

    r = await create_resolver(session, **body.model_dump(exclude_unset=True))
    return await _build_detail(session, r)


@router.put("/api/resolvers/{resolver_id}", response_model=ResolverDetailResponse)
async def api_update_resolver(resolver_id: int, body: ResolverUpdate, session: DBSession) -> ResolverDetailResponse:
    """Update an existing resolver."""

    r = await get_resolver(session, resolver_id)
    if not r:
        raise HTTPException(status_code=404, detail="Resolver not found")

    if body.name is not None and body.name != r.name:
        conflict = await get_resolver_by_name(session, body.name)
        if conflict:
            raise HTTPException(status_code=409, detail=f"Resolver '{body.name}' already exists")

    r = await update_resolver(session, r, **body.model_dump(exclude_unset=True))
    return await _build_detail(session, r)


@router.delete("/api/resolvers/{resolver_id}", response_model=MessageResponse)
async def api_delete_resolver(resolver_id: int, session: DBSession) -> MessageResponse:
    """Delete a resolver and its nameservers."""

    r = await get_resolver(session, resolver_id)
    if not r:
        raise HTTPException(status_code=404, detail="Resolver not found")

    await delete_resolver(session, r)
    return MessageResponse(detail="Resolver deleted")


@router.post("/api/resolvers/{resolver_id}/nameservers", response_model=ResolverNameserverResponse, status_code=201)
async def api_add_nameserver(
    resolver_id: int,
    body: ResolverNameserverCreate,
    session: DBSession,
) -> ResolverNameserverResponse:
    """Add a nameserver to a resolver section."""

    r = await get_resolver(session, resolver_id)
    if not r:
        raise HTTPException(status_code=404, detail="Resolver not found")

    ns = await create_resolver_nameserver(session, resolver_id=resolver_id, **body.model_dump(exclude_unset=True))
    return ResolverNameserverResponse.model_validate(ns)


@router.put("/api/resolvers/{resolver_id}/nameservers/{ns_id}", response_model=ResolverNameserverResponse)
async def api_update_nameserver(
    resolver_id: int,
    ns_id: int,
    body: ResolverNameserverUpdate,
    session: DBSession,
) -> ResolverNameserverResponse:
    """Update a resolver nameserver."""

    ns = await get_resolver_nameserver(session, ns_id)
    if not ns or ns.resolver_id != resolver_id:
        raise HTTPException(status_code=404, detail="Nameserver not found")

    ns = await update_resolver_nameserver(session, ns, **body.model_dump(exclude_unset=True))
    return ResolverNameserverResponse.model_validate(ns)


@router.delete("/api/resolvers/{resolver_id}/nameservers/{ns_id}", response_model=MessageResponse)
async def api_delete_nameserver(resolver_id: int, ns_id: int, session: DBSession) -> MessageResponse:
    """Remove a nameserver from a resolver."""

    ns = await get_resolver_nameserver(session, ns_id)
    if not ns or ns.resolver_id != resolver_id:
        raise HTTPException(status_code=404, detail="Nameserver not found")

    await delete_resolver_nameserver(session, ns)
    return MessageResponse(detail="Nameserver deleted")
