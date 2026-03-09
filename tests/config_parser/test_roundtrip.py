"""
Parser <-> Generator roundtrip tests
====================================

Verifies that parse -> generate -> parse -> generate produces stable,
identical output across multiple passes. Any drift between passes
would cause phantom "pending changes" in the Manual Edit workflow.
"""

import textwrap
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

from proxy_manager.config_parser.generator import generate_config
from proxy_manager.config_parser.parser import ParsedConfig, parse_config
from proxy_manager.config_parser.snapshot import _diff_entity_list


def _mock(spec: type, **attrs: Any) -> MagicMock:
    """Create a MagicMock with spec, defaulting columns to None/False."""

    m = MagicMock(spec=spec)
    for col in getattr(spec, "__table__", MagicMock()).columns:
        col_type = str(col.type)
        if "BOOLEAN" in col_type:
            setattr(m, col.name, False)
        elif "INTEGER" in col_type:
            setattr(m, col.name, None)
        else:
            setattr(m, col.name, None)

    for k, v in attrs.items():
        setattr(m, k, v)

    return m


def _parsed_to_models(parsed: ParsedConfig) -> dict[str, Any]:
    """Convert ParsedConfig into SimpleNamespace 'model' objects
    suitable for `generate_config`."""

    gs = [SimpleNamespace(directive=s.directive, value=s.value, comment=s.comment, sort_order=s.order) for s in parsed.global_settings]

    ds = [SimpleNamespace(directive=s.directive, value=s.value, comment=s.comment, sort_order=s.order) for s in parsed.default_settings]

    listen_blocks = []
    for lb in parsed.listen_blocks:
        lb_model = SimpleNamespace(
            name=lb.name,
            mode=lb.mode if lb.mode != "http" else lb.mode,
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
        lb_binds = [SimpleNamespace(bind_line=b, sort_order=i) for i, b in enumerate(lb.binds)]
        listen_blocks.append((lb_model, lb_binds))

    userlists = []
    for ul in parsed.userlists:
        ul_model = SimpleNamespace(name=ul.name)
        entries = [SimpleNamespace(username=e.username, password_hash=e.password_hash, sort_order=e.order) for e in ul.entries]
        userlists.append((ul_model, entries))

    frontends = []
    for fe in parsed.frontends:
        fe_model = SimpleNamespace(
            name=fe.name,
            mode=fe.mode,
            default_backend=fe.default_backend,
            timeout_client=fe.timeout_client,
            timeout_http_request=fe.timeout_http_request,
            timeout_http_keep_alive=fe.timeout_http_keep_alive,
            maxconn=fe.maxconn,
            option_httplog=fe.option_httplog,
            option_tcplog=fe.option_tcplog,
            option_forwardfor=fe.option_forwardfor,
            compression_algo=fe.compression_algo,
            compression_type=fe.compression_type,
            comment=fe.comment,
        )
        binds = [SimpleNamespace(bind_line=b, sort_order=i) for i, b in enumerate(fe.binds)]
        opts = [SimpleNamespace(directive=o.directive, value=o.value, comment=o.comment, sort_order=o.order) for o in fe.options]
        acls = []
        for a in fe.acls:
            acl_model = SimpleNamespace(
                domain=a.domain,
                backend_name=a.backend_name,
                acl_match_type=a.acl_match_type,
                is_redirect=a.is_redirect,
                redirect_target=a.redirect_target,
                redirect_code=a.redirect_code,
                comment=a.comment,
                enabled=a.enabled,
            )
            acls.append(acl_model)
        frontends.append((fe_model, binds, opts, acls))

    backends = []
    for be in parsed.backends:
        be_model = SimpleNamespace(
            name=be.name,
            mode=be.mode,
            balance=be.balance,
            option_forwardfor=be.option_forwardfor,
            option_httplog=be.option_httplog,
            option_tcplog=be.option_tcplog,
            option_redispatch=be.option_redispatch,
            retries=be.retries,
            retry_on=be.retry_on,
            auth_userlist=be.auth_userlist,
            health_check_enabled=be.health_check_enabled,
            health_check_method=be.health_check_method,
            health_check_uri=be.health_check_uri,
            http_check_expect=be.http_check_expect,
            errorfile=be.errorfile,
            comment=be.comment,
            extra_options=be.extra_options,
            cookie=be.cookie,
            timeout_server=be.timeout_server,
            timeout_connect=be.timeout_connect,
            timeout_queue=be.timeout_queue,
            default_server_options=be.default_server_options,
            http_reuse=be.http_reuse,
            hash_type=be.hash_type,
            compression_algo=be.compression_algo,
            compression_type=be.compression_type,
        )
        servers = []
        for srv in be.servers:
            srv_model = SimpleNamespace(
                name=srv.name,
                address=srv.address,
                port=srv.port,
                check_enabled=srv.check_enabled,
                maxconn=srv.maxconn,
                maxqueue=srv.maxqueue,
                extra_params=srv.extra_params,
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
            servers.append(srv_model)
        backends.append((be_model, servers))

    resolvers = []
    for r in parsed.resolvers:
        r_model = SimpleNamespace(
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
        ns = [SimpleNamespace(name=n.name, address=n.address, port=n.port) for n in r.nameservers]
        resolvers.append((r_model, ns))

    peers = []
    for p in parsed.peers:
        p_model = SimpleNamespace(
            name=p.name,
            comment=p.comment,
            default_bind=p.default_bind,
            default_server_options=p.default_server_options,
            extra_options=p.extra_options,
        )
        entries = [SimpleNamespace(name=e.name, address=e.address, port=e.port) for e in p.entries]
        peers.append((p_model, entries))

    mailers = []
    for m in parsed.mailers:
        m_model = SimpleNamespace(
            name=m.name,
            timeout_mail=m.timeout_mail,
            comment=m.comment,
            extra_options=m.extra_options,
        )
        entries = [
            SimpleNamespace(
                name=e.name,
                address=e.address,
                port=e.port,
                smtp_auth=e.smtp_auth,
                smtp_user=e.smtp_user,
                smtp_password=e.smtp_password,
                use_tls=e.use_tls,
                use_starttls=e.use_starttls,
            )
            for e in m.entries
        ]
        mailers.append((m_model, entries))

    http_errors = []
    for he in parsed.http_errors:
        he_model = SimpleNamespace(
            name=he.name,
            comment=he.comment,
            extra_options=he.extra_options,
        )
        entries = [SimpleNamespace(type=e.type, status_code=e.status_code, value=e.value) for e in he.entries]
        http_errors.append((he_model, entries))

    caches = []
    for c in parsed.caches:
        caches.append(
            SimpleNamespace(
                name=c.name,
                total_max_size=c.total_max_size,
                max_object_size=c.max_object_size,
                max_age=c.max_age,
                max_secondary_entries=c.max_secondary_entries,
                process_vary=c.process_vary,
                comment=c.comment,
                extra_options=c.extra_options,
            )
        )

    return dict(
        global_settings=gs,
        default_settings=ds,
        listen_blocks=listen_blocks,
        userlists=userlists,
        frontends=frontends,
        backends=backends,
        resolvers=resolvers,
        peers=peers,
        mailers=mailers,
        http_errors=http_errors,
        caches=caches,
    )


def _roundtrip(config_text: str, passes: int = 3) -> list[str]:
    """Run parse -> generate for *passes* iterations, returning
    the generated text at each pass."""

    results: list[str] = []
    text = config_text
    for _ in range(passes):
        parsed = parse_config(text)
        models = _parsed_to_models(parsed)
        text = generate_config(**models)
        results.append(text)

    return results


def _assert_stable(config_text: str, *, passes: int = 3) -> str:
    """Assert that the roundtrip is idempotent and return the stable output."""

    results = _roundtrip(config_text, passes=passes)
    for i in range(1, len(results)):
        assert results[i] == results[0], f"Roundtrip diverged at pass {i + 1}.\n--- pass 1 ---\n{results[0]}\n--- pass {i + 1} ---\n{results[i]}"
    return results[0]


def test_basic_settings() -> None:
    """Basic settings."""

    config = textwrap.dedent("""\
        global
            log 127.0.0.1 local0
            maxconn 4096
            daemon

        defaults
            mode http
            timeout connect 5000
            timeout client 30s
            timeout server 30s
    """)
    _assert_stable(config)


def test_settings_with_inline_comments() -> None:
    """Settings with inline comments."""

    config = textwrap.dedent("""\
        global
            maxconn 10000  # maximum connections
            ca-base /etc/ssl/certs  # Default SSL material locations
            tune.ssl.cachesize 200000  # ##
            tune.bufsize 32768  # Increased for custom errors

        defaults
            maxconn 2000  # option http-use-htx
            timeout client 300s  # must match server timeout
    """)

    _assert_stable(config)


def test_settings_with_hyphenated_directives() -> None:
    """Settings with hyphenated directives."""

    config = textwrap.dedent("""\
        global
            hard-stop-after 30s
            log-send-hostname
            ssl-default-bind-options prefer-client-ciphers no-sslv3

        defaults
            timeout http-request 10s
            timeout http-keep-alive 2s
    """)

    _assert_stable(config)


def test_valueless_directives() -> None:
    """Valueless directives."""

    config = textwrap.dedent("""\
        global
            daemon
            log-send-hostname

        defaults
            option httplog
    """)

    _assert_stable(config)


def test_multi_word_values() -> None:
    """Multi word values."""

    config = textwrap.dedent("""\
        global
            stats socket /run/haproxy/admin.sock mode 660 level admin
            log 127.0.0.1:514  local0
            ssl-default-bind-ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384
    """)

    _assert_stable(config)


def test_double_whitespace_preserved() -> None:
    """Internal whitespace inside values is preserved through roundtrip."""

    config = textwrap.dedent("""\
        global
            log 127.0.0.1:514  local0
    """)

    result = _assert_stable(config)
    assert "127.0.0.1:514  local0" in result


def test_basic_frontend() -> None:
    """Basic frontend."""

    config = textwrap.dedent("""\
        frontend fe_http
            bind *:80
            mode http
            default_backend be_web
    """)

    _assert_stable(config)


def test_frontend_with_options() -> None:
    """Frontend with options."""

    config = textwrap.dedent("""\
        frontend fe_http
            bind *:80
            mode http
            option httplog
            option forwardfor
            default_backend be_web
            timeout client 30s
    """)

    _assert_stable(config)


def test_frontend_with_ssl_bind() -> None:
    """Frontend with ssl bind."""

    config = textwrap.dedent("""\
        frontend fe_https
            bind *:443 ssl crt /etc/ssl/cert.pem
            mode http
            default_backend be_web
    """)

    _assert_stable(config)


def test_frontend_with_acl() -> None:
    """Frontend with acl."""

    config = textwrap.dedent("""\
        frontend fe_http
            bind *:80
            mode http
            default_backend be_default

            acl ACL_example_com hdr_dom(Host) -i example.com
            use_backend be_example if ACL_example_com
    """)

    _assert_stable(config)


def test_basic_backend() -> None:
    """Basic backend."""

    config = textwrap.dedent("""\
        backend be_web
            mode http
            balance roundrobin
            server web1 10.0.0.1:8080 check
    """)

    _assert_stable(config)


def test_backend_with_servers() -> None:
    """Backend with servers."""

    config = textwrap.dedent("""\
        backend be_web
            mode http
            balance roundrobin
            timeout server 30s
            timeout connect 5s
            server web1 10.0.0.1:8080 check inter 5s rise 3 fall 2
            server web2 10.0.0.2:8080 check weight 50 backup
    """)

    _assert_stable(config)


def test_backend_with_health_check() -> None:
    """Backend with health check."""

    config = textwrap.dedent("""\
        backend be_api
            mode http
            option httpchk
            http-check send meth GET uri /health
            http-check expect status 200
            server api1 10.0.0.1:3000 check
    """)

    _assert_stable(config)


def test_backend_with_ssl_server() -> None:
    """Backend with ssl server."""

    config = textwrap.dedent("""\
        backend be_secure
            mode http
            server s1 10.0.0.1:443 ssl verify required check
    """)

    _assert_stable(config)


def test_backend_with_cookie() -> None:
    """Backend with cookie."""

    config = textwrap.dedent("""\
        backend be_sticky
            mode http
            cookie SRVID insert indirect nocache
            server s1 10.0.0.1:8080 cookie s1 check
            server s2 10.0.0.2:8080 cookie s2 check
    """)

    _assert_stable(config)


def test_basic_listen() -> None:
    """Basic listen."""

    config = textwrap.dedent("""\
        listen stats
            bind *:8404
            mode http
            maxconn 100
    """)

    _assert_stable(config)


def test_listen_with_options() -> None:
    """Listen with options."""

    config = textwrap.dedent("""\
        listen stats
            bind *:8404
            mode http
            balance roundrobin
            timeout client 10s
            timeout server 10s
            timeout connect 5s
    """)

    _assert_stable(config)


def test_basic_userlist() -> None:
    """Basic userlist."""

    config = textwrap.dedent("""\
        userlist admin_users
            user admin password $5$rounds=5000$hash123
            user viewer password $5$rounds=5000$hash456
    """)

    _assert_stable(config)


def test_basic_resolver() -> None:
    """Basic resolver."""

    config = textwrap.dedent("""\
        resolvers dns
            nameserver ns1 8.8.8.8:53
            nameserver ns2 8.8.4.4:53
            resolve_retries 3
            timeout resolve 1s
            timeout retry 1s
    """)

    _assert_stable(config)


def test_resolver_with_holds() -> None:
    """Resolver with holds."""

    config = textwrap.dedent("""\
        resolvers dns
            nameserver ns1 1.1.1.1:53
            resolve_retries 3
            timeout resolve 2s
            timeout retry 1s
            hold valid 30s
            hold other 30s
            hold refused 30s
            hold timeout 30s
            hold obsolete 30s
    """)
    _assert_stable(config)


def test_basic_peers() -> None:
    """Basic peers."""

    config = textwrap.dedent("""\
        peers mycluster
            peer haproxy1 192.168.1.1:10000
            peer haproxy2 192.168.1.2:10000
    """)

    _assert_stable(config)


def test_basic_mailers() -> None:
    """Basic mailers."""

    config = textwrap.dedent("""\
        mailers alerting
            timeout mail 10s
            mailer smtp1 smtp.example.com:25
    """)

    _assert_stable(config)


def test_basic_http_errors() -> None:
    """Basic http errors."""

    config = textwrap.dedent("""\
        http-errors custom_errors
            errorfile 503 /etc/haproxy/errors/503.http
            errorfile 502 /etc/haproxy/errors/502.http
    """)

    _assert_stable(config)


def test_basic_cache() -> None:
    """Basic cache."""

    config = textwrap.dedent("""\
        cache small
            total-max-size 64
            max-object-size 10000
            max-age 30
    """)

    _assert_stable(config)


PRODUCTION_CONFIG = textwrap.dedent("""\
    global
        log 127.0.0.1:514  local0
        log-send-hostname
        stats socket /run/haproxy/admin.sock mode 660 level admin
        hard-stop-after 30s
        maxconn 10000
        ca-base /etc/ssl/certs  # Default SSL material locations
        crt-base /etc/ssl/private
        ssl-default-bind-options prefer-client-ciphers no-sslv3 no-tlsv10 no-tlsv11
        tune.ssl.cachesize 200000  # ##
        tune.bufsize 32768  # Increased for custom errors
        daemon

    defaults
        maxconn 2000  # connection limit
        log global
        mode http
        option httplog
        timeout client 300s  # Client timeout
        timeout server 300s  # Server timeout
        timeout queue 30s
        timeout connect 5s
        timeout http-request 10s
        timeout http-keep-alive 2s

    listen stats
        bind *:8404
        mode http
        maxconn 100

    userlist admin_users
        user admin password $5$rounds=5000$abcdef1234567890

    frontend fe_http
        bind *:80
        mode http
        default_backend be_web

        acl ACL_example_com hdr_dom(Host) -i example.com
        use_backend be_example if ACL_example_com

    frontend fe_https
        bind *:443 ssl crt /etc/ssl/cert.pem
        mode http
        default_backend be_web

    backend be_web
        mode http
        balance roundrobin
        option forwardfor
        timeout server 30s
        timeout connect 5s
        server web1 10.0.0.1:8080 check inter 5s
        server web2 10.0.0.2:8080 check weight 50

    backend be_example
        mode http
        balance roundrobin
        server app1 10.0.1.1:3000 check

    resolvers dns
        nameserver ns1 8.8.8.8:53
        nameserver ns2 8.8.4.4:53
        resolve_retries 3
        timeout resolve 1s
        timeout retry 1s

    cache small
        total-max-size 64
        max-object-size 10000
        max-age 30
""")


def test_full_config_stable() -> None:
    """Three-pass roundtrip produces identical output."""

    _assert_stable(PRODUCTION_CONFIG)


def test_single_setting_change_detected() -> None:
    """Changing one setting value yields exactly one diff in the
    global_settings section when compared via the snapshot diff
    algorithm (positional, id/sort_order stripped)."""

    parsed_orig = parse_config(PRODUCTION_CONFIG)
    modified_text = PRODUCTION_CONFIG.replace("hard-stop-after 30s", "hard-stop-after 31s")
    parsed_mod = parse_config(modified_text)

    # Compare settings content-only (same logic as _strip_meta)
    strip = {"id", "sort_order"}

    orig_gs = [
        {k: v for k, v in {"directive": s.directive, "value": s.value, "comment": s.comment, "sort_order": s.order}.items() if k not in strip} for s in parsed_orig.global_settings
    ]

    mod_gs = [
        {k: v for k, v in {"directive": s.directive, "value": s.value, "comment": s.comment, "sort_order": s.order}.items() if k not in strip} for s in parsed_mod.global_settings
    ]

    diffs = sum(1 for a, b in zip(orig_gs, mod_gs, strict=False) if a != b)
    length_diff = abs(len(orig_gs) - len(mod_gs))

    assert diffs + length_diff == 1, f"Expected exactly 1 diff, got {diffs} value diffs and {length_diff} length difference"


def test_single_default_change_detected() -> None:
    """Changing one default setting yields exactly one diff."""

    modified_text = PRODUCTION_CONFIG.replace("timeout connect 5s", "timeout connect 6s")
    parsed_orig = parse_config(PRODUCTION_CONFIG)
    parsed_mod = parse_config(modified_text)

    strip = {"id", "sort_order"}
    orig_ds = [{k: v for k, v in {"directive": s.directive, "value": s.value, "comment": s.comment}.items() if k not in strip} for s in parsed_orig.default_settings]

    mod_ds = [{k: v for k, v in {"directive": s.directive, "value": s.value, "comment": s.comment}.items() if k not in strip} for s in parsed_mod.default_settings]

    diffs = sum(1 for a, b in zip(orig_ds, mod_ds, strict=False) if a != b)
    assert diffs == 1


def test_pass1_equals_pass2() -> None:
    """First and second generation passes produce byte-identical text."""

    results = _roundtrip(PRODUCTION_CONFIG, passes=2)
    assert results[0] == results[1]


def test_pass1_equals_pass5() -> None:
    """Five-pass roundtrip is still stable."""

    results = _roundtrip(PRODUCTION_CONFIG, passes=5)
    assert results[0] == results[4]


def test_nonsequential_sort_order() -> None:
    """Settings with non-sequential sort_order (e.g. 0,2,5,10)
    should still match after re-import which uses sequential (0,1,2,3)
    when sort_order is stripped from comparison."""

    old_items = [
        {"id": 1, "directive": "log", "value": "127.0.0.1 local0", "comment": None, "sort_order": 0},
        {"id": 2, "directive": "maxconn", "value": "4096", "comment": None, "sort_order": 5},
        {"id": 3, "directive": "daemon", "value": "", "comment": None, "sort_order": 10},
    ]

    # After re-import, IDs change and sort_order is sequential
    new_items = [
        {"id": 100, "directive": "log", "value": "127.0.0.1 local0", "comment": None, "sort_order": 0},
        {"id": 101, "directive": "maxconn", "value": "4096", "comment": None, "sort_order": 1},
        {"id": 102, "directive": "daemon", "value": "", "comment": None, "sort_order": 2},
    ]

    diff = _diff_entity_list(old_items, new_items, "_ordered")
    assert diff["total"] == 0, (
        f"Expected 0 changes (different id/sort_order should be ignored), got {diff['total']}: created={diff['created']}, deleted={diff['deleted']}, updated={diff['updated']}"
    )


def test_one_value_change_with_different_sort_order() -> None:
    """Changing one value should produce exactly 1 diff even when
    sort_order values differ between old and new snapshots."""

    old_items = [
        {"id": 1, "directive": "log", "value": "127.0.0.1 local0", "comment": None, "sort_order": 0},
        {"id": 2, "directive": "maxconn", "value": "4096", "comment": None, "sort_order": 5},
        {"id": 3, "directive": "hard-stop-after", "value": "30s", "comment": None, "sort_order": 10},
    ]
    new_items = [
        {"id": 100, "directive": "log", "value": "127.0.0.1 local0", "comment": None, "sort_order": 0},
        {"id": 101, "directive": "maxconn", "value": "4096", "comment": None, "sort_order": 1},
        {"id": 102, "directive": "hard-stop-after", "value": "31s", "comment": None, "sort_order": 2},
    ]

    diff = _diff_entity_list(old_items, new_items, "_ordered")
    assert diff["total"] == 1
    assert len(diff["updated"]) == 1
    assert diff["updated"][0]["entity"] == "hard-stop-after"


def test_entity_id_carried_in_ordered_diff() -> None:
    """The _ordered diff should carry entity_id from the new item's
    raw (pre-strip) id for frontend matching."""

    old_items = [
        {"id": 1, "directive": "maxconn", "value": "4096", "comment": None, "sort_order": 0},
    ]
    new_items = [
        {"id": 42, "directive": "maxconn", "value": "8192", "comment": None, "sort_order": 0},
    ]

    diff = _diff_entity_list(old_items, new_items, "_ordered")
    assert diff["total"] == 1
    assert diff["updated"][0]["entity_id"] == "42"


def test_hash_only_comment() -> None:
    """A comment that is just '##' survives."""

    config = textwrap.dedent("""\
        global
            tune.ssl.cachesize 200000  # ##
    """)

    result = _assert_stable(config)
    assert "# ##" in result


def test_comment_with_special_chars() -> None:
    """Comments with special characters survive."""

    config = textwrap.dedent("""\
        global
            maxconn 10000  # max connections (production)
    """)

    result = _assert_stable(config)
    assert "# max connections (production)" in result


def test_no_comments() -> None:
    """Settings without comments don't gain comments."""

    config = textwrap.dedent("""\
        global
            maxconn 4096
            daemon
    """)

    result = _assert_stable(config)
    assert "#" not in result.split("global")[1]
