"""
Configuration snapshot utilities
=================================

Functions for taking, comparing, and restoring configuration snapshots.
A snapshot is a JSON-serializable dictionary representing the complete
state of all HAProxy configuration entities in the database.
"""

import json
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.database.models.acl_rule import create_acl_rule, delete_all_acl_rules, list_all_acl_rules
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
    list_ssl_certificates,
)
from proxy_manager.database.models.userlist import (
    create_userlist,
    create_userlist_entry,
    delete_all_userlists,
    list_userlist_entries,
    list_userlists,
)

# Sections tracked for diff/badge display, mapped to sidebar section IDs
SECTION_SIDEBAR_MAP: dict[str, str] = {
    "global_settings": "global",
    "default_settings": "defaults",
    "frontends": "frontends",
    "acl_rules": "acl",
    "backends": "backends",
    "listen_blocks": "listen",
    "userlists": "userlists",
    "resolvers": "resolvers",
    "peers": "peers",
    "mailers": "mailers",
    "http_errors": "http-errors",
    "caches": "caches",
    "ssl_certificates": "ssl-certificates",
}


async def take_snapshot(session: AsyncSession) -> dict[str, Any]:
    """Take a full JSON-serializable snapshot of all config entities."""

    snapshot: dict[str, Any] = {}

    # Global settings
    gs = await list_global_settings(session)
    snapshot["global_settings"] = [{"id": s.id, "directive": s.directive, "value": s.value, "comment": s.comment, "sort_order": s.sort_order} for s in gs]

    # Default settings
    ds = await list_default_settings(session)
    snapshot["default_settings"] = [{"id": s.id, "directive": s.directive, "value": s.value, "comment": s.comment, "sort_order": s.sort_order} for s in ds]

    # Userlists
    uls = await list_userlists(session)
    userlists_data = []
    for ul in uls:
        entries = await list_userlist_entries(session, ul.id)
        userlists_data.append(
            {
                "name": ul.name,
                "entries": [{"username": e.username, "password_hash": e.password_hash, "sort_order": e.sort_order} for e in entries],
            }
        )
    snapshot["userlists"] = userlists_data

    # Frontends (binds + options, ACL rules tracked separately)
    fes = await list_frontends(session)
    frontends_data = []
    fe_name_map: dict[int, str] = {}
    for fe in fes:
        fe_name_map[fe.id] = fe.name
        binds = await list_frontend_binds(session, fe.id)
        opts = await list_frontend_options(session, fe.id)
        frontends_data.append(
            {
                "name": fe.name,
                "mode": fe.mode,
                "default_backend": fe.default_backend,
                "timeout_client": fe.timeout_client,
                "timeout_http_request": fe.timeout_http_request,
                "timeout_http_keep_alive": fe.timeout_http_keep_alive,
                "maxconn": fe.maxconn,
                "option_httplog": fe.option_httplog,
                "option_tcplog": fe.option_tcplog,
                "option_forwardfor": fe.option_forwardfor,
                "compression_algo": fe.compression_algo,
                "compression_type": fe.compression_type,
                "comment": fe.comment,
                "binds": [{"bind_line": b.bind_line, "sort_order": b.sort_order} for b in binds],
                "options": [{"directive": o.directive, "value": o.value, "comment": o.comment, "sort_order": o.sort_order} for o in opts],
            }
        )
    snapshot["frontends"] = frontends_data

    # ACL rules (stored separately with frontend_name for portability)
    all_acls = await list_all_acl_rules(session)
    snapshot["acl_rules"] = [
        {
            "id": acl.id,
            "frontend_name": fe_name_map.get(acl.frontend_id, "") if acl.frontend_id is not None else "",
            "domain": acl.domain,
            "backend_name": acl.backend_name,
            "acl_match_type": acl.acl_match_type,
            "is_redirect": acl.is_redirect,
            "redirect_target": acl.redirect_target,
            "redirect_code": acl.redirect_code,
            "comment": acl.comment,
            "sort_order": acl.sort_order,
            "enabled": acl.enabled,
        }
        for acl in all_acls
    ]

    # Backends + servers
    bes = await list_backends(session)
    backends_data = []
    for be in bes:
        srvs = await list_backend_servers(session, be.id)
        backends_data.append(
            {
                "name": be.name,
                "mode": be.mode,
                "balance": be.balance,
                "option_forwardfor": be.option_forwardfor,
                "option_redispatch": be.option_redispatch,
                "retries": be.retries,
                "retry_on": be.retry_on,
                "auth_userlist": be.auth_userlist,
                "health_check_enabled": be.health_check_enabled,
                "health_check_method": be.health_check_method,
                "health_check_uri": be.health_check_uri,
                "errorfile": be.errorfile,
                "comment": be.comment,
                "extra_options": be.extra_options,
                "cookie": be.cookie,
                "timeout_server": be.timeout_server,
                "timeout_connect": be.timeout_connect,
                "timeout_queue": be.timeout_queue,
                "http_check_expect": be.http_check_expect,
                "default_server_options": be.default_server_options,
                "http_reuse": be.http_reuse,
                "hash_type": be.hash_type,
                "option_httplog": be.option_httplog,
                "option_tcplog": be.option_tcplog,
                "compression_algo": be.compression_algo,
                "compression_type": be.compression_type,
                "servers": [
                    {
                        "name": s.name,
                        "address": s.address,
                        "port": s.port,
                        "check_enabled": s.check_enabled,
                        "maxconn": s.maxconn,
                        "maxqueue": s.maxqueue,
                        "extra_params": s.extra_params,
                        "sort_order": s.sort_order,
                        "weight": s.weight,
                        "ssl_enabled": s.ssl_enabled,
                        "ssl_verify": s.ssl_verify,
                        "backup": s.backup,
                        "inter": s.inter,
                        "fastinter": s.fastinter,
                        "downinter": s.downinter,
                        "rise": s.rise,
                        "fall": s.fall,
                        "cookie_value": s.cookie_value,
                        "send_proxy": s.send_proxy,
                        "send_proxy_v2": s.send_proxy_v2,
                        "slowstart": s.slowstart,
                        "resolve_prefer": s.resolve_prefer,
                        "resolvers_ref": s.resolvers_ref,
                        "on_marked_down": s.on_marked_down,
                        "disabled": s.disabled,
                    }
                    for s in srvs
                ],
            }
        )
    snapshot["backends"] = backends_data

    # Listen blocks + binds
    lbs = await list_listen_blocks(session)
    listen_data = []
    for lb in lbs:
        binds = await list_listen_block_binds(session, lb.id)
        listen_data.append(
            {
                "name": lb.name,
                "mode": lb.mode,
                "balance": lb.balance,
                "maxconn": lb.maxconn,
                "timeout_client": lb.timeout_client,
                "timeout_server": lb.timeout_server,
                "timeout_connect": lb.timeout_connect,
                "default_server_params": lb.default_server_params,
                "option_forwardfor": lb.option_forwardfor,
                "option_httplog": lb.option_httplog,
                "option_tcplog": lb.option_tcplog,
                "content": lb.content,
                "comment": lb.comment,
                "sort_order": lb.sort_order,
                "binds": [{"bind_line": b.bind_line, "sort_order": b.sort_order} for b in binds],
            }
        )
    snapshot["listen_blocks"] = listen_data

    # Resolvers + nameservers
    res = await list_resolvers(session)
    resolvers_data = []
    for r in res:
        ns = await list_resolver_nameservers(session, r.id)
        resolvers_data.append(
            {
                "name": r.name,
                "resolve_retries": r.resolve_retries,
                "timeout_resolve": r.timeout_resolve,
                "timeout_retry": r.timeout_retry,
                "hold_valid": r.hold_valid,
                "hold_other": r.hold_other,
                "hold_refused": r.hold_refused,
                "hold_timeout": r.hold_timeout,
                "hold_obsolete": r.hold_obsolete,
                "hold_nx": r.hold_nx,
                "hold_aa": r.hold_aa,
                "accepted_payload_size": r.accepted_payload_size,
                "parse_resolv_conf": r.parse_resolv_conf,
                "comment": r.comment,
                "extra_options": r.extra_options,
                "nameservers": [{"name": n.name, "address": n.address, "port": n.port, "sort_order": n.sort_order} for n in ns],
            }
        )
    snapshot["resolvers"] = resolvers_data

    # Peers + entries
    peers_raw = await list_peer_sections(session)
    peers_data = []
    for p in peers_raw:
        entries = await list_peer_entries(session, p.id)
        peers_data.append(
            {
                "name": p.name,
                "comment": p.comment,
                "extra_options": p.extra_options,
                "default_bind": p.default_bind,
                "default_server_options": p.default_server_options,
                "entries": [{"name": e.name, "address": e.address, "port": e.port, "sort_order": e.sort_order} for e in entries],
            }
        )
    snapshot["peers"] = peers_data

    # Mailers + entries
    mailers_raw = await list_mailer_sections(session)
    mailers_data = []
    for m in mailers_raw:
        entries = await list_mailer_entries(session, m.id)
        mailers_data.append(
            {
                "name": m.name,
                "timeout_mail": m.timeout_mail,
                "comment": m.comment,
                "extra_options": m.extra_options,
                "entries": [
                    {
                        "name": e.name,
                        "address": e.address,
                        "port": e.port,
                        "smtp_auth": e.smtp_auth,
                        "smtp_user": e.smtp_user,
                        "smtp_password": e.smtp_password,
                        "use_tls": e.use_tls,
                        "use_starttls": e.use_starttls,
                        "sort_order": e.sort_order,
                    }
                    for e in entries
                ],
            }
        )
    snapshot["mailers"] = mailers_data

    # HTTP errors + entries
    he_raw = await list_http_errors_sections(session)
    http_errors_data = []
    for he in he_raw:
        entries = await list_http_error_entries(session, he.id)
        http_errors_data.append(
            {
                "name": he.name,
                "comment": he.comment,
                "extra_options": he.extra_options,
                "entries": [{"status_code": e.status_code, "type": e.type, "value": e.value, "sort_order": e.sort_order} for e in entries],
            }
        )
    snapshot["http_errors"] = http_errors_data

    # Caches
    caches = await list_cache_sections(session)
    snapshot["caches"] = [
        {
            "name": c.name,
            "total_max_size": c.total_max_size,
            "max_object_size": c.max_object_size,
            "max_age": c.max_age,
            "max_secondary_entries": c.max_secondary_entries,
            "process_vary": c.process_vary,
            "comment": c.comment,
            "extra_options": c.extra_options,
        }
        for c in caches
    ]

    # SSL certificates
    certs = await list_ssl_certificates(session)
    snapshot["ssl_certificates"] = [
        {
            "domain": c.domain,
            "alt_domains": c.alt_domains,
            "email": c.email,
            "provider": c.provider,
            "status": c.status,
            "cert_path": c.cert_path,
            "key_path": c.key_path,
            "fullchain_path": c.fullchain_path,
            "issued_at": c.issued_at.isoformat() if c.issued_at else None,
            "expires_at": c.expires_at.isoformat() if c.expires_at else None,
            "auto_renew": c.auto_renew,
            "challenge_type": c.challenge_type,
            "dns_plugin": c.dns_plugin,
            "last_renewal_at": c.last_renewal_at.isoformat() if c.last_renewal_at else None,
            "last_error": c.last_error,
            "comment": c.comment,
        }
        for c in certs
    ]

    return snapshot


