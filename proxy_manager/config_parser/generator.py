"""
HAProxy configuration generator
================================

Generates valid HAProxy configuration text from database models.
"""

from proxy_manager.database.models.acl_rule import AclRule
from proxy_manager.database.models.backend import Backend, BackendServer
from proxy_manager.database.models.cache import CacheSection
from proxy_manager.database.models.default_setting import DefaultSetting
from proxy_manager.database.models.frontend import Frontend, FrontendBind, FrontendOption
from proxy_manager.database.models.global_setting import GlobalSetting
from proxy_manager.database.models.http_errors import HttpErrorEntry, HttpErrorsSection
from proxy_manager.database.models.listen_block import ListenBlock, ListenBlockBind
from proxy_manager.database.models.mailer import MailerEntry, MailerSection
from proxy_manager.database.models.peer import PeerEntry, PeerSection
from proxy_manager.database.models.resolver import Resolver, ResolverNameserver
from proxy_manager.database.models.userlist import Userlist, UserlistEntry

_INDENT = '    '


def generate_config(
    *,
    global_settings: list[GlobalSetting],
    default_settings: list[DefaultSetting],
    listen_blocks: list[tuple[ListenBlock, list[ListenBlockBind]]],
    userlists: list[tuple[Userlist, list[UserlistEntry]]],
    frontends: list[tuple[Frontend, list[FrontendBind], list[FrontendOption], list[AclRule]]],
    backends: list[tuple[Backend, list[BackendServer]]],
    resolvers: list[tuple[Resolver, list[ResolverNameserver]]] | None = None,
    peers: list[tuple[PeerSection, list[PeerEntry]]] | None = None,
    mailers: list[tuple[MailerSection, list[MailerEntry]]] | None = None,
    http_errors: list[tuple[HttpErrorsSection, list[HttpErrorEntry]]] | None = None,
    caches: list[CacheSection] | None = None,
) -> str:
    """Generate HAProxy config text from database models."""

    parts: list[str] = []

    def _emit_settings_section(name: str, settings: list[GlobalSetting] | list[DefaultSetting]) -> None:
        """Emit a global/defaults settings block."""

        if not settings:
            return

        parts.append(name)
        for s in settings:
            line = f'{_INDENT}{s.directive}'

            if s.value:
                line += f' {s.value}'

            if s.comment:
                first_comment_line = s.comment.split('\n')[0]
                line += f'  # {first_comment_line}'

            parts.append(line)

        parts.append('')

    _emit_settings_section('global', global_settings)
    _emit_settings_section('defaults', default_settings)

    # Listen blocks
    for lb, lb_binds in listen_blocks:
        parts.append(f'listen {lb.name}')

        if lb.comment:
            for cl in lb.comment.splitlines():
                parts.append(f'{_INDENT}# {cl}')

        for b in lb_binds:
            parts.append(f'{_INDENT}bind {b.bind_line}')

        if lb.mode:
            parts.append(f'{_INDENT}mode {lb.mode}')

        if lb.balance:
            parts.append(f'{_INDENT}balance {lb.balance}')

        if lb.maxconn is not None:
            parts.append(f'{_INDENT}maxconn {lb.maxconn}')

        if lb.timeout_client:
            parts.append(f'{_INDENT}timeout client {lb.timeout_client}')

        if lb.timeout_server:
            parts.append(f'{_INDENT}timeout server {lb.timeout_server}')

        if lb.timeout_connect:
            parts.append(f'{_INDENT}timeout connect {lb.timeout_connect}')

        if lb.default_server_params:
            parts.append(f'{_INDENT}default-server {lb.default_server_params}')

        if lb.option_httplog:
            parts.append(f'{_INDENT}option httplog')

        if lb.option_tcplog:
            parts.append(f'{_INDENT}option tcplog')

        if lb.option_forwardfor:
            parts.append(f'{_INDENT}option forwardfor')

        if lb.content:
            for cl in lb.content.splitlines():
                parts.append(f'{_INDENT}{cl}')
        parts.append('')

    # Userlists
    for ul, entries in userlists:
        parts.append(f'userlist {ul.name}')

        for e in entries:
            parts.append(f'{_INDENT}user {e.username} password {e.password_hash}')
        parts.append('')

    # Frontends
    for fe, binds, options, acls in frontends:
        parts.append(f'frontend {fe.name}')

        if fe.comment:
            for cl in fe.comment.splitlines():
                parts.append(f'{_INDENT}# {cl}')

        for b in binds:
            parts.append(f'{_INDENT}bind {b.bind_line}')

        if fe.mode:
            parts.append(f'{_INDENT}mode {fe.mode}')

        if fe.maxconn is not None:
            parts.append(f'{_INDENT}maxconn {fe.maxconn}')

        if fe.default_backend:
            parts.append(f'{_INDENT}default_backend {fe.default_backend}')

        if fe.timeout_client:
            parts.append(f'{_INDENT}timeout client {fe.timeout_client}')

        if fe.timeout_http_request:
            parts.append(f'{_INDENT}timeout http-request {fe.timeout_http_request}')

        if fe.timeout_http_keep_alive:
            parts.append(f'{_INDENT}timeout http-keep-alive {fe.timeout_http_keep_alive}')

        if fe.option_httplog:
            parts.append(f'{_INDENT}option httplog')

        if fe.option_tcplog:
            parts.append(f'{_INDENT}option tcplog')

        if fe.option_forwardfor:
            parts.append(f'{_INDENT}option forwardfor')

        if fe.compression_algo:
            parts.append(f'{_INDENT}compression algo {fe.compression_algo}')

        if fe.compression_type:
            parts.append(f'{_INDENT}compression type {fe.compression_type}')

        # Options (headers, DDoS, etc.)
        for opt in options:
            line = f'{_INDENT}{opt.directive}'

            if opt.value:
                line += f' {opt.value}'

            if opt.comment:
                first_comment_line = opt.comment.split('\n')[0]
                line += f'  # {first_comment_line}'
            parts.append(line)

        # ACL rules
        if acls:
            parts.append('')

        for acl in acls:
            if not acl.enabled:
                parts.append(f'{_INDENT}# DISABLED:')

            if acl.comment:
                for cl in acl.comment.splitlines():
                    parts.append(f'{_INDENT}# {cl}')

            acl_name = f'ACL_{acl.domain.replace(".", "_").replace("-", "_")}'
            match_fn = f'{acl.acl_match_type}(Host)'
            prefix = f'{_INDENT}#' if not acl.enabled else _INDENT

            parts.append(f'{prefix}acl {acl_name} {match_fn} -i {acl.domain}')
            if acl.is_redirect and acl.redirect_target:
                parts.append(f'{prefix}redirect prefix {acl.redirect_target} code {acl.redirect_code} if {acl_name}')
            else:
                parts.append(f'{prefix}use_backend {acl.backend_name} if {acl_name}')
            parts.append('')

        parts.append('')

    # Backends
    for be, servers in backends:
        parts.append(f'backend {be.name}')

        if be.comment:
            for cl in be.comment.splitlines():
                parts.append(f'{_INDENT}# {cl}')

        if be.mode:
            parts.append(f'{_INDENT}mode {be.mode}')

        if be.auth_userlist:
            parts.append(f'{_INDENT}acl authorized http_auth({be.auth_userlist})')
            parts.append(f'{_INDENT}http-request auth realm Login unless authorized')

        if be.health_check_enabled:
            parts.append(f'{_INDENT}option httpchk')
            if be.health_check_method and be.health_check_uri:
                parts.append(f'{_INDENT}http-check send meth {be.health_check_method} uri {be.health_check_uri}')

            if be.http_check_expect:
                parts.append(f'{_INDENT}http-check expect {be.http_check_expect}')

        if be.option_forwardfor:
            parts.append(f'{_INDENT}option forwardfor')

        if be.option_httplog:
            parts.append(f'{_INDENT}option httplog')

        if be.option_tcplog:
            parts.append(f'{_INDENT}option tcplog')

        if be.balance:
            parts.append(f'{_INDENT}balance {be.balance}')

        if be.hash_type:
            parts.append(f'{_INDENT}hash-type {be.hash_type}')

        if be.cookie:
            parts.append(f'{_INDENT}cookie {be.cookie}')

        if be.http_reuse:
            parts.append(f'{_INDENT}http-reuse {be.http_reuse}')

        if be.retry_on:
            parts.append(f'{_INDENT}retry-on {be.retry_on}')

        if be.option_redispatch:
            parts.append(f'{_INDENT}option redispatch 1')

        if be.retries is not None:
            parts.append(f'{_INDENT}retries {be.retries}')

        if be.timeout_server:
            parts.append(f'{_INDENT}timeout server {be.timeout_server}')

        if be.timeout_connect:
            parts.append(f'{_INDENT}timeout connect {be.timeout_connect}')

        if be.timeout_queue:
            parts.append(f'{_INDENT}timeout queue {be.timeout_queue}')

        if be.compression_algo:
            parts.append(f'{_INDENT}compression algo {be.compression_algo}')

        if be.compression_type:
            parts.append(f'{_INDENT}compression type {be.compression_type}')

        if be.default_server_options:
            parts.append(f'{_INDENT}default-server {be.default_server_options}')

        if be.extra_options:
            for ol in be.extra_options.splitlines():
                parts.append(f'{_INDENT}{ol}')

        for srv in servers:
            line = f'{_INDENT}server {srv.name} {srv.address}:{srv.port}'

            if srv.weight is not None:
                line += f' weight {srv.weight}'

            if srv.cookie_value:
                line += f' cookie {srv.cookie_value}'

            if srv.maxconn is not None:
                line += f' maxconn {srv.maxconn}'

            if srv.maxqueue is not None:
                line += f' maxqueue {srv.maxqueue}'

            if srv.ssl_enabled:
                line += ' ssl'

            if srv.ssl_verify:
                line += f' verify {srv.ssl_verify}'

            if srv.check_enabled:
                line += ' check'

            if srv.inter:
                line += f' inter {srv.inter}'

            if srv.fastinter:
                line += f' fastinter {srv.fastinter}'

            if srv.downinter:
                line += f' downinter {srv.downinter}'

            if srv.rise is not None:
                line += f' rise {srv.rise}'

            if srv.fall is not None:
                line += f' fall {srv.fall}'

            if srv.slowstart:
                line += f' slowstart {srv.slowstart}'

            if srv.backup:
                line += ' backup'

            if srv.send_proxy_v2:
                line += ' send-proxy-v2'
            elif srv.send_proxy:
                line += ' send-proxy'

            if srv.resolvers_ref:
                line += f' resolvers {srv.resolvers_ref}'

            if srv.resolve_prefer:
                line += f' resolve-prefer {srv.resolve_prefer}'

            if srv.on_marked_down:
                line += f' on-marked-down {srv.on_marked_down}'

            if srv.disabled:
                line += ' disabled'

            if srv.extra_params:
                line += f' {srv.extra_params}'

            parts.append(line)

        if be.errorfile:
            parts.append(f'{_INDENT}errorfile {be.errorfile}')

        parts.append('')

    # Resolvers
    for res, nameservers in resolvers or []:
        parts.append(f'resolvers {res.name}')

        if res.comment:
            for cl in res.comment.splitlines():
                parts.append(f'{_INDENT}# {cl}')

        if res.parse_resolv_conf:
            parts.append(f'{_INDENT}parse-resolv-conf')

        for ns in nameservers:
            parts.append(f'{_INDENT}nameserver {ns.name} {ns.address}:{ns.port}')

        if res.resolve_retries is not None:
            parts.append(f'{_INDENT}resolve_retries {res.resolve_retries}')

        if res.timeout_resolve:
            parts.append(f'{_INDENT}timeout resolve {res.timeout_resolve}')

        if res.timeout_retry:
            parts.append(f'{_INDENT}timeout retry {res.timeout_retry}')

        for hold_name in ('valid', 'other', 'refused', 'timeout', 'obsolete', 'nx', 'aa'):
            val = getattr(res, f'hold_{hold_name}', None)
            if val:
                parts.append(f'{_INDENT}hold {hold_name} {val}')

        if res.accepted_payload_size is not None:
            parts.append(f'{_INDENT}accepted_payload_size {res.accepted_payload_size}')

        if res.extra_options:
            for ol in res.extra_options.splitlines():
                parts.append(f'{_INDENT}{ol}')

        parts.append('')

    # Peers
    for ps, entries in peers or []:
        parts.append(f'peers {ps.name}')

        if ps.comment:
            for cl in ps.comment.splitlines():
                parts.append(f'{_INDENT}# {cl}')

        if ps.default_bind:
            parts.append(f'{_INDENT}bind {ps.default_bind}')

        if ps.default_server_options:
            parts.append(f'{_INDENT}default-server {ps.default_server_options}')

        for e in entries:
            parts.append(f'{_INDENT}peer {e.name} {e.address}:{e.port}')

        if ps.extra_options:
            for ol in ps.extra_options.splitlines():
                parts.append(f'{_INDENT}{ol}')
        parts.append('')

    # Mailers
    for ms, entries in mailers or []:
        parts.append(f'mailers {ms.name}')

        if ms.comment:
            for cl in ms.comment.splitlines():
                parts.append(f'{_INDENT}# {cl}')

        if ms.timeout_mail:
            parts.append(f'{_INDENT}timeout mail {ms.timeout_mail}')

        for e in entries:
            parts.append(f'{_INDENT}mailer {e.name} {e.address}:{e.port}')
            if getattr(e, 'smtp_auth', False):
                user = getattr(e, 'smtp_user', '') or ''
                pwd = getattr(e, 'smtp_password', '') or ''
                tls = getattr(e, 'use_tls', False)
                starttls = getattr(e, 'use_starttls', False)
                parts.append(
                    f'{_INDENT}# _pm_mailer_auth {e.name} smtp_auth=true smtp_user={user} smtp_password={pwd} use_tls={str(tls).lower()} use_starttls={str(starttls).lower()}'
                )

        if ms.extra_options:
            for ol in ms.extra_options.splitlines():
                parts.append(f'{_INDENT}{ol}')

        parts.append('')

    # HTTP Errors
    for he_sec, entries in http_errors or []:
        parts.append(f'http-errors {he_sec.name}')

        if he_sec.comment:
            for cl in he_sec.comment.splitlines():
                parts.append(f'{_INDENT}# {cl}')

        for e in entries:
            parts.append(f'{_INDENT}{e.type} {e.status_code} {e.value}')

        if he_sec.extra_options:
            for ol in he_sec.extra_options.splitlines():
                parts.append(f'{_INDENT}{ol}')
        parts.append('')

    # Cache
    for c in caches or []:
        parts.append(f'cache {c.name}')

        if c.comment:
            for cl in c.comment.splitlines():
                parts.append(f'{_INDENT}# {cl}')

        if c.total_max_size is not None:
            parts.append(f'{_INDENT}total-max-size {c.total_max_size}')

        if c.max_object_size is not None:
            parts.append(f'{_INDENT}max-object-size {c.max_object_size}')

        if c.max_age is not None:
            parts.append(f'{_INDENT}max-age {c.max_age}')

        if c.max_secondary_entries is not None:
            parts.append(f'{_INDENT}max-secondary-entries {c.max_secondary_entries}')

        if c.process_vary is not None:
            parts.append(f'{_INDENT}process-vary {c.process_vary}')

        if c.extra_options:
            for ol in c.extra_options.splitlines():
                parts.append(f'{_INDENT}{ol}')

        parts.append('')

    return '\n'.join(parts)
