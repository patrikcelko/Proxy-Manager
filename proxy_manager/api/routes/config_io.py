"""
Config import/export routes
============================
"""

from fastapi import APIRouter, HTTPException

from proxy_manager.api.dependencies import DBSession
from proxy_manager.api.schemas.common import MessageResponse
from proxy_manager.api.schemas.config_io import (
    ConfigExportResponse,
    ConfigImportRequest,
    OverviewResponse,
)
from proxy_manager.config_parser.generator import generate_config
from proxy_manager.config_parser.parser import parse_config
from proxy_manager.database.models.acl_rule import (
    create_acl_rule,
    delete_all_acl_rules,
    list_acl_rules,
    list_all_acl_rules,
)
from proxy_manager.database.models.backend import (
    create_backend,
    create_backend_server,
    delete_all_backends,
    list_backend_servers,
    list_backends,
)
from proxy_manager.database.models.cache import create_cache_section, delete_all_cache_sections, list_cache_sections
from proxy_manager.database.models.default_setting import (
    create_default_setting,
    delete_all_default_settings,
    list_default_settings,
)
from proxy_manager.database.models.frontend import (
    create_frontend,
    create_frontend_bind,
    create_frontend_option,
    delete_all_frontends,
    list_frontend_binds,
    list_frontend_options,
    list_frontends,
)
from proxy_manager.database.models.global_setting import (
    create_global_setting,
    delete_all_global_settings,
    list_global_settings,
)
from proxy_manager.database.models.http_errors import (
    create_http_error_entry,
    create_http_errors_section,
    delete_all_http_errors_sections,
    list_http_error_entries,
    list_http_errors_sections,
)
from proxy_manager.database.models.listen_block import (
    create_listen_block,
    create_listen_block_bind,
    delete_all_listen_blocks,
    list_listen_block_binds,
    list_listen_blocks,
)
from proxy_manager.database.models.mailer import (
    create_mailer_entry,
    create_mailer_section,
    delete_all_mailer_sections,
    list_mailer_entries,
    list_mailer_sections,
)
from proxy_manager.database.models.peer import (
    create_peer_entry,
    create_peer_section,
    delete_all_peer_sections,
    list_peer_entries,
    list_peer_sections,
)
from proxy_manager.database.models.resolver import (
    create_resolver,
    create_resolver_nameserver,
    delete_all_resolvers,
    list_resolver_nameservers,
    list_resolvers,
)
from proxy_manager.database.models.ssl_certificate import (
    create_ssl_certificate,
    delete_all_ssl_certificates,
    get_ssl_certificate_by_domain,
    list_ssl_certificates,
)
from proxy_manager.database.models.userlist import (
    create_userlist,
    create_userlist_entry,
    delete_all_userlists,
    list_userlist_entries,
    list_userlists,
)

router = APIRouter(tags=['config'])


@router.get('/api/overview', response_model=OverviewResponse)
async def api_overview(session: DBSession) -> OverviewResponse:
    """Return a summary of all configured sections."""

    gs = await list_global_settings(session)
    ds = await list_default_settings(session)
    uls = await list_userlists(session)
    fes = await list_frontends(session)
    acls = await list_all_acl_rules(session)
    bes = await list_backends(session)
    lbs = await list_listen_blocks(session)
    resolvers = await list_resolvers(session)
    peers = await list_peer_sections(session)
    mailers = await list_mailer_sections(session)
    http_errors = await list_http_errors_sections(session)
    caches = await list_cache_sections(session)
    ssl_certs = await list_ssl_certificates(session)

    server_count = 0
    for be in bes:
        srvs = await list_backend_servers(session, be.id)
        server_count += len(srvs)

    return OverviewResponse(
        global_settings=len(gs),
        default_settings=len(ds),
        userlists=len(uls),
        frontends=len(fes),
        acl_rules=len(acls),
        backends=len(bes),
        backend_servers=server_count,
        listen_blocks=len(lbs),
        resolvers=len(resolvers),
        peers=len(peers),
        mailers=len(mailers),
        http_errors=len(http_errors),
        caches=len(caches),
        ssl_certificates=len(ssl_certs),
    )


