"""
Config generator tests
======================

Comprehensive tests for `generate_config` and round-trip verification.
"""

from typing import Any
from unittest.mock import MagicMock

from proxy_manager.config_parser.generator import generate_config
from proxy_manager.config_parser.parser import parse_config
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


def _empty_gen(**overrides: Any) -> str:
    """Call `generate_config` with all-empty defaults, overridden by *overrides*."""

    defaults: dict[str, Any] = {
        "global_settings": [],
        "default_settings": [],
        "listen_blocks": [],
        "userlists": [],
        "frontends": [],
        "backends": [],
        "resolvers": [],
        "peers": [],
        "mailers": [],
        "http_errors": [],
        "caches": [],
    }
    defaults.update(overrides)

    return generate_config(**defaults)


def _mock(spec: type, **attrs: Any) -> MagicMock:
    """Create a `MagicMock` with the given *spec* and attributes.

    All non-overridden attributes default to `None` (or `False` for booleans).
    """

    m = MagicMock(spec=spec)

    # Reset all mapped-column attributes to None/False
    for col in getattr(spec, "__table__", MagicMock()).columns:  # pyright: ignore[reportAttributeAccessIssue]
        col_type = str(col.type)
        if "BOOLEAN" in col_type:
            setattr(m, col.name, False)
        elif "INTEGER" in col_type:
            setattr(m, col.name, None)
        else:
            setattr(m, col.name, None)

    # Apply explicit overrides
    for k, v in attrs.items():
        setattr(m, k, v)
    return m


def test_empty_config() -> None:
    """Empty inputs produce an empty string."""

    result = _empty_gen()
    assert result.strip() == ""


def test_global_settings() -> None:
    """Global settings section is emitted."""

    gs1 = _mock(GlobalSetting, directive="log", value="127.0.0.1 local0", comment=None)
    gs2 = _mock(GlobalSetting, directive="maxconn", value="4096", comment=None)

    result = _empty_gen(global_settings=[gs1, gs2])
    assert "global" in result
    assert "log 127.0.0.1 local0" in result
    assert "maxconn 4096" in result


def test_global_with_comment() -> None:
    """Comment is emitted after `#`."""

    gs = _mock(GlobalSetting, directive="maxconn", value="4096", comment="max conns")
    result = _empty_gen(global_settings=[gs])

    assert "# max conns" in result


def test_global_no_value() -> None:
    """Directive without value (e.g. `daemon`)."""

    gs = _mock(GlobalSetting, directive="daemon", value="", comment=None)
    result = _empty_gen(global_settings=[gs])
    assert "daemon" in result


def test_default_settings() -> None:
    """Defaults section is emitted."""

    ds1 = _mock(DefaultSetting, directive="mode", value="http", comment=None)
    ds2 = _mock(DefaultSetting, directive="timeout connect", value="5000", comment=None)

    result = _empty_gen(default_settings=[ds1, ds2])
    assert "defaults" in result
    assert "mode http" in result
    assert "timeout connect 5000" in result


def test_frontend_basic() -> None:
    """Basic frontend with bind and mode."""

    fe = _mock(
        Frontend,
        name="fe_http",
        mode="http",
        default_backend="be_web",
    )
    bind = _mock(FrontendBind, bind_line="*:80")

    result = _empty_gen(frontends=[(fe, [bind], [], [])])
    assert "frontend fe_http" in result
    assert "bind *:80" in result
    assert "mode http" in result
    assert "default_backend be_web" in result


def test_frontend_with_options() -> None:
    """Frontend options are emitted."""
    fe = _mock(Frontend, name="fe", mode="http", default_backend="be")
    bind = _mock(FrontendBind, bind_line="*:80")
    opt = _mock(FrontendOption, directive="http-request", value="set-header X-A val", comment=None)

    result = _empty_gen(frontends=[(fe, [bind], [opt], [])])
    assert "http-request set-header X-A val" in result


def test_frontend_option_with_comment() -> None:
    """Frontend option comment is appended."""

    fe = _mock(Frontend, name="fe", mode="http", default_backend="be")
    bind = _mock(FrontendBind, bind_line="*:80")
    opt = _mock(FrontendOption, directive="http-request", value="deny", comment="Block bad")

    result = _empty_gen(frontends=[(fe, [bind], [opt], [])])
    assert "# Block bad" in result