async def clear_all_entities(session: AsyncSession) -> None:
    """Delete all configuration entities from the database."""

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


async def restore_snapshot(session: AsyncSession, snapshot_data: dict[str, Any]) -> None:
    """Restore the database to match a snapshot. Clears all existing data first."""

    await clear_all_entities(session)

    # Global settings
    for s in snapshot_data.get("global_settings", []):
        await create_global_setting(session, directive=s["directive"], value=s.get("value"), comment=s.get("comment"), sort_order=s.get("sort_order", 0))

    # Default settings
    for s in snapshot_data.get("default_settings", []):
        await create_default_setting(session, directive=s["directive"], value=s.get("value"), comment=s.get("comment"), sort_order=s.get("sort_order", 0))

    # Userlists
    for ul in snapshot_data.get("userlists", []):
        db_ul = await create_userlist(session, name=ul["name"])

        for e in ul.get("entries", []):
            await create_userlist_entry(
                session,
                userlist_id=db_ul.id,
                username=e["username"],
                password_hash=e.get("password_hash", ""),
                sort_order=e.get("sort_order", 0),
            )

    # Listen blocks
    for lb in snapshot_data.get("listen_blocks", []):
        db_lb = await create_listen_block(
            session,
            name=lb["name"],
            mode=lb.get("mode"),
            balance=lb.get("balance"),
            maxconn=lb.get("maxconn"),
            timeout_client=lb.get("timeout_client"),
            timeout_server=lb.get("timeout_server"),
            timeout_connect=lb.get("timeout_connect"),
            default_server_params=lb.get("default_server_params"),
            option_forwardfor=lb.get("option_forwardfor", False),
            option_httplog=lb.get("option_httplog", False),
            option_tcplog=lb.get("option_tcplog", False),
            content=lb.get("content"),
            comment=lb.get("comment"),
            sort_order=lb.get("sort_order", 0),
        )

        for b in lb.get("binds", []):
            await create_listen_block_bind(session, listen_block_id=db_lb.id, bind_line=b["bind_line"], sort_order=b.get("sort_order", 0))

    # Frontends
    fe_id_map: dict[str, int] = {}
    for fe in snapshot_data.get("frontends", []):
        db_fe = await create_frontend(
            session,
            name=fe["name"],
            mode=fe.get("mode", "http"),
            default_backend=fe.get("default_backend"),
            comment=fe.get("comment"),
            timeout_client=fe.get("timeout_client"),
            timeout_http_request=fe.get("timeout_http_request"),
            timeout_http_keep_alive=fe.get("timeout_http_keep_alive"),
            maxconn=fe.get("maxconn"),
            option_httplog=fe.get("option_httplog", False),
            option_tcplog=fe.get("option_tcplog", False),
            option_forwardfor=fe.get("option_forwardfor", False),
            compression_algo=fe.get("compression_algo"),
            compression_type=fe.get("compression_type"),
        )
        fe_id_map[fe["name"]] = db_fe.id

        for b in fe.get("binds", []):
            await create_frontend_bind(session, frontend_id=db_fe.id, bind_line=b["bind_line"], sort_order=b.get("sort_order", 0))

        for o in fe.get("options", []):
            await create_frontend_option(
                session,
                frontend_id=db_fe.id,
                directive=o["directive"],
                value=o.get("value"),
                comment=o.get("comment"),
                sort_order=o.get("sort_order", 0),
            )

    # ACL rules
    for acl in snapshot_data.get("acl_rules", []):
        fe_name = acl.get("frontend_name", "")
        fe_id = fe_id_map.get(fe_name)

        if fe_id is None:
            continue
        await create_acl_rule(
            session,
            frontend_id=fe_id,
            domain=acl["domain"],
            backend_name=acl.get("backend_name"),
            acl_match_type=acl.get("acl_match_type", "hdr_dom"),
            is_redirect=acl.get("is_redirect", False),
            redirect_target=acl.get("redirect_target"),
            redirect_code=acl.get("redirect_code", 308),
            comment=acl.get("comment"),
            sort_order=acl.get("sort_order", 0),
            enabled=acl.get("enabled", True),
        )

    # Backends
    for be in snapshot_data.get("backends", []):
        db_be = await create_backend(
            session,
            name=be["name"],
            mode=be.get("mode"),
            balance=be.get("balance"),
            option_forwardfor=be.get("option_forwardfor", False),
            option_redispatch=be.get("option_redispatch", False),
            retries=be.get("retries"),
            retry_on=be.get("retry_on"),
            auth_userlist=be.get("auth_userlist"),
            health_check_enabled=be.get("health_check_enabled", False),
            health_check_method=be.get("health_check_method"),
            health_check_uri=be.get("health_check_uri"),
            errorfile=be.get("errorfile"),
            comment=be.get("comment"),
            extra_options=be.get("extra_options"),
            cookie=be.get("cookie"),
            timeout_server=be.get("timeout_server"),
            timeout_connect=be.get("timeout_connect"),
            timeout_queue=be.get("timeout_queue"),
            http_check_expect=be.get("http_check_expect"),
            default_server_options=be.get("default_server_options"),
            http_reuse=be.get("http_reuse"),
            hash_type=be.get("hash_type"),
            option_httplog=be.get("option_httplog", False),
            option_tcplog=be.get("option_tcplog", False),
            compression_algo=be.get("compression_algo"),
            compression_type=be.get("compression_type"),
        )

        for srv in be.get("servers", []):
            await create_backend_server(
                session,
                backend_id=db_be.id,
                name=srv["name"],
                address=srv["address"],
                port=srv["port"],
                check_enabled=srv.get("check_enabled", False),
                maxconn=srv.get("maxconn"),
                maxqueue=srv.get("maxqueue"),
                extra_params=srv.get("extra_params"),
                sort_order=srv.get("sort_order", 0),
                weight=srv.get("weight"),
                ssl_enabled=srv.get("ssl_enabled", False),
                ssl_verify=srv.get("ssl_verify"),
                backup=srv.get("backup", False),
                inter=srv.get("inter"),
                fastinter=srv.get("fastinter"),
                downinter=srv.get("downinter"),
                rise=srv.get("rise"),
                fall=srv.get("fall"),
                cookie_value=srv.get("cookie_value"),
                send_proxy=srv.get("send_proxy", False),
                send_proxy_v2=srv.get("send_proxy_v2", False),
                slowstart=srv.get("slowstart"),
                resolve_prefer=srv.get("resolve_prefer"),
                resolvers_ref=srv.get("resolvers_ref"),
                on_marked_down=srv.get("on_marked_down"),
                disabled=srv.get("disabled", False),
            )

    # Resolvers
    for r in snapshot_data.get("resolvers", []):
        db_r = await create_resolver(
            session,
            name=r["name"],
            resolve_retries=r.get("resolve_retries"),
            timeout_resolve=r.get("timeout_resolve"),
            timeout_retry=r.get("timeout_retry"),
            hold_valid=r.get("hold_valid"),
            hold_other=r.get("hold_other"),
            hold_refused=r.get("hold_refused"),
            hold_timeout=r.get("hold_timeout"),
            hold_obsolete=r.get("hold_obsolete"),
            hold_nx=r.get("hold_nx"),
            hold_aa=r.get("hold_aa"),
            accepted_payload_size=r.get("accepted_payload_size"),
            parse_resolv_conf=r.get("parse_resolv_conf"),
            comment=r.get("comment"),
            extra_options=r.get("extra_options"),
        )

        for ns in r.get("nameservers", []):
            await create_resolver_nameserver(
                session,
                resolver_id=db_r.id,
                name=ns["name"],
                address=ns["address"],
                port=ns["port"],
                sort_order=ns.get("sort_order", 0),
            )

    # Peers
    for p in snapshot_data.get("peers", []):
        db_p = await create_peer_section(
            session,
            name=p["name"],
            comment=p.get("comment"),
            extra_options=p.get("extra_options"),
            default_bind=p.get("default_bind"),
            default_server_options=p.get("default_server_options"),
        )

        for e in p.get("entries", []):
            await create_peer_entry(
                session,
                peer_section_id=db_p.id,
                name=e["name"],
                address=e["address"],
                port=e["port"],
                sort_order=e.get("sort_order", 0),
            )

    # Mailers
    for m in snapshot_data.get("mailers", []):
        db_m = await create_mailer_section(
            session,
            name=m["name"],
            timeout_mail=m.get("timeout_mail"),
            comment=m.get("comment"),
            extra_options=m.get("extra_options"),
        )

        for e in m.get("entries", []):
            await create_mailer_entry(
                session,
                mailer_section_id=db_m.id,
                name=e["name"],
                address=e["address"],
                port=e["port"],
                smtp_auth=e.get("smtp_auth", False),
                smtp_user=e.get("smtp_user"),
                smtp_password=e.get("smtp_password"),
                use_tls=e.get("use_tls", False),
                use_starttls=e.get("use_starttls", False),
                sort_order=e.get("sort_order", 0),
            )

    # HTTP errors
    for he in snapshot_data.get("http_errors", []):
        db_he = await create_http_errors_section(
            session,
            name=he["name"],
            comment=he.get("comment"),
            extra_options=he.get("extra_options"),
        )

        for e in he.get("entries", []):
            await create_http_error_entry(
                session,
                section_id=db_he.id,
                status_code=e["status_code"],
                type=e["type"],
                value=e["value"],
                sort_order=e.get("sort_order", 0),
            )

    # Caches
    for c in snapshot_data.get("caches", []):
        await create_cache_section(
            session,
            name=c["name"],
            total_max_size=c.get("total_max_size"),
            max_object_size=c.get("max_object_size"),
            max_age=c.get("max_age"),
            max_secondary_entries=c.get("max_secondary_entries"),
            process_vary=c.get("process_vary"),
            comment=c.get("comment"),
            extra_options=c.get("extra_options"),
        )

    # SSL certificates
    for sc in snapshot_data.get("ssl_certificates", []):
        await create_ssl_certificate(
            session,
            domain=sc["domain"],
            alt_domains=sc.get("alt_domains"),
            email=sc.get("email"),
            provider=sc.get("provider", "manual"),
            status=sc.get("status", "pending"),
            cert_path=sc.get("cert_path"),
            key_path=sc.get("key_path"),
            fullchain_path=sc.get("fullchain_path"),
            issued_at=_parse_iso_datetime(sc.get("issued_at")),
            expires_at=_parse_iso_datetime(sc.get("expires_at")),
            auto_renew=sc.get("auto_renew", False),
            challenge_type=sc.get("challenge_type", "http"),
            dns_plugin=sc.get("dns_plugin"),
            last_renewal_at=_parse_iso_datetime(sc.get("last_renewal_at")),
            last_error=sc.get("last_error"),
            comment=sc.get("comment"),
        )