@router.post('/api/config/import', response_model=MessageResponse)
async def api_import_config(body: ConfigImportRequest, session: DBSession) -> MessageResponse:
    """Import an HAProxy configuration from text."""

    try:
        parsed = parse_config(body.config_text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Parse error: {e}') from e

    if not body.merge:
        # Clear everything
        await delete_all_acl_rules(session)
        await delete_all_frontends(session)
        await delete_all_backends(session)
        await delete_all_userlists(session)
        await delete_all_listen_blocks(session)
        await delete_all_global_settings(session)
        await delete_all_default_settings(session)
        await delete_all_resolvers(session)
        await delete_all_peer_sections(session)
        await delete_all_mailer_sections(session)
        await delete_all_http_errors_sections(session)
        await delete_all_cache_sections(session)
        await delete_all_ssl_certificates(session)

    # Import global settings
    for s in parsed.global_settings:
        await create_global_setting(
            session,
            directive=s.directive,
            value=s.value,
            comment=s.comment,
            sort_order=s.order,
        )

    # Import default settings
    for s in parsed.default_settings:
        await create_default_setting(
            session,
            directive=s.directive,
            value=s.value,
            comment=s.comment,
            sort_order=s.order,
        )

    # Import userlists
    for ul in parsed.userlists:
        db_ul = await create_userlist(session, name=ul.name)
        for e in ul.entries:
            await create_userlist_entry(
                session,
                userlist_id=db_ul.id,
                username=e.username,
                password_hash=e.password_hash,
                sort_order=e.order,
            )

    # Import listen blocks
    for lb in parsed.listen_blocks:
        db_lb = await create_listen_block(
            session,
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
        )
        for i, bind_line in enumerate(lb.binds):
            await create_listen_block_bind(
                session,
                listen_block_id=db_lb.id,
                bind_line=bind_line,
                sort_order=i,
            )

    # Import frontends
    for fe in parsed.frontends:
        db_fe = await create_frontend(
            session,
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
        )
        for idx, bind in enumerate(fe.binds):
            await create_frontend_bind(session, frontend_id=db_fe.id, bind_line=bind, sort_order=idx)
        for idx, opt in enumerate(fe.options):
            await create_frontend_option(
                session,
                frontend_id=db_fe.id,
                directive=opt.directive,
                value=opt.value,
                comment=opt.comment,
                sort_order=opt.order if opt.order else idx,
            )
        for acl in fe.acls:
            await create_acl_rule(
                session,
                frontend_id=db_fe.id,
                domain=acl.domain,
                backend_name=acl.backend_name,
                acl_match_type=acl.acl_match_type,
                is_redirect=acl.is_redirect,
                redirect_target=acl.redirect_target,
                redirect_code=acl.redirect_code,
                comment=acl.comment,
                sort_order=acl.order,
                enabled=acl.enabled,
            )

    # Import backends
    for be in parsed.backends:
        db_be = await create_backend(
            session,
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
        )
        for srv in be.servers:
            await create_backend_server(
                session,
                backend_id=db_be.id,
                name=srv.name,
                address=srv.address,
                port=srv.port,
                check_enabled=srv.check_enabled,
                maxconn=srv.maxconn,
                maxqueue=srv.maxqueue,
                extra_params=srv.extra_params,
                sort_order=srv.order,
                weight=srv.weight,
                ssl_enabled=srv.ssl_enabled,
                ssl_verify=srv.ssl_verify,
                backup=srv.backup,
                inter=srv.inter,
                fastinter=srv.fastinter,
                downinter=srv.downinter,
                rise=srv.rise,
                fall=srv.fall,
                cookie_value=srv.cookie_value,
                send_proxy=srv.send_proxy,
                send_proxy_v2=srv.send_proxy_v2,
                slowstart=srv.slowstart,
                resolve_prefer=srv.resolve_prefer,
                resolvers_ref=srv.resolvers_ref,
                on_marked_down=srv.on_marked_down,
                disabled=srv.disabled,
            )

    # Import resolvers
    for r in parsed.resolvers:
        db_r = await create_resolver(
            session,
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
        )
        for ns in r.nameservers:
            await create_resolver_nameserver(
                session,
                resolver_id=db_r.id,
                name=ns.name,
                address=ns.address,
                port=ns.port,
                sort_order=ns.order,
            )

    # Import peers
    for p in parsed.peers:
        db_p = await create_peer_section(
            session,
            name=p.name,
            comment=p.comment,
            extra_options=p.extra_options,
            default_bind=p.default_bind,
            default_server_options=p.default_server_options,
        )
        for e in p.entries:
            await create_peer_entry(
                session,
                peer_section_id=db_p.id,
                name=e.name,
                address=e.address,
                port=e.port,
                sort_order=e.order,
            )

    # Import mailers
    for m in parsed.mailers:
        db_m = await create_mailer_section(
            session,
            name=m.name,
            timeout_mail=m.timeout_mail,
            comment=m.comment,
            extra_options=m.extra_options,
        )
        for e in m.entries:
            await create_mailer_entry(
                session,
                mailer_section_id=db_m.id,
                name=e.name,
                address=e.address,
                port=e.port,
                smtp_auth=e.smtp_auth,
                smtp_user=e.smtp_user,
                smtp_password=e.smtp_password,
                use_tls=e.use_tls,
                use_starttls=e.use_starttls,
                sort_order=e.order,
            )

    # Import http-errors
    for he in parsed.http_errors:
        db_he = await create_http_errors_section(
            session,
            name=he.name,
            comment=he.comment,
            extra_options=he.extra_options,
        )
        for e in he.entries:
            await create_http_error_entry(
                session,
                section_id=db_he.id,
                status_code=e.status_code,
                type=e.type,
                value=e.value,
                sort_order=e.order,
            )

    # Import caches
    for c in parsed.caches:
        await create_cache_section(
            session,
            name=c.name,
            total_max_size=c.total_max_size,
            max_object_size=c.max_object_size,
            max_age=c.max_age,
            max_secondary_entries=c.max_secondary_entries,
            process_vary=c.process_vary,
            comment=c.comment,
            extra_options=c.extra_options,
        )

    # Import SSL certificates (extracted from bind lines)
    ssl_imported = 0
    for sc in parsed.ssl_certificates:
        # Skip if a certificate with this domain already exists
        existing = await get_ssl_certificate_by_domain(session, sc.domain)
        if existing:
            continue
        await create_ssl_certificate(
            session,
            domain=sc.domain,
            alt_domains=sc.alt_domains,
            provider=sc.provider,
            status=sc.status,
            cert_path=sc.cert_path,
            key_path=sc.key_path,
            fullchain_path=sc.fullchain_path,
            auto_renew=sc.auto_renew,
            challenge_type=sc.challenge_type,
            comment=sc.comment,
        )
        ssl_imported += 1

    counts = (
        f'{len(parsed.global_settings)} global, {len(parsed.default_settings)} defaults, '
        f'{len(parsed.userlists)} userlists, {len(parsed.frontends)} frontends, '
        f'{len(parsed.backends)} backends, {len(parsed.listen_blocks)} listen blocks, '
        f'{len(parsed.resolvers)} resolvers, {len(parsed.peers)} peers, '
        f'{len(parsed.mailers)} mailers, {len(parsed.http_errors)} http-errors, '
        f'{len(parsed.caches)} caches, {ssl_imported} ssl certificates'
    )
    return MessageResponse(detail=f'Config imported: {counts}')


@router.get('/api/config/export', response_model=ConfigExportResponse)
async def api_export_config(session: DBSession) -> ConfigExportResponse:
    """Export the current HAProxy configuration as text."""

    gs = await list_global_settings(session)
    ds = await list_default_settings(session)
    lbs_raw = await list_listen_blocks(session)

    listen_blocks = []
    for lb in lbs_raw:
        lb_binds = await list_listen_block_binds(session, lb.id)
        listen_blocks.append((lb, lb_binds))

    uls_raw = await list_userlists(session)
    userlists = []
    for ul in uls_raw:
        entries = await list_userlist_entries(session, ul.id)
        userlists.append((ul, entries))

    fes_raw = await list_frontends(session)
    frontends = []
    for fe in fes_raw:
        binds = await list_frontend_binds(session, fe.id)
        opts = await list_frontend_options(session, fe.id)
        acls = await list_acl_rules(session, fe.id)
        frontends.append((fe, binds, opts, acls))

    bes_raw = await list_backends(session)
    backends = []
    for be in bes_raw:
        srvs = await list_backend_servers(session, be.id)
        backends.append((be, srvs))

    # Resolvers
    res_raw = await list_resolvers(session)
    resolvers_data = []
    for r in res_raw:
        ns = await list_resolver_nameservers(session, r.id)
        resolvers_data.append((r, ns))

    # Peers
    peers_raw = await list_peer_sections(session)
    peers_data = []
    for p in peers_raw:
        entries = await list_peer_entries(session, p.id)
        peers_data.append((p, entries))

    # Mailers
    mailers_raw = await list_mailer_sections(session)
    mailers_data = []
    for m in mailers_raw:
        entries = await list_mailer_entries(session, m.id)
        mailers_data.append((m, entries))

    # HTTP Errors
    he_raw = await list_http_errors_sections(session)
    http_errors_data = []
    for he in he_raw:
        entries = await list_http_error_entries(session, he.id)
        http_errors_data.append((he, entries))

    # Caches
    caches_data = await list_cache_sections(session)

    config_text = generate_config(
        global_settings=gs,
        default_settings=ds,
        listen_blocks=listen_blocks,
        userlists=userlists,
        frontends=frontends,
        backends=backends,
        resolvers=resolvers_data,
        peers=peers_data,
        mailers=mailers_data,
        http_errors=http_errors_data,
        caches=caches_data,
    )
    return ConfigExportResponse(config_text=config_text)


@router.post('/api/config/validate')
async def api_validate_config(body: ConfigImportRequest) -> dict[str, bool | str]:
    """Validate HAProxy configuration text without importing it."""

    try:
        parse_config(body.config_text)
    except Exception as e:
        return {'valid': False, 'error': f'Parse error: {e}'}

    return {'valid': True, 'error': ''}