def test_frontend_acl_use_backend() -> None:
    """ACL + `use_backend` is emitted."""

    fe = _mock(Frontend, name="fe", mode="http", default_backend="be")
    bind = _mock(FrontendBind, bind_line="*:80")
    acl = _mock(
        AclRule,
        domain="example.com",
        backend_name="be_example",
        acl_match_type="hdr",
        is_redirect=False,
        redirect_target=None,
        redirect_code=None,
        comment=None,
        enabled=True,
    )

    result = _empty_gen(frontends=[(fe, [bind], [], [acl])])
    assert "acl ACL_example_com hdr(Host) -i example.com" in result
    assert "use_backend be_example if ACL_example_com" in result


def test_frontend_acl_redirect() -> None:
    """ACL redirect is emitted."""

    fe = _mock(Frontend, name="fe", mode="http", default_backend="be")
    bind = _mock(FrontendBind, bind_line="*:80")
    acl = _mock(
        AclRule,
        domain="old.com",
        backend_name=None,
        acl_match_type="hdr",
        is_redirect=True,
        redirect_target="https://new.com",
        redirect_code=301,
        comment=None,
        enabled=True,
    )

    result = _empty_gen(frontends=[(fe, [bind], [], [acl])])
    assert "redirect prefix https://new.com code 301" in result


def test_frontend_acl_disabled() -> None:
    """Disabled ACL is commented out."""

    fe = _mock(Frontend, name="fe", mode="http", default_backend="be")
    bind = _mock(FrontendBind, bind_line="*:80")
    acl = _mock(
        AclRule,
        domain="disabled.com",
        backend_name="be_x",
        acl_match_type="hdr",
        is_redirect=False,
        redirect_target=None,
        redirect_code=None,
        comment=None,
        enabled=False,
    )

    result = _empty_gen(frontends=[(fe, [bind], [], [acl])])
    assert "# DISABLED:" in result
    assert "#acl ACL_disabled_com" in result
    assert "#use_backend be_x" in result


def test_frontend_acl_redirect_disabled() -> None:
    """Disabled redirect ACL is commented out."""

    fe = _mock(Frontend, name="fe", mode="http", default_backend="be")
    bind = _mock(FrontendBind, bind_line="*:80")
    acl = _mock(
        AclRule,
        domain="old.com",
        backend_name=None,
        acl_match_type="hdr",
        is_redirect=True,
        redirect_target="https://new.com",
        redirect_code=301,
        comment=None,
        enabled=False,
    )

    result = _empty_gen(frontends=[(fe, [bind], [], [acl])])
    assert "# DISABLED:" in result
    assert "#redirect prefix https://new.com" in result


def test_frontend_timeout_fields() -> None:
    """Frontend timeout fields are emitted."""

    fe = _mock(
        Frontend,
        name="fe",
        mode="http",
        default_backend="be",
        timeout_client="30s",
        timeout_http_request="10s",
        timeout_http_keep_alive="5s",
    )

    bind = _mock(FrontendBind, bind_line="*:80")
    result = _empty_gen(frontends=[(fe, [bind], [], [])])
    assert "timeout client 30s" in result
    assert "timeout http-request 10s" in result
    assert "timeout http-keep-alive 5s" in result


def test_frontend_maxconn() -> None:
    """Frontend maxconn is emitted."""

    fe = _mock(Frontend, name="fe", mode="http", default_backend="be", maxconn=10000)
    bind = _mock(FrontendBind, bind_line="*:80")
    result = _empty_gen(frontends=[(fe, [bind], [], [])])
    assert "maxconn 10000" in result


def test_frontend_option_flags() -> None:
    """Frontend option flags (httplog, tcplog, forwardfor) are emitted."""

    fe = _mock(
        Frontend,
        name="fe",
        mode="http",
        default_backend="be",
        option_httplog=True,
        option_tcplog=True,
        option_forwardfor=True,
    )
    bind = _mock(FrontendBind, bind_line="*:80")

    result = _empty_gen(frontends=[(fe, [bind], [], [])])
    assert "option httplog" in result
    assert "option tcplog" in result
    assert "option forwardfor" in result


def test_frontend_compression() -> None:
    """Frontend compression fields are emitted."""

    fe = _mock(
        Frontend,
        name="fe",
        mode="http",
        default_backend="be",
        compression_algo="gzip",
        compression_type="text/html text/css",
    )

    bind = _mock(FrontendBind, bind_line="*:80")
    result = _empty_gen(frontends=[(fe, [bind], [], [])])
    assert "compression algo gzip" in result
    assert "compression type text/html text/css" in result