def _parse_iso_datetime(value: str | None) -> datetime | None:
    """Parse an ISO-8601 datetime string, returning *None* for falsy input."""

    if not value:
        return None
    return datetime.fromisoformat(value)


def compute_diff(old_snapshot: dict[str, Any], new_snapshot: dict[str, Any]) -> dict[str, Any]:
    """Compute a detailed diff between two snapshots.

    Returns a dict with per-section changes including created, deleted,
    and updated entities with field-level change details.
    """

    diff: dict[str, Any] = {}

    for section_key in SECTION_SIDEBAR_MAP:
        old_items = old_snapshot.get(section_key, [])
        new_items = new_snapshot.get(section_key, [])

        # Determine the name/key field for this section
        name_key = _section_name_key(section_key, old_items or new_items)
        section_diff = _diff_entity_list(old_items, new_items, name_key)

        if section_diff["total"] > 0:
            diff[section_key] = section_diff

    return diff


def compute_pending_counts(old_snapshot: dict[str, Any], new_snapshot: dict[str, Any]) -> dict[str, int]:
    """Compute per-section change counts for sidebar badges."""

    counts: dict[str, int] = {}
    for section_key in SECTION_SIDEBAR_MAP:
        old_items = old_snapshot.get(section_key, [])
        new_items = new_snapshot.get(section_key, [])
        name_key = _section_name_key(section_key, old_items or new_items)

        old_json = json.dumps(old_items, sort_keys=True, default=str)
        new_json = json.dumps(new_items, sort_keys=True, default=str)

        if old_json != new_json:
            diff = _diff_entity_list(old_items, new_items, name_key)
            counts[section_key] = diff["total"]
        else:
            counts[section_key] = 0

    return counts


