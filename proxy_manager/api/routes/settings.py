"""
Settings routes
===============
"""

from fastapi import APIRouter, HTTPException

from proxy_manager.api.dependencies import DBSession
from proxy_manager.api.schemas.common import MessageResponse
from proxy_manager.api.schemas.settings import (
    SettingCreate,
    SettingListResponse,
    SettingResponse,
    SettingUpdate,
)
from proxy_manager.database.models.default_setting import (
    create_default_setting,
    delete_default_setting,
    get_default_setting,
    list_default_settings,
    update_default_setting,
)
from proxy_manager.database.models.global_setting import (
    create_global_setting,
    delete_global_setting,
    get_global_setting,
    list_global_settings,
    update_global_setting,
)

router = APIRouter(tags=["settings"])


@router.get("/api/global-settings", response_model=SettingListResponse)
async def api_list_global_settings(session: DBSession) -> SettingListResponse:
    """List all global settings."""

    rows = await list_global_settings(session)
    return SettingListResponse(count=len(rows), items=[SettingResponse.model_validate(r) for r in rows])


@router.post("/api/global-settings", response_model=SettingResponse, status_code=201)
async def api_create_global_setting(body: SettingCreate, session: DBSession) -> SettingResponse:
    """Create a new global setting."""

    row = await create_global_setting(session, directive=body.directive, value=body.value, comment=body.comment, sort_order=body.sort_order)
    return SettingResponse.model_validate(row)


@router.put("/api/global-settings/{setting_id}", response_model=SettingResponse)
async def api_update_global_setting(setting_id: int, body: SettingUpdate, session: DBSession) -> SettingResponse:
    """Update a global setting."""

    row = await get_global_setting(session, setting_id)
    if not row:
        raise HTTPException(status_code=404, detail="Setting not found")

    updated = await update_global_setting(
        session,
        row,
        directive=body.directive,
        value=body.value,
        comment=body.comment,
        sort_order=body.sort_order,
    )
    return SettingResponse.model_validate(updated)


@router.delete("/api/global-settings/{setting_id}", response_model=MessageResponse)
async def api_delete_global_setting(setting_id: int, session: DBSession) -> MessageResponse:
    """Delete a global setting."""

    row = await get_global_setting(session, setting_id)
    if not row:
        raise HTTPException(status_code=404, detail="Setting not found")

    await delete_global_setting(session, row)
    return MessageResponse(detail="Setting deleted")


@router.get("/api/default-settings", response_model=SettingListResponse)
async def api_list_default_settings(session: DBSession) -> SettingListResponse:
    """List all default settings."""

    rows = await list_default_settings(session)
    return SettingListResponse(count=len(rows), items=[SettingResponse.model_validate(r) for r in rows])


@router.post("/api/default-settings", response_model=SettingResponse, status_code=201)
async def api_create_default_setting(body: SettingCreate, session: DBSession) -> SettingResponse:
    """Create a new default setting."""

    row = await create_default_setting(session, directive=body.directive, value=body.value, comment=body.comment, sort_order=body.sort_order)
    return SettingResponse.model_validate(row)


@router.put("/api/default-settings/{setting_id}", response_model=SettingResponse)
async def api_update_default_setting(setting_id: int, body: SettingUpdate, session: DBSession) -> SettingResponse:
    """Update a default setting."""

    row = await get_default_setting(session, setting_id)
    if not row:
        raise HTTPException(status_code=404, detail="Setting not found")

    updated = await update_default_setting(
        session,
        row,
        directive=body.directive,
        value=body.value,
        comment=body.comment,
        sort_order=body.sort_order,
    )
    return SettingResponse.model_validate(updated)


@router.delete("/api/default-settings/{setting_id}", response_model=MessageResponse)
async def api_delete_default_setting(setting_id: int, session: DBSession) -> MessageResponse:
    """Delete a default setting."""

    row = await get_default_setting(session, setting_id)
    if not row:
        raise HTTPException(status_code=404, detail="Setting not found")

    await delete_default_setting(session, row)
    return MessageResponse(detail="Setting deleted")