def test_gen_frontend_option_tcplog() -> None:
    """`option tcplog` in generated frontend."""

    fe = _mock(Frontend, name="fe", mode="tcp", default_backend="be", option_tcplog=True)
    bind = _mock(FrontendBind, bind_line="*:3306")
    result = _empty_gen(frontends=[(fe, [bind], [], [])])
    assert "option tcplog" in result


def test_backend_basic() -> None:
    """Basic backend with a server."""

    be = _mock(Backend, name="be_web", mode="http", balance="roundrobin")
    srv = _mock(BackendServer, name="s1", address="10.0.0.1", port=80, check_enabled=True)

    result = _empty_gen(backends=[(be, [srv])])
    assert "backend be_web" in result
    assert "mode http" in result
    assert "balance roundrobin" in result
    assert "server s1 10.0.0.1:80" in result
    assert "check" in result


def test_backend_comment() -> None:
    """Backend comment is emitted before the section."""

    be = _mock(Backend, name="be", mode="http", comment="Main backend")
    srv = _mock(BackendServer, name="s1", address="10.0.0.1", port=80)

    result = _empty_gen(backends=[(be, [srv])])
    assert "# Main backend" in result


def test_backend_health_check() -> None:
    """Health check directives are emitted."""

    be = _mock(
        Backend,
        name="be",
        mode="http",
        health_check_enabled=True,
        health_check_method="GET",
        health_check_uri="/health",
    )
    srv = _mock(BackendServer, name="s1", address="10.0.0.1", port=80)

    result = _empty_gen(backends=[(be, [srv])])
    assert "option httpchk" in result
    assert "http-check send meth GET uri /health" in result


def test_backend_http_check_expect() -> None:
    """`http-check expect` is emitted."""

    be = _mock(Backend, name="be", mode="http", http_check_expect="status 200")
    srv = _mock(BackendServer, name="s1", address="10.0.0.1", port=80)

    result = _empty_gen(backends=[(be, [srv])])
    assert "http-check expect status 200" in result


def test_backend_cookie() -> None:
    """`cookie` directive is emitted."""

    be = _mock(Backend, name="be", mode="http", cookie="SRVID insert indirect nocache")
    srv = _mock(BackendServer, name="s1", address="10.0.0.1", port=80)

    result = _empty_gen(backends=[(be, [srv])])
    assert "cookie SRVID insert indirect nocache" in result


def test_backend_timeouts() -> None:
    """Backend timeout fields are emitted."""

    be = _mock(
        Backend,
        name="be",
        mode="http",
        timeout_server="30s",
        timeout_connect="5s",
        timeout_queue="60s",
    )
    srv = _mock(BackendServer, name="s1", address="10.0.0.1", port=80)

    result = _empty_gen(backends=[(be, [srv])])
    assert "timeout server 30s" in result
    assert "timeout connect 5s" in result
    assert "timeout queue 60s" in result


def test_backend_default_server_options() -> None:
    """`default-server` directive is emitted."""

    be = _mock(Backend, name="be", mode="http", default_server_options="inter 3s fall 3 rise 2")
    srv = _mock(BackendServer, name="s1", address="10.0.0.1", port=80)

    result = _empty_gen(backends=[(be, [srv])])
    assert "default-server inter 3s fall 3 rise 2" in result


def test_backend_http_reuse_hash_type() -> None:
    """`http-reuse` and `hash-type` are emitted."""

    be = _mock(Backend, name="be", mode="http", http_reuse="aggressive", hash_type="consistent sdbm")
    srv = _mock(BackendServer, name="s1", address="10.0.0.1", port=80)

    result = _empty_gen(backends=[(be, [srv])])
    assert "http-reuse aggressive" in result
    assert "hash-type consistent sdbm" in result


def test_backend_compression() -> None:
    """Backend compression fields are emitted."""

    be = _mock(
        Backend,
        name="be",
        mode="http",
        compression_algo="gzip deflate",
        compression_type="text/html text/css",
    )
    srv = _mock(BackendServer, name="s1", address="10.0.0.1", port=80)

    result = _empty_gen(backends=[(be, [srv])])
    assert "compression algo gzip deflate" in result
    assert "compression type text/html text/css" in result


