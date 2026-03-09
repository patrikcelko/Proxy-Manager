"""
Mailers routes
==============
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.api.dependencies import DBSession
from proxy_manager.api.schemas.common import MessageResponse
from proxy_manager.api.schemas.mailers import (
    MailerEntryCreate,
    MailerEntryResponse,
    MailerEntryUpdate,
    MailerSectionCreate,
    MailerSectionDetailResponse,
    MailerSectionListResponse,
    MailerSectionUpdate,
)
from proxy_manager.database.models.mailer import (
    MailerSection,
    create_mailer_entry,
    create_mailer_section,
    delete_mailer_entry,
    delete_mailer_section,
    get_mailer_entry,
    get_mailer_section,
    get_mailer_section_by_name,
    list_mailer_entries,
    list_mailer_sections,
    update_mailer_entry,
    update_mailer_section,
)

router = APIRouter(tags=['mailers'])


async def _build_detail(session: AsyncSession, m: MailerSection) -> MailerSectionDetailResponse:
    """Build a detail response with all child relations loaded."""

    entries = await list_mailer_entries(session, m.id)
    return MailerSectionDetailResponse(
        id=m.id,
        name=m.name,
        timeout_mail=m.timeout_mail,
        comment=m.comment,
        extra_options=m.extra_options,
        entries=[MailerEntryResponse.model_validate(e) for e in entries],
    )


@router.get('/api/mailers', response_model=MailerSectionListResponse)
async def api_list_mailers(session: DBSession) -> MailerSectionListResponse:
    """List all mailer sections."""

    items = await list_mailer_sections(session)
    result = [await _build_detail(session, m) for m in items]

    return MailerSectionListResponse(count=len(result), items=result)


@router.get('/api/mailers/{mailer_id}', response_model=MailerSectionDetailResponse)
async def api_get_mailer(mailer_id: int, session: DBSession) -> MailerSectionDetailResponse:
    """Retrieve a single mailer section by ID."""

    m = await get_mailer_section(session, mailer_id)
    if not m:
        raise HTTPException(status_code=404, detail='Mailer section not found')

    return await _build_detail(session, m)


@router.post('/api/mailers', response_model=MailerSectionDetailResponse, status_code=201)
async def api_create_mailer(body: MailerSectionCreate, session: DBSession) -> MailerSectionDetailResponse:
    """Create a new mailer section."""

    existing = await get_mailer_section_by_name(session, body.name)
    if existing:
        raise HTTPException(status_code=409, detail=f"Mailer section '{body.name}' already exists")

    m = await create_mailer_section(session, **body.model_dump(exclude_unset=True))
    return await _build_detail(session, m)


@router.put('/api/mailers/{mailer_id}', response_model=MailerSectionDetailResponse)
async def api_update_mailer(
    mailer_id: int,
    body: MailerSectionUpdate,
    session: DBSession,
) -> MailerSectionDetailResponse:
    """Update an existing mailer section."""

    m = await get_mailer_section(session, mailer_id)
    if not m:
        raise HTTPException(status_code=404, detail='Mailer section not found')

    if body.name is not None and body.name != m.name:
        conflict = await get_mailer_section_by_name(session, body.name)
        if conflict:
            raise HTTPException(status_code=409, detail=f"Mailer section '{body.name}' already exists")

    m = await update_mailer_section(session, m, **body.model_dump(exclude_unset=True))
    return await _build_detail(session, m)


@router.delete('/api/mailers/{mailer_id}', response_model=MessageResponse)
async def api_delete_mailer(mailer_id: int, session: DBSession) -> MessageResponse:
    """Delete a mailer section."""

    m = await get_mailer_section(session, mailer_id)
    if not m:
        raise HTTPException(status_code=404, detail='Mailer section not found')

    await delete_mailer_section(session, m)
    return MessageResponse(detail='Mailer section deleted')


@router.post('/api/mailers/{mailer_id}/entries', response_model=MailerEntryResponse, status_code=201)
async def api_add_mailer_entry(mailer_id: int, body: MailerEntryCreate, session: DBSession) -> MailerEntryResponse:
    """Add an entry to a mailer section."""

    m = await get_mailer_section(session, mailer_id)
    if not m:
        raise HTTPException(status_code=404, detail='Mailer section not found')

    e = await create_mailer_entry(session, mailer_section_id=mailer_id, **body.model_dump(exclude_unset=True))
    return MailerEntryResponse.model_validate(e)


@router.put('/api/mailers/{mailer_id}/entries/{entry_id}', response_model=MailerEntryResponse)
async def api_update_mailer_entry(
    mailer_id: int,
    entry_id: int,
    body: MailerEntryUpdate,
    session: DBSession,
) -> MailerEntryResponse:
    """Update a mailer entry."""

    e = await get_mailer_entry(session, entry_id)
    if not e or e.mailer_section_id != mailer_id:
        raise HTTPException(status_code=404, detail='Mailer entry not found')

    e = await update_mailer_entry(session, e, **body.model_dump(exclude_unset=True))
    return MailerEntryResponse.model_validate(e)


@router.delete('/api/mailers/{mailer_id}/entries/{entry_id}', response_model=MessageResponse)
async def api_delete_mailer_entry(mailer_id: int, entry_id: int, session: DBSession) -> MessageResponse:
    """Remove a mailer entry from a section."""

    e = await get_mailer_entry(session, entry_id)
    if not e or e.mailer_section_id != mailer_id:
        raise HTTPException(status_code=404, detail='Mailer entry not found')

    await delete_mailer_entry(session, e)
    return MessageResponse(detail='Mailer entry deleted')
