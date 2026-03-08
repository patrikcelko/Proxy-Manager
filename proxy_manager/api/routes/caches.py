"""
Cache routes
============
"""

from fastapi import APIRouter, HTTPException

from proxy_manager.api.dependencies import DBSession
from proxy_manager.api.schemas.caches import (
    CacheSectionCreate,
    CacheSectionListResponse,
    CacheSectionResponse,
    CacheSectionUpdate,
)
from proxy_manager.api.schemas.common import MessageResponse
from proxy_manager.database.models.cache import (
    create_cache_section,
    delete_cache_section,
    get_cache_section,
    get_cache_section_by_name,
    list_cache_sections,
    update_cache_section,
)

router = APIRouter(tags=["cache"])


@router.get("/api/caches", response_model=CacheSectionListResponse)
async def api_list_caches(session: DBSession) -> CacheSectionListResponse:
    """List all cache sections."""

    items = await list_cache_sections(session)
    return CacheSectionListResponse(
        count=len(items),
        items=[CacheSectionResponse.model_validate(c) for c in items],
    )


@router.get("/api/caches/{cache_id}", response_model=CacheSectionResponse)
async def api_get_cache(cache_id: int, session: DBSession) -> CacheSectionResponse:
    """Get a single cache section by ID."""

    c = await get_cache_section(session, cache_id)
    if not c:
        raise HTTPException(status_code=404, detail="Cache section not found")

    return CacheSectionResponse.model_validate(c)


@router.post("/api/caches", response_model=CacheSectionResponse, status_code=201)
async def api_create_cache(body: CacheSectionCreate, session: DBSession) -> CacheSectionResponse:
    """Create a new cache section."""

    existing = await get_cache_section_by_name(session, body.name)
    if existing:
        raise HTTPException(status_code=409, detail=f"Cache section '{body.name}' already exists")

    c = await create_cache_section(session, **body.model_dump(exclude_unset=True))
    return CacheSectionResponse.model_validate(c)


@router.put("/api/caches/{cache_id}", response_model=CacheSectionResponse)
async def api_update_cache(cache_id: int, body: CacheSectionUpdate, session: DBSession) -> CacheSectionResponse:
    """Update an existing cache section."""

    c = await get_cache_section(session, cache_id)
    if not c:
        raise HTTPException(status_code=404, detail="Cache section not found")

    if body.name is not None and body.name != c.name:
        conflict = await get_cache_section_by_name(session, body.name)
        if conflict:
            raise HTTPException(status_code=409, detail=f"Cache section '{body.name}' already exists")

    c = await update_cache_section(session, c, **body.model_dump(exclude_unset=True))
    return CacheSectionResponse.model_validate(c)


@router.delete("/api/caches/{cache_id}", response_model=MessageResponse)
async def api_delete_cache(cache_id: int, session: DBSession) -> MessageResponse:
    """Delete a cache section."""

    c = await get_cache_section(session, cache_id)
    if not c:
        raise HTTPException(status_code=404, detail="Cache section not found")

    await delete_cache_section(session, c)
    return MessageResponse(detail="Cache section deleted")