def test_backend_option_flags() -> None:
    """Backend option flags (forwardfor, httplog, tcplog) are emitted."""

    be = _mock(
        Backend,
        name="be",
        mode="http",
        option_forwardfor=True,
        option_httplog=True,
        option_tcplog=True,
    )
    srv = _mock(BackendServer, name="s1", address="10.0.0.1", port=80)

    result = _empty_gen(backends=[(be, [srv])])
    assert "option forwardfor" in result
    assert "option httplog" in result
    assert "option tcplog" in result


def test_backend_retry_redispatch() -> None:
    """`retry-on`, `option redispatch`, `retries` are emitted."""

    be = _mock(
        Backend,
        name="be",
        mode="http",
        retry_on="conn-failure empty-response",
        option_redispatch=True,
        retries=3,
    )
    srv = _mock(BackendServer, name="s1", address="10.0.0.1", port=80)

    result = _empty_gen(backends=[(be, [srv])])
    assert "retry-on conn-failure empty-response" in result
    assert "option redispatch 1" in result
    assert "retries 3" in result


def test_backend_errorfile() -> None:
    """`errorfile` directive is emitted."""

    be = _mock(Backend, name="be", mode="http", errorfile="503 /errors/503.http")
    srv = _mock(BackendServer, name="s1", address="10.0.0.1", port=80)

    result = _empty_gen(backends=[(be, [srv])])
    assert "errorfile 503 /errors/503.http" in result


def test_backend_extra_options() -> None:
    """`extra_options` is emitted as-is."""

    be = _mock(Backend, name="be", mode="http", extra_options="stick on src\nstick-table type ip size 1m")
    srv = _mock(BackendServer, name="s1", address="10.0.0.1", port=80)

    result = _empty_gen(backends=[(be, [srv])])
    assert "stick on src" in result
    assert "stick-table type ip size 1m" in result


def test_backend_auth_userlist() -> None:
    """`acl authorized http_auth(...)` is emitted."""

    be = _mock(Backend, name="be", mode="http", auth_userlist="admins")
    srv = _mock(BackendServer, name="s1", address="10.0.0.1", port=80)

    result = _empty_gen(backends=[(be, [srv])])
    assert "acl authorized http_auth(admins)" in result
    assert "http-request auth realm Login unless authorized" in result


def test_gen_backend_option_tcplog() -> None:
    """`option tcplog` in generated backend."""

    be = _mock(Backend, name="be", mode="tcp", option_tcplog=True)
    srv = _mock(BackendServer, name="s1", address="10.0.0.1", port=80)

    result = _empty_gen(backends=[(be, [srv])])
    assert "option tcplog" in result


def test_server_all_fields() -> None:
    """Server with all tier-1/2 fields."""

    be = _mock(Backend, name="be", mode="http")
    srv = _mock(
        BackendServer,
        name="s1",
        address="10.0.0.1",
        port=80,
        weight=50,
        cookie_value="srv1",
        maxconn=100,
        maxqueue=50,
        ssl_enabled=True,
        ssl_verify="none",
        check_enabled=True,
        inter="3s",
        fastinter="1s",
        downinter="5s",
        rise=2,
        fall=3,
        slowstart="60s",
        backup=True,
        send_proxy=False,
        send_proxy_v2=True,
        resolvers_ref="mydns",
        resolve_prefer="ipv4",
        on_marked_down="shutdown-sessions",
        disabled=True,
        extra_params=None,
    )

    result = _empty_gen(backends=[(be, [srv])])
    line = [ln for ln in result.splitlines() if "server s1" in ln][0]
    assert "weight 50" in line
    assert "cookie srv1" in line
    assert "maxconn 100" in line
    assert "maxqueue 50" in line
    assert "ssl" in line
    assert "verify none" in line
    assert "check" in line
    assert "inter 3s" in line
    assert "fastinter 1s" in line
    assert "downinter 5s" in line
    assert "rise 2" in line
    assert "fall 3" in line
    assert "slowstart 60s" in line
    assert "backup" in line
    assert "send-proxy-v2" in line
    assert "send-proxy " not in line  # v2 takes precedence
    assert "resolvers mydns" in line
    assert "resolve-prefer ipv4" in line
    assert "on-marked-down shutdown-sessions" in line
    assert "disabled" in line


def test_server_send_proxy_v1() -> None:
    """`send-proxy` (v1) is emitted when v2 is False."""

    be = _mock(Backend, name="be", mode="http")
    srv = _mock(
        BackendServer,
        name="s1",
        address="10.0.0.1",
        port=80,
        send_proxy=True,
        send_proxy_v2=False,
    )

    result = _empty_gen(backends=[(be, [srv])])
    line = [ln for ln in result.splitlines() if "server s1" in ln][0]
    assert "send-proxy" in line
    assert "send-proxy-v2" not in line