def _section_name_key(section_key: str, items: list[dict[str, Any]] | None = None) -> str:
    """Return the field name used to identify entities in a section.

    Settings always use `"_ordered"` (positional comparison with
    `id` stripped) so that the diff stays correct even after a
    full re-import via Manual Edit, which deletes and re-creates
    all rows with new database IDs.
    """

    if section_key in ("global_settings", "default_settings"):
        return "_ordered"

    if section_key == "ssl_certificates":
        return "domain"

    if section_key == "acl_rules":
        return "_id_keyed"  # Use id-based matching with composite fallback

    return "name"


def _diff_entity_list(old_items: list[dict[str, Any]], new_items: list[dict[str, Any]], name_key: str) -> dict[str, Any]:
    """Diff two lists of entity dicts."""

    created: list[dict[str, Any]] = []
    deleted: list[dict[str, Any]] = []
    updated: list[dict[str, Any]] = []

    if name_key == "_ordered":
        # Settings: multi-phase matching that correctly handles
        # insertions, deletions, modifications, and directive
        # renames regardless of position or database IDs.
        _STRIP_KEYS = {"id"}  # noqa

        def _strip_meta(d: dict[str, Any]) -> dict[str, Any]:
            return {k: v for k, v in d.items() if k not in _STRIP_KEYS}

        def _content_key(d: dict[str, Any]) -> tuple[Any, Any, Any]:
            return (d.get("directive", ""), d.get("value", ""), d.get("comment"))

        def _emit_updated(old_i: int, new_j: int) -> None:
            old_stripped = _strip_meta(old_items[old_i])
            new_stripped = _strip_meta(new_items[new_j])
            if old_stripped == new_stripped:
                return  # identical after stripping meta - no change

            changes = _compute_field_changes(old_stripped, new_stripped)
            new_d = new_items[new_j].get("directive", "")
            entry: dict[str, Any] = {
                "entity": new_d,
                "old": old_stripped,
                "new": new_stripped,
                "changes": changes,
            }

            new_id = new_items[new_j].get("id")
            if new_id is not None:
                entry["entity_id"] = str(new_id)
            updated.append(entry)

        old_matched: set[int] = set()
        new_matched: set[int] = set()

        # Phase 0 Match by database ID (handles normal UI
        # operations including directive renames; IDs stay stable
        # between edits until a Manual-Edit re-import).
        old_by_id: dict[Any, int] = {}
        for i, item in enumerate(old_items):
            eid = item.get("id")

            if eid is not None:
                old_by_id[eid] = i

        for j, item in enumerate(new_items):
            eid = item.get("id")

            if eid is not None and eid in old_by_id:
                old_i = old_by_id.pop(eid)
                old_matched.add(old_i)
                new_matched.add(j)
                _emit_updated(old_i, j)

        # Phase 1 Exact content matches for remaining
        # (unchanged entries with different IDs, e.g. after
        # Manual-Edit re-import).  Track matched pairs so we
        # can detect ORDER changes afterwards.
        old_remaining = [i for i in range(len(old_items)) if i not in old_matched]

        old_by_content: dict[tuple[Any, Any, Any], list[int]] = {}
        for i in old_remaining:
            key = _content_key(old_items[i])
            old_by_content.setdefault(key, []).append(i)

        phase1_pairs: list[tuple[int, int]] = []

        for j in range(len(new_items)):
            if j in new_matched:
                continue

            key = _content_key(new_items[j])
            if key in old_by_content and old_by_content[key]:
                old_i = old_by_content[key].pop(0)
                old_matched.add(old_i)
                new_matched.add(j)
                phase1_pairs.append((old_i, j))

        # Phase 1b  Detect ORDER changes among content-matched
        # items.  After a Manual-Edit re-import sort_order values
        # are renumbered (e.g. 0,5,10 -> 0,1,2) which is noise,
        # but an actual UI reorder swaps the positions of items
        # in the list.  We distinguish the two by checking for
        # inversions in the old-position sequence (sorted by new
        # position).  Items involved in at least one inversion
        # were truly reordered.
        if len(phase1_pairs) > 1:
            phase1_pairs.sort(key=lambda p: p[1])
            old_positions = [p[0] for p in phase1_pairs]

            reordered: set[int] = set()
            for a in range(len(old_positions)):
                for b in range(a + 1, len(old_positions)):
                    if old_positions[a] > old_positions[b]:
                        reordered.add(a)
                        reordered.add(b)

            for idx in reordered:
                _emit_updated(phase1_pairs[idx][0], phase1_pairs[idx][1])

        # Phase 2 Match remaining by directive name
        # (modified entries after Manual-Edit re-import).
        old_remaining = [i for i in range(len(old_items)) if i not in old_matched]
        new_remaining = [j for j in range(len(new_items)) if j not in new_matched]

        old_by_directive: dict[str, list[int]] = {}
        for i in old_remaining:
            d = old_items[i].get("directive", "")
            old_by_directive.setdefault(d, []).append(i)

        still_new: list[int] = []
        for j in new_remaining:
            d = new_items[j].get("directive", "")

            if d in old_by_directive and old_by_directive[d]:
                old_i = old_by_directive[d].pop(0)
                _emit_updated(old_i, j)
            else:
                still_new.append(j)

        # Phase 3  Remaining unmatched -> created / deleted
        for d_indices in old_by_directive.values():
            for old_i in d_indices:
                entry = _strip_meta(old_items[old_i])
                deleted.append(entry)

        for j in still_new:
            entry = _strip_meta(new_items[j])
            new_id = new_items[j].get("id")

            if new_id is not None:
                entry["entity_id"] = str(new_id)
            created.append(entry)

        return {"created": created, "deleted": deleted, "updated": updated, "total": len(created) + len(deleted) + len(updated)}

    if name_key == "_id_keyed":
        # ACL rules: match by database id first (stable for normal UI operations
        # including reorder), then fall back to composite key without sort_order
        # for Manual Edit re-imports where IDs change.
        _id_strip = {"id"}

        def _strip_id(d: dict[str, Any]) -> dict[str, Any]:
            return {k: v for k, v in d.items() if k not in _id_strip}

        acl_by_id: dict[Any, dict[str, Any]] = {}
        for item in old_items:
            eid = item.get("id")
            if eid is not None:
                acl_by_id[eid] = item

        matched_old_ids: set[Any] = set()
        matched_new_idx: set[int] = set()

        # Phase 1: match by database id
        for j, new_item in enumerate(new_items):
            eid = new_item.get("id")
            if eid is not None and eid in acl_by_id:
                matched_old_ids.add(eid)
                matched_new_idx.add(j)
                old_stripped = _strip_id(acl_by_id[eid])
                new_stripped = _strip_id(new_item)
                if old_stripped != new_stripped:
                    changes = _compute_field_changes(old_stripped, new_stripped)
                    updated.append({"entity": str(eid), "entity_id": str(eid), "old": old_stripped, "new": new_stripped, "changes": changes})

        # Phase 2: composite fallback for unmatched (after Manual Edit re-import)
        def _acl_content_key(item: dict[str, Any]) -> str:
            return f"{item.get('frontend_name', '')}:{item.get('domain', '')}:{item.get('acl_match_type', '')}"

        remaining_old = [item for item in old_items if item.get("id") not in matched_old_ids]
        remaining_new = [(j, item) for j, item in enumerate(new_items) if j not in matched_new_idx]

        old_cmap: dict[str, list[dict[str, Any]]] = {}
        for item in remaining_old:
            key = _acl_content_key(item)
            old_cmap.setdefault(key, []).append(item)

        unmatched_new: list[dict[str, Any]] = []
        for _j, new_item in remaining_new:
            key = _acl_content_key(new_item)
            if key in old_cmap and old_cmap[key]:
                old_item = old_cmap[key].pop(0)
                old_stripped = _strip_id(old_item)
                new_stripped = _strip_id(new_item)
                if old_stripped != new_stripped:
                    changes = _compute_field_changes(old_stripped, new_stripped)
                    entry: dict[str, Any] = {"entity": key, "old": old_stripped, "new": new_stripped, "changes": changes}
                    new_id = new_item.get("id")
                    if new_id is not None:
                        entry["entity_id"] = str(new_id)
                    updated.append(entry)
            else:
                unmatched_new.append(new_item)

        for remaining in old_cmap.values():
            for item in remaining:
                deleted.append(_strip_id(item))
        for item in unmatched_new:
            entry = _strip_id(item)
            new_id = item.get("id")
            if new_id is not None:
                entry["entity_id"] = str(new_id)
            created.append(entry)

        return {"created": created, "deleted": deleted, "updated": updated, "total": len(created) + len(deleted) + len(updated)}

    old_map = {item.get(name_key, f"#{i}"): item for i, item in enumerate(old_items)}
    new_map = {item.get(name_key, f"#{i}"): item for i, item in enumerate(new_items)}

    # Created: in new but not in old
    for key in new_map:
        if key not in old_map:
            created.append(new_map[key])

    # Deleted: in old but not in new
    for key in old_map:
        if key not in new_map:
            deleted.append(old_map[key])

    # Updated: in both but different
    for key in old_map:
        if key in new_map:
            # Normalise nested list items by stripping sort_order
            # (list position encodes ordering) to avoid false diffs.
            old_norm = {k: _strip_nested_sort_order(v) for k, v in old_map[key].items()}
            new_norm = {k: _strip_nested_sort_order(v) for k, v in new_map[key].items()}
            old_json = json.dumps(old_norm, sort_keys=True, default=str)
            new_json = json.dumps(new_norm, sort_keys=True, default=str)

            if old_json != new_json:
                changes = _compute_field_changes(old_map[key], new_map[key])

                # For id-based matching (settings), show directive as
                # entity display name and carry the id separately.
                if name_key == "id":
                    display = new_map[key].get("directive", str(key))
                    updated.append(
                        {
                            "entity": display,
                            "entity_id": str(key),
                            "old": old_map[key],
                            "new": new_map[key],
                            "changes": changes,
                        }
                    )
                else:
                    updated.append(
                        {
                            "entity": key,
                            "old": old_map[key],
                            "new": new_map[key],
                            "changes": changes,
                        }
                    )

    # Rename detection
    # If an entity's name changed, the initial pass sees it as deleted +
    # created. Detect such pairs by field similarity and convert them
    # to "updated" entries so the UI shows "Modified" instead of
    # "Deleted" + "New".
    if deleted and created and name_key not in ("_ordered", "_id_keyed"):
        matched = _match_renamed_entities(deleted, created, name_key)

        for old_entity, new_entity in matched:
            deleted.remove(old_entity)
            created.remove(new_entity)
            changes = _compute_field_changes(old_entity, new_entity)
            updated.append(
                {
                    "entity": new_entity.get(name_key, ""),
                    "old": old_entity,
                    "new": new_entity,
                    "changes": changes,
                }
            )

    return {
        "created": created,
        "deleted": deleted,
        "updated": updated,
        "total": len(created) + len(deleted) + len(updated),
    }


