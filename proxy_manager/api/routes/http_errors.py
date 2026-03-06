"""
HTTP Errors routes
==================
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.api.dependencies import DBSession
from proxy_manager.api.schemas.common import MessageResponse
from proxy_manager.api.schemas.http_errors import (
    HttpErrorEntryCreate,
    HttpErrorEntryResponse,
    HttpErrorEntryUpdate,
    HttpErrorsSectionCreate,
    HttpErrorsSectionDetailResponse,
    HttpErrorsSectionListResponse,
    HttpErrorsSectionUpdate,
)
from proxy_manager.database.models.http_errors import (
    HttpErrorsSection,
    create_http_error_entry,
    create_http_errors_section,
    delete_http_error_entry,
    delete_http_errors_section,
    get_http_error_entry,
    get_http_errors_section,
    get_http_errors_section_by_name,
    list_http_error_entries,
    list_http_errors_sections,
    update_http_error_entry,
    update_http_errors_section,
)

router = APIRouter(tags=["http-errors"])


async def _build_detail(session: AsyncSession, s: HttpErrorsSection) -> HttpErrorsSectionDetailResponse:
    """Build a detail response with all child relations loaded."""

    entries = await list_http_error_entries(session, s.id)
    return HttpErrorsSectionDetailResponse(
        id=s.id,
        name=s.name,
        comment=s.comment,
        extra_options=s.extra_options,
        entries=[HttpErrorEntryResponse.model_validate(e) for e in entries],
    )


@router.get("/api/http-errors", response_model=HttpErrorsSectionListResponse)
async def api_list_http_errors(session: DBSession) -> HttpErrorsSectionListResponse:
    """List all HTTP error sections."""

    items = await list_http_errors_sections(session)
    result = [await _build_detail(session, s) for s in items]

    return HttpErrorsSectionListResponse(count=len(result), items=result)


@router.get("/api/http-errors/{section_id}", response_model=HttpErrorsSectionDetailResponse)
async def api_get_http_errors(section_id: int, session: DBSession) -> HttpErrorsSectionDetailResponse:
    """Retrieve a single HTTP errors section by ID."""

    s = await get_http_errors_section(session, section_id)
    if not s:
        raise HTTPException(status_code=404, detail="HTTP errors section not found")

    return await _build_detail(session, s)


@router.post("/api/http-errors", response_model=HttpErrorsSectionDetailResponse, status_code=201)
async def api_create_http_errors(body: HttpErrorsSectionCreate, session: DBSession) -> HttpErrorsSectionDetailResponse:
    """Create a new HTTP errors section."""

    existing = await get_http_errors_section_by_name(session, body.name)
    if existing:
        raise HTTPException(status_code=409, detail=f"HTTP errors section '{body.name}' already exists")

    s = await create_http_errors_section(session, **body.model_dump(exclude_unset=True))
    return await _build_detail(session, s)


@router.put("/api/http-errors/{section_id}", response_model=HttpErrorsSectionDetailResponse)
async def api_update_http_errors(
    section_id: int,
    body: HttpErrorsSectionUpdate,
    session: DBSession,
) -> HttpErrorsSectionDetailResponse:
    """Update an existing HTTP errors section."""

    s = await get_http_errors_section(session, section_id)
    if not s:
        raise HTTPException(status_code=404, detail="HTTP errors section not found")

    s = await update_http_errors_section(session, s, **body.model_dump(exclude_unset=True))
    return await _build_detail(session, s)


@router.delete("/api/http-errors/{section_id}", response_model=MessageResponse)
async def api_delete_http_errors(section_id: int, session: DBSession) -> MessageResponse:
    """Delete an HTTP errors section."""

    s = await get_http_errors_section(session, section_id)
    if not s:
        raise HTTPException(status_code=404, detail="HTTP errors section not found")

    await delete_http_errors_section(session, s)
    return MessageResponse(detail="HTTP errors section deleted")


@router.post("/api/http-errors/{section_id}/entries", response_model=HttpErrorEntryResponse, status_code=201)
async def api_add_http_error_entry(
    section_id: int,
    body: HttpErrorEntryCreate,
    session: DBSession,
) -> HttpErrorEntryResponse:
    """Add an error entry to an HTTP errors section."""

    s = await get_http_errors_section(session, section_id)
    if not s:
        raise HTTPException(status_code=404, detail="HTTP errors section not found")

    e = await create_http_error_entry(session, section_id=section_id, **body.model_dump(exclude_unset=True))
    return HttpErrorEntryResponse.model_validate(e)


@router.put("/api/http-errors/{section_id}/entries/{entry_id}", response_model=HttpErrorEntryResponse)
async def api_update_http_error_entry(
    section_id: int,
    entry_id: int,
    body: HttpErrorEntryUpdate,
    session: DBSession,
) -> HttpErrorEntryResponse:
    """Update an http-error entry."""

    e = await get_http_error_entry(session, entry_id)
    if not e or e.section_id != section_id:
        raise HTTPException(status_code=404, detail="Error entry not found")

    e = await update_http_error_entry(session, e, **body.model_dump(exclude_unset=True))
    return HttpErrorEntryResponse.model_validate(e)


@router.delete("/api/http-errors/{section_id}/entries/{entry_id}", response_model=MessageResponse)
async def api_delete_http_error_entry(section_id: int, entry_id: int, session: DBSession) -> MessageResponse:
    """Remove an http-error entry from a section."""

    e = await get_http_error_entry(session, entry_id)
    if not e or e.section_id != section_id:
        raise HTTPException(status_code=404, detail="Error entry not found")

    await delete_http_error_entry(session, e)
    return MessageResponse(detail="Error entry deleted")