def test_server_extra_params() -> None:
    """`extra_params` appended to server line."""

    be = _mock(Backend, name="be", mode="http")
    srv = _mock(
        BackendServer,
        name="s1",
        address="10.0.0.1",
        port=80,
        extra_params="ca-file /etc/ssl/ca.pem sni str(example.com)",
    )

    result = _empty_gen(backends=[(be, [srv])])
    line = [ln for ln in result.splitlines() if "server s1" in ln][0]
    assert "ca-file /etc/ssl/ca.pem sni str(example.com)" in line


def test_server_maxconn_maxqueue() -> None:
    """`maxconn` and `maxqueue` are emitted."""

    be = _mock(Backend, name="be", mode="http")
    srv = _mock(BackendServer, name="s1", address="10.0.0.1", port=80, maxconn=200, maxqueue=100)

    result = _empty_gen(backends=[(be, [srv])])
    line = [ln for ln in result.splitlines() if "server s1" in ln][0]
    assert "maxconn 200" in line
    assert "maxqueue 100" in line


def test_server_downinter_fastinter() -> None:
    """`downinter` and `fastinter` are emitted."""

    be = _mock(Backend, name="be", mode="http")
    srv = _mock(
        BackendServer,
        name="s1",
        address="10.0.0.1",
        port=80,
        check_enabled=True,
        inter="3s",
        fastinter="1s",
        downinter="5s",
    )

    result = _empty_gen(backends=[(be, [srv])])
    line = [ln for ln in result.splitlines() if "server s1" in ln][0]
    assert "inter 3s" in line
    assert "fastinter 1s" in line
    assert "downinter 5s" in line


def test_listen_basic() -> None:
    """Basic listen block."""

    lb = _mock(
        ListenBlock,
        name="stats",
        mode="http",
        content="stats enable\nstats uri /stats",
    )
    lb_bind = _mock(ListenBlockBind, bind_line="*:8404")

    result = _empty_gen(listen_blocks=[(lb, [lb_bind])])
    assert "listen stats" in result
    assert "bind *:8404" in result
    assert "mode http" in result
    assert "stats enable" in result
    assert "stats uri /stats" in result


def test_listen_all_fields() -> None:
    """Listen block with all expanded fields."""

    lb = _mock(
        ListenBlock,
        name="myproxy",
        mode="tcp",
        balance="roundrobin",
        maxconn=2000,
        timeout_client="30s",
        timeout_server="60s",
        timeout_connect="5s",
        default_server_params="inter 3s fall 3 rise 2",
        option_httplog=False,
        option_tcplog=True,
        option_forwardfor=True,
        content="server db1 10.0.0.1:3306 check",
    )
    lb_bind = _mock(ListenBlockBind, bind_line="*:3306")

    result = _empty_gen(listen_blocks=[(lb, [lb_bind])])
    assert "listen myproxy" in result
    assert "mode tcp" in result
    assert "balance roundrobin" in result
    assert "maxconn 2000" in result
    assert "timeout client 30s" in result
    assert "timeout server 60s" in result
    assert "timeout connect 5s" in result
    assert "default-server inter 3s fall 3 rise 2" in result
    assert "option tcplog" in result
    assert "option forwardfor" in result
    assert "option httplog" not in result
    assert "server db1 10.0.0.1:3306 check" in result


def test_userlist_basic() -> None:
    """Basic userlist."""

    ul = _mock(Userlist, name="admins")
    entry = _mock(UserlistEntry, username="admin", password_hash="$6$hash")

    result = _empty_gen(userlists=[(ul, [entry])])
    assert "userlist admins" in result
    assert "user admin password $6$hash" in result


def test_resolver_basic() -> None:
    """Basic resolver section."""

    res = _mock(
        Resolver,
        name="mydns",
        resolve_retries=3,
        timeout_resolve="1s",
        timeout_retry="1s",
        parse_resolv_conf=None,
        accepted_payload_size=None,
        extra_options=None,
    )

    # Reset hold_ fields
    for hold in ("valid", "other", "refused", "timeout", "obsolete", "nx", "aa"):
        setattr(res, f"hold_{hold}", None)

    ns = _mock(ResolverNameserver, name="dns1", address="8.8.8.8", port=53)

    result = _empty_gen(resolvers=[(res, [ns])])
    assert "resolvers mydns" in result
    assert "nameserver dns1 8.8.8.8:53" in result
    assert "resolve_retries 3" in result
    assert "timeout resolve 1s" in result


