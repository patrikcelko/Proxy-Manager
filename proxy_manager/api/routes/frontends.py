"""
Frontend routes
===============
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.api.dependencies import DBSession
from proxy_manager.api.schemas.common import MessageResponse
from proxy_manager.api.schemas.frontends import (
    AclRuleCreate,
    AclRuleListResponse,
    AclRuleResponse,
    AclRuleUpdate,
    FrontendBindCreate,
    FrontendBindResponse,
    FrontendBindUpdate,
    FrontendCreate,
    FrontendDetailResponse,
    FrontendListResponse,
    FrontendOptionCreate,
    FrontendOptionResponse,
    FrontendOptionUpdate,
    FrontendUpdate,
)
from proxy_manager.database.models.acl_rule import (
    create_acl_rule,
    delete_acl_rule,
    get_acl_rule,
    list_acl_rules,
    list_all_acl_rules,
    update_acl_rule,
)
from proxy_manager.database.models.frontend import (
    Frontend,
    create_frontend,
    create_frontend_bind,
    create_frontend_option,
    delete_frontend,
    delete_frontend_bind,
    delete_frontend_option,
    get_frontend,
    get_frontend_bind,
    get_frontend_by_name,
    get_frontend_option,
    list_frontend_binds,
    list_frontend_options,
    list_frontends,
    update_frontend,
    update_frontend_bind,
    update_frontend_option,
)

router = APIRouter(tags=["frontends"])


async def _build_detail(session: AsyncSession, fe: Frontend) -> FrontendDetailResponse:
    """Build a detail response with all child relations loaded."""

    binds = await list_frontend_binds(session, fe.id)
    opts = await list_frontend_options(session, fe.id)
    return FrontendDetailResponse(
        id=fe.id,
        name=fe.name,
        default_backend=fe.default_backend,
        mode=fe.mode,
        comment=fe.comment,
        timeout_client=fe.timeout_client,
        timeout_http_request=fe.timeout_http_request,
        timeout_http_keep_alive=fe.timeout_http_keep_alive,
        maxconn=fe.maxconn,
        option_httplog=fe.option_httplog,
        option_tcplog=fe.option_tcplog,
        option_forwardfor=fe.option_forwardfor,
        compression_algo=fe.compression_algo,
        compression_type=fe.compression_type,
        binds=[FrontendBindResponse.model_validate(b) for b in binds],
        options=[FrontendOptionResponse.model_validate(o) for o in opts],
    )


@router.get("/api/frontends", response_model=FrontendListResponse)
async def api_list_frontends(session: DBSession) -> FrontendListResponse:
    """List all frontends with binds and options."""

    rows = await list_frontends(session)
    items = [await _build_detail(session, r) for r in rows]

    return FrontendListResponse(count=len(items), items=items)


@router.get("/api/frontends/{frontend_id}", response_model=FrontendDetailResponse)
async def api_get_frontend(frontend_id: int, session: DBSession) -> FrontendDetailResponse:
    """Get a single frontend by ID."""

    fe = await get_frontend(session, frontend_id)
    if not fe:
        raise HTTPException(status_code=404, detail="Frontend not found")

    return await _build_detail(session, fe)


@router.post("/api/frontends", response_model=FrontendDetailResponse, status_code=201)
async def api_create_frontend(body: FrontendCreate, session: DBSession) -> FrontendDetailResponse:
    """Create a new frontend."""

    existing = await get_frontend_by_name(session, body.name)
    if existing:
        raise HTTPException(status_code=409, detail=f"Frontend '{body.name}' already exists")

    row = await create_frontend(
        session,
        name=body.name,
        default_backend=body.default_backend,
        mode=body.mode,
        comment=body.comment,
        timeout_client=body.timeout_client,
        timeout_http_request=body.timeout_http_request,
        timeout_http_keep_alive=body.timeout_http_keep_alive,
        maxconn=body.maxconn,
        option_httplog=body.option_httplog,
        option_tcplog=body.option_tcplog,
        option_forwardfor=body.option_forwardfor,
        compression_algo=body.compression_algo,
        compression_type=body.compression_type,
    )
    return await _build_detail(session, row)


@router.put("/api/frontends/{frontend_id}", response_model=FrontendDetailResponse)
async def api_update_frontend(frontend_id: int, body: FrontendUpdate, session: DBSession) -> FrontendDetailResponse:
    """Update an existing frontend."""

    fe = await get_frontend(session, frontend_id)
    if not fe:
        raise HTTPException(status_code=404, detail="Frontend not found")

    if body.name is not None and body.name != fe.name:
        existing = await get_frontend_by_name(session, body.name)
        if existing:
            raise HTTPException(status_code=409, detail=f"Frontend '{body.name}' already exists")

    updated = await update_frontend(
        session,
        fe,
        name=body.name,
        default_backend=body.default_backend,
        mode=body.mode,
        comment=body.comment,
        timeout_client=body.timeout_client,
        timeout_http_request=body.timeout_http_request,
        timeout_http_keep_alive=body.timeout_http_keep_alive,
        maxconn=body.maxconn,
        option_httplog=body.option_httplog,
        option_tcplog=body.option_tcplog,
        option_forwardfor=body.option_forwardfor,
        compression_algo=body.compression_algo,
        compression_type=body.compression_type,
        fields_set=frozenset(body.model_fields_set),
    )
    return await _build_detail(session, updated)


@router.delete("/api/frontends/{frontend_id}", response_model=MessageResponse)
async def api_delete_frontend(frontend_id: int, session: DBSession) -> MessageResponse:
    """Delete a frontend and its binds/options."""

    fe = await get_frontend(session, frontend_id)
    if not fe:
        raise HTTPException(status_code=404, detail="Frontend not found")

    await delete_frontend(session, fe)
    return MessageResponse(detail=f"Frontend '{fe.name}' deleted")


@router.post("/api/frontends/{frontend_id}/binds", response_model=FrontendBindResponse, status_code=201)
async def api_create_bind(frontend_id: int, body: FrontendBindCreate, session: DBSession) -> FrontendBindResponse:
    """Add a bind directive to a frontend."""

    fe = await get_frontend(session, frontend_id)
    if not fe:
        raise HTTPException(status_code=404, detail="Frontend not found")

    bind = await create_frontend_bind(
        session,
        frontend_id=frontend_id,
        bind_line=body.bind_line,
        sort_order=body.sort_order,
    )

    return FrontendBindResponse.model_validate(bind)


@router.put("/api/frontends/{frontend_id}/binds/{bind_id}", response_model=FrontendBindResponse)
async def api_update_bind(
    frontend_id: int,
    bind_id: int,
    body: FrontendBindUpdate,
    session: DBSession,
) -> FrontendBindResponse:
    """Update a frontend bind directive."""

    bind = await get_frontend_bind(session, bind_id)
    if not bind or bind.frontend_id != frontend_id:
        raise HTTPException(status_code=404, detail="Bind not found")

    updated = await update_frontend_bind(session, bind, bind_line=body.bind_line, sort_order=body.sort_order)
    return FrontendBindResponse.model_validate(updated)


@router.delete("/api/frontends/{frontend_id}/binds/{bind_id}", response_model=MessageResponse)
async def api_delete_bind(frontend_id: int, bind_id: int, session: DBSession) -> MessageResponse:
    """Remove a bind directive from a frontend."""

    bind = await get_frontend_bind(session, bind_id)
    if not bind or bind.frontend_id != frontend_id:
        raise HTTPException(status_code=404, detail="Bind not found")

    await delete_frontend_bind(session, bind)
    return MessageResponse(detail="Bind deleted")


@router.post("/api/frontends/{frontend_id}/options", response_model=FrontendOptionResponse, status_code=201)
async def api_create_option(frontend_id: int, body: FrontendOptionCreate, session: DBSession) -> FrontendOptionResponse:
    """Add an option directive to a frontend."""

    fe = await get_frontend(session, frontend_id)
    if not fe:
        raise HTTPException(status_code=404, detail="Frontend not found")

    opt = await create_frontend_option(
        session,
        frontend_id=frontend_id,
        directive=body.directive,
        value=body.value,
        comment=body.comment,
        sort_order=body.sort_order,
    )
    return FrontendOptionResponse.model_validate(opt)


@router.put("/api/frontends/{frontend_id}/options/{option_id}", response_model=FrontendOptionResponse)
async def api_update_option(
    frontend_id: int,
    option_id: int,
    body: FrontendOptionUpdate,
    session: DBSession,
) -> FrontendOptionResponse:
    """Update a frontend option directive."""

    opt = await get_frontend_option(session, option_id)
    if not opt or opt.frontend_id != frontend_id:
        raise HTTPException(status_code=404, detail="Option not found")

    updated = await update_frontend_option(
        session,
        opt,
        directive=body.directive,
        value=body.value,
        comment=body.comment,
        sort_order=body.sort_order,
    )
    return FrontendOptionResponse.model_validate(updated)


@router.delete("/api/frontends/{frontend_id}/options/{option_id}", response_model=MessageResponse)
async def api_delete_option(frontend_id: int, option_id: int, session: DBSession) -> MessageResponse:
    """Remove an option directive from a frontend."""

    opt = await get_frontend_option(session, option_id)
    if not opt or opt.frontend_id != frontend_id:
        raise HTTPException(status_code=404, detail="Option not found")

    await delete_frontend_option(session, opt)
    return MessageResponse(detail="Option deleted")


@router.get("/api/acl-rules", response_model=AclRuleListResponse)
async def api_list_all_acl_rules(session: DBSession) -> AclRuleListResponse:
    """List all ACL rules across all frontends."""

    rows = await list_all_acl_rules(session)
    return AclRuleListResponse(count=len(rows), items=[AclRuleResponse.model_validate(r) for r in rows])


@router.get("/api/frontends/{frontend_id}/acl-rules", response_model=AclRuleListResponse)
async def api_list_acl_rules(frontend_id: int, session: DBSession) -> AclRuleListResponse:
    """List ACL rules for a specific frontend."""

    fe = await get_frontend(session, frontend_id)
    if not fe:
        raise HTTPException(status_code=404, detail="Frontend not found")

    rows = await list_acl_rules(session, frontend_id)
    return AclRuleListResponse(count=len(rows), items=[AclRuleResponse.model_validate(r) for r in rows])


@router.post("/api/acl-rules", response_model=AclRuleResponse, status_code=201)
async def api_create_acl_rule(body: AclRuleCreate, session: DBSession) -> AclRuleResponse:
    """Create a new ACL rule."""

    if body.frontend_id:
        fe = await get_frontend(session, body.frontend_id)
        if not fe:
            raise HTTPException(status_code=404, detail="Frontend not found")

    row = await create_acl_rule(
        session,
        frontend_id=body.frontend_id,
        domain=body.domain,
        backend_name=body.backend_name or "",
        acl_match_type=body.acl_match_type,
        is_redirect=body.is_redirect,
        redirect_target=body.redirect_target,
        redirect_code=body.redirect_code or 301,
        comment=body.comment,
        sort_order=body.sort_order,
        enabled=body.enabled,
    )
    return AclRuleResponse.model_validate(row)


@router.put("/api/acl-rules/{rule_id}", response_model=AclRuleResponse)
async def api_update_acl_rule(rule_id: int, body: AclRuleUpdate, session: DBSession) -> AclRuleResponse:
    """Update an existing ACL rule."""

    row = await get_acl_rule(session, rule_id)
    if not row:
        raise HTTPException(status_code=404, detail="ACL rule not found")

    updated = await update_acl_rule(
        session,
        row,
        frontend_id=body.frontend_id,
        domain=body.domain,
        backend_name=body.backend_name,
        acl_match_type=body.acl_match_type,
        is_redirect=body.is_redirect,
        redirect_target=body.redirect_target,
        redirect_code=body.redirect_code,
        comment=body.comment,
        sort_order=body.sort_order,
        enabled=body.enabled,
        fields_set=frozenset(body.model_fields_set),
    )

    return AclRuleResponse.model_validate(updated)


@router.delete("/api/acl-rules/{rule_id}", response_model=MessageResponse)
async def api_delete_acl_rule(rule_id: int, session: DBSession) -> MessageResponse:
    """Delete an ACL rule."""

    row = await get_acl_rule(session, rule_id)
    if not row:
        raise HTTPException(status_code=404, detail="ACL rule not found")

    await delete_acl_rule(session, row)
    return MessageResponse(detail="ACL rule deleted")