def _match_renamed_entities(deleted: list[dict[str, Any]], created: list[dict[str, Any]], name_key: str) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Match deleted+created entity pairs that look like renames.

    When an entity's name changes (e.g. `stats` -> `statsc`), the
    initial key-based matching classifies it as one deletion and one
    creation.  This helper detects such pairs by comparing all fields
    *except* the name key. Pairs where ≥ 50 % of the remaining fields
    are identical are treated as the same entity that was renamed.

    Returns a list of *(old_entity, new_entity)* tuples that should be
    reclassified as "updated".
    """

    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    used_created: set[int] = set()

    for old_entity in deleted:
        best_score = 0.0
        best_idx = -1

        old_fields = {k: json.dumps(v, sort_keys=True, default=str) for k, v in old_entity.items() if k != name_key}
        all_keys_old = set(old_fields.keys())

        for j, new_entity in enumerate(created):
            if j in used_created:
                continue

            new_fields = {k: json.dumps(v, sort_keys=True, default=str) for k, v in new_entity.items() if k != name_key}
            all_keys = all_keys_old | set(new_fields.keys())
            if not all_keys:
                continue

            matching = sum(1 for k in all_keys if old_fields.get(k) == new_fields.get(k))
            score = matching / len(all_keys)

            if score > best_score:
                best_score = score
                best_idx = j

        if best_idx >= 0 and best_score >= 0.5:
            pairs.append((old_entity, created[best_idx]))
            used_created.add(best_idx)

    return pairs


def _strip_nested_sort_order(val: Any) -> Any:
    """Strip `sort_order` from dicts inside a list.

    List position already encodes ordering, so the explicit
    `sort_order` field is redundant.  Committed snapshots may
    store different `sort_order` values (e.g. all zeros vs
    sequential) which causes false-positive diffs.
    """

    if not isinstance(val, list):
        return val

    return [
        {k: v for k, v in item.items() if k != "sort_order"}
        if isinstance(item, dict)
        else item
        for item in val
    ]


def _compute_field_changes(old: dict[str, Any], new: dict[str, Any]) -> list[dict[str, Any]]:
    """Compute field-level changes between two entity dicts."""

    changes: list[dict[str, Any]] = []
    all_keys = sorted(set(list(old.keys()) + list(new.keys())))

    for key in all_keys:
        old_val = _strip_nested_sort_order(old.get(key))
        new_val = _strip_nested_sort_order(new.get(key))
        old_str = json.dumps(old_val, sort_keys=True, default=str)
        new_str = json.dumps(new_val, sort_keys=True, default=str)

        if old_str != new_str:
            changes.append({"field": key, "old": old_val, "new": new_val})

    return changes