def test_resolver_hold_timers() -> None:
    """Resolver hold timers are emitted."""

    res = _mock(
        Resolver,
        name="dns",
        resolve_retries=None,
        timeout_resolve=None,
        timeout_retry=None,
        parse_resolv_conf=None,
        accepted_payload_size=None,
        extra_options=None,
        hold_valid="10s",
        hold_other="30s",
        hold_refused="30s",
        hold_timeout="30s",
        hold_obsolete="30s",
        hold_nx="60s",
        hold_aa="5s",
    )
    ns = _mock(ResolverNameserver, name="dns1", address="8.8.8.8", port=53)

    result = _empty_gen(resolvers=[(res, [ns])])
    assert "hold valid 10s" in result
    assert "hold other 30s" in result
    assert "hold nx 60s" in result


def test_resolver_parse_resolv_conf() -> None:
    """`parse-resolv-conf` is emitted."""

    res = _mock(
        Resolver,
        name="dns",
        parse_resolv_conf=1,
        resolve_retries=None,
        timeout_resolve=None,
        timeout_retry=None,
        accepted_payload_size=None,
        extra_options=None,
    )

    for hold in ("valid", "other", "refused", "timeout", "obsolete", "nx", "aa"):
        setattr(res, f"hold_{hold}", None)

    ns = _mock(ResolverNameserver, name="dns1", address="8.8.8.8", port=53)

    result = _empty_gen(resolvers=[(res, [ns])])
    assert "parse-resolv-conf" in result


def test_resolver_extra_options() -> None:
    """Resolver `extra_options` are emitted."""

    res = _mock(
        Resolver,
        name="dns",
        resolve_retries=None,
        timeout_resolve=None,
        timeout_retry=None,
        parse_resolv_conf=None,
        accepted_payload_size=None,
        extra_options="some-future-directive value",
    )

    for hold in ("valid", "other", "refused", "timeout", "obsolete", "nx", "aa"):
        setattr(res, f"hold_{hold}", None)

    ns = _mock(ResolverNameserver, name="dns1", address="8.8.8.8", port=53)

    result = _empty_gen(resolvers=[(res, [ns])])
    assert "some-future-directive value" in result


def test_peer_basic() -> None:
    """Basic peer section."""

    ps = _mock(PeerSection, name="mypeers", default_bind=None, default_server_options=None, extra_options=None)
    pe = _mock(PeerEntry, name="haproxy1", address="10.0.0.1", port=10000)

    result = _empty_gen(peers=[(ps, [pe])])
    assert "peers mypeers" in result
    assert "peer haproxy1 10.0.0.1:10000" in result


def test_peer_with_bind_and_default_server() -> None:
    """Peers with `bind` and `default-server`."""

    ps = _mock(
        PeerSection,
        name="cluster",
        default_bind=":10000 ssl crt /etc/ssl/cert.pem",
        default_server_options="ssl verify none",
        extra_options=None,
    )
    pe = _mock(PeerEntry, name="node1", address="10.0.0.1", port=10000)

    result = _empty_gen(peers=[(ps, [pe])])
    assert "bind :10000 ssl crt /etc/ssl/cert.pem" in result
    assert "default-server ssl verify none" in result


def test_peer_extra_options() -> None:
    """Peers `extra_options` are emitted."""

    ps = _mock(
        PeerSection,
        name="mypeers",
        default_bind=None,
        default_server_options=None,
        extra_options="table stick_table type ip size 1m",
    )
    pe = _mock(PeerEntry, name="node1", address="10.0.0.1", port=10000)

    result = _empty_gen(peers=[(ps, [pe])])
    assert "table stick_table type ip size 1m" in result


def test_mailer_basic() -> None:
    """Basic mailer section."""

    ms = _mock(MailerSection, name="mymailers", timeout_mail="10s", extra_options=None)
    me = _mock(MailerEntry, name="smtp1", address="smtp.example.com", port=25, smtp_auth=False)

    result = _empty_gen(mailers=[(ms, [me])])
    assert "mailers mymailers" in result
    assert "timeout mail 10s" in result
    assert "mailer smtp1 smtp.example.com:25" in result


def test_mailer_smtp_auth() -> None:
    """SMTP auth comment is emitted."""

    ms = _mock(MailerSection, name="auth", timeout_mail=None, extra_options=None)
    me = _mock(
        MailerEntry,
        name="smtp1",
        address="smtp.gmail.com",
        port=587,
        smtp_auth=True,
        smtp_user="user@gmail.com",
        smtp_password="app-pass",
        use_tls=False,
        use_starttls=True,
    )

    result = _empty_gen(mailers=[(ms, [me])])
    assert "# _pm_mailer_auth smtp1" in result
    assert "smtp_auth=true" in result
    assert "smtp_user=user@gmail.com" in result
    assert "use_starttls=true" in result


def test_mailer_extra_options() -> None:
    """Mailer `extra_options` are emitted."""

    ms = _mock(MailerSection, name="m", timeout_mail=None, extra_options="log global\ncustom-directive value")
    me = _mock(MailerEntry, name="smtp1", address="smtp.example.com", port=25, smtp_auth=False)

    result = _empty_gen(mailers=[(ms, [me])])
    assert "log global" in result
    assert "custom-directive value" in result


def test_http_errors_basic() -> None:
    """Basic http-errors section."""

    he_sec = _mock(HttpErrorsSection, name="custom-errors", extra_options=None)
    e1 = _mock(HttpErrorEntry, type="errorfile", status_code=503, value="/errors/503.http")
    e2 = _mock(HttpErrorEntry, type="errorloc302", status_code=504, value="https://sorry.example.com")

    result = _empty_gen(http_errors=[(he_sec, [e1, e2])])
    assert "http-errors custom-errors" in result
    assert "errorfile 503 /errors/503.http" in result
    assert "errorloc302 504 https://sorry.example.com" in result


def test_http_errors_extra_options() -> None:
    """Http-errors `extra_options` are emitted."""

    he_sec = _mock(HttpErrorsSection, name="custom", extra_options="log global")
    e1 = _mock(HttpErrorEntry, type="errorfile", status_code=503, value="/errors/503.http")

    result = _empty_gen(http_errors=[(he_sec, [e1])])
    assert "log global" in result


def test_cache_basic() -> None:
    """Basic cache section."""

    c = _mock(
        CacheSection,
        name="my_cache",
        total_max_size=4,
        max_object_size=524288,
        max_age=60,
        max_secondary_entries=None,
        process_vary=None,
        extra_options=None,
    )

    result = _empty_gen(caches=[c])
    assert "cache my_cache" in result
    assert "total-max-size 4" in result
    assert "max-object-size 524288" in result
    assert "max-age 60" in result


def test_cache_all_fields() -> None:
    """Cache section with every field."""

    c = _mock(
        CacheSection,
        name="full",
        total_max_size=64,
        max_object_size=524288,
        max_age=3600,
        max_secondary_entries=10,
        process_vary=1,
        extra_options=None,
    )
    result = _empty_gen(caches=[c])

    assert "max-secondary-entries 10" in result
    assert "process-vary 1" in result


def test_cache_extra_options() -> None:
    """Cache `extra_options` are emitted."""

    c = _mock(
        CacheSection,
        name="c",
        total_max_size=4,
        max_object_size=None,
        max_age=None,
        max_secondary_entries=None,
        process_vary=None,
        extra_options="some-future-directive value",
    )
    result = _empty_gen(caches=[c])
    assert "some-future-directive value" in result


def test_roundtrip_global_defaults() -> None:
    """Global + defaults round-trip."""

    gs = _mock(GlobalSetting, directive="log", value="127.0.0.1 local0", comment=None)
    ds = _mock(DefaultSetting, directive="mode", value="http", comment=None)
    text = _empty_gen(global_settings=[gs], default_settings=[ds])
    parsed = parse_config(text)

    assert len(parsed.global_settings) >= 1
    assert len(parsed.default_settings) >= 1


def test_roundtrip_frontend() -> None:
    """Frontend round-trip."""

    fe = _mock(Frontend, name="fe", mode="http", default_backend="be_web")
    bind = _mock(FrontendBind, bind_line="*:80")
    text = _empty_gen(frontends=[(fe, [bind], [], [])])
    parsed = parse_config(text)

    assert len(parsed.frontends) == 1
    assert parsed.frontends[0].name == "fe"


def test_roundtrip_backend() -> None:
    """Backend round-trip."""

    be = _mock(Backend, name="be_web", mode="http", balance="roundrobin")
    srv = _mock(BackendServer, name="s1", address="10.0.0.1", port=80, check_enabled=True)
    text = _empty_gen(backends=[(be, [srv])])
    parsed = parse_config(text)

    assert len(parsed.backends) == 1
    assert parsed.backends[0].name == "be_web"
    assert len(parsed.backends[0].servers) == 1


def test_roundtrip_resolver() -> None:
    """Resolver round-trip."""

    res = _mock(
        Resolver,
        name="mydns",
        resolve_retries=3,
        timeout_resolve="1s",
        timeout_retry="1s",
        parse_resolv_conf=None,
        accepted_payload_size=None,
        extra_options=None,
    )
    for hold in ("valid", "other", "refused", "timeout", "obsolete", "nx", "aa"):
        setattr(res, f"hold_{hold}", None)

    ns = _mock(ResolverNameserver, name="dns1", address="8.8.8.8", port=53)
    text = _empty_gen(resolvers=[(res, [ns])])
    parsed = parse_config(text)

    assert len(parsed.resolvers) == 1
    assert parsed.resolvers[0].name == "mydns"


def test_roundtrip_peers() -> None:
    """Peers round-trip."""

    ps = _mock(PeerSection, name="cluster", default_bind=None, default_server_options=None, extra_options=None)
    pe = _mock(PeerEntry, name="node1", address="10.0.0.1", port=10000)
    text = _empty_gen(peers=[(ps, [pe])])
    parsed = parse_config(text)

    assert len(parsed.peers) == 1
    assert parsed.peers[0].name == "cluster"


def test_roundtrip_http_errors() -> None:
    """HTTP errors round-trip."""

    he_sec = _mock(HttpErrorsSection, name="custom", extra_options=None)
    e = _mock(HttpErrorEntry, type="errorfile", status_code=503, value="/errors/503.http")
    text = _empty_gen(http_errors=[(he_sec, [e])])
    parsed = parse_config(text)

    assert len(parsed.http_errors) == 1
    assert parsed.http_errors[0].entries[0].status_code == 503


def test_roundtrip_cache() -> None:
    """Cache round-trip."""

    c = _mock(
        CacheSection,
        name="my_cache",
        total_max_size=64,
        max_object_size=524288,
        max_age=3600,
        max_secondary_entries=None,
        process_vary=None,
        extra_options=None,
    )
    text = _empty_gen(caches=[c])
    parsed = parse_config(text)

    assert len(parsed.caches) == 1
    assert parsed.caches[0].total_max_size == 64


def test_roundtrip_mailers() -> None:
    """Mailers round-trip."""

    ms = _mock(MailerSection, name="mymailers", timeout_mail="10s", extra_options=None)
    me = _mock(MailerEntry, name="smtp1", address="smtp.example.com", port=25, smtp_auth=False)
    text = _empty_gen(mailers=[(ms, [me])])
    parsed = parse_config(text)

    assert len(parsed.mailers) == 1
    assert parsed.mailers[0].entries[0].address == "smtp.example.com"


def test_roundtrip_full_config() -> None:
    """Full config round-trip with all section types."""

    gs = _mock(GlobalSetting, directive="log", value="127.0.0.1 local0", comment=None)
    ds = _mock(DefaultSetting, directive="mode", value="http", comment=None)

    fe = _mock(Frontend, name="fe", mode="http", default_backend="be")
    bind = _mock(FrontendBind, bind_line="*:80")

    be = _mock(Backend, name="be", mode="http", balance="roundrobin")
    srv = _mock(BackendServer, name="s1", address="10.0.0.1", port=80, check_enabled=True)

    lb = _mock(ListenBlock, name="stats", mode="http", content="stats enable")
    lb_bind = _mock(ListenBlockBind, bind_line="*:8404")

    ul = _mock(Userlist, name="admins")
    ue = _mock(UserlistEntry, username="admin", password_hash="$6$hash")

    text = _empty_gen(
        global_settings=[gs],
        default_settings=[ds],
        frontends=[(fe, [bind], [], [])],
        backends=[(be, [srv])],
        listen_blocks=[(lb, [lb_bind])],
        userlists=[(ul, [ue])],
    )

    parsed = parse_config(text)
    assert len(parsed.global_settings) >= 1
    assert len(parsed.frontends) == 1
    assert len(parsed.backends) == 1
    assert len(parsed.listen_blocks) == 1
    assert len(parsed.userlists) == 1
