"""
Config parser tests
===================

Comprehensive tests for `parse_config` and related parser dataclasses.
"""

import textwrap

from proxy_manager.config_parser.parser import (
    ParsedCacheSection,
    ParsedHttpErrorEntry,
    ParsedHttpErrorsSection,
    ParsedMailerEntry,
    ParsedMailerSection,
    ParsedPeerEntry,
    ParsedPeerSection,
    ParsedResolver,
    ParsedResolverNameserver,
    ParsedSslCertificate,
    parse_config,
)

MINIMAL_CONFIG = textwrap.dedent("""\
    global
        log 127.0.0.1 local0
        maxconn 4096

    defaults
        mode http
        timeout connect 5000

    frontend fe_http
        bind *:80
        mode http
        default_backend be_web

    backend be_web
        mode http
        balance roundrobin
    server web1 10.0.0.1:8080 check
""")


def test_parse_global() -> None:
    """Global directives are parsed."""

    parsed = parse_config(MINIMAL_CONFIG)
    assert len(parsed.global_settings) >= 2

    directives = {s.directive for s in parsed.global_settings}
    assert "log" in directives or any("log" in s.directive for s in parsed.global_settings)


def test_parse_defaults() -> None:
    """Defaults directives are parsed."""

    parsed = parse_config(MINIMAL_CONFIG)
    assert len(parsed.default_settings) >= 2


def test_parse_empty() -> None:
    """Empty config produces empty result."""

    parsed = parse_config("")
    assert len(parsed.global_settings) == 0
    assert len(parsed.frontends) == 0
    assert len(parsed.backends) == 0


def test_parse_global_comment_block() -> None:
    """Comment block before a directive is attached as `comment`."""

    config = textwrap.dedent("""\
        global
            # Important setting
            maxconn 4096
            log 127.0.0.1 local0
    """)
    parsed = parse_config(config)
    maxconn = [s for s in parsed.global_settings if s.directive == "maxconn"][0]

    assert maxconn.comment == "Important setting"


def test_parse_settings_directive_only() -> None:
    """Directive without a value stores empty string."""

    config = textwrap.dedent("""\
        global
            daemon
    """)

    parsed = parse_config(config)
    daemon = [s for s in parsed.global_settings if s.directive == "daemon"]
    assert len(daemon) == 1
    assert daemon[0].value == ""


def test_parse_inline_comment_in_global() -> None:
    """`_strip_inline_comment` extracts `#` mid-line."""

    config = textwrap.dedent("""\
        global
            maxconn 4096  # max connections
    """)

    parsed = parse_config(config)
    gs = [s for s in parsed.global_settings if s.directive == "maxconn"]
    assert len(gs) == 1
    assert gs[0].value == "4096"
    assert gs[0].comment == "max connections"


def test_parse_inline_comment_quoted() -> None:
    """`#` inside quotes is NOT treated as a comment."""

    config = textwrap.dedent("""\
        global
            log "syslog#local0" facility
    """)

    parsed = parse_config(config)
    gs = [s for s in parsed.global_settings if s.directive == "log"]

    assert len(gs) == 1
    assert "#" in gs[0].value


def test_parse_frontend() -> None:
    """Frontend section is parsed."""

    parsed = parse_config(MINIMAL_CONFIG)
    assert len(parsed.frontends) == 1

    fe = parsed.frontends[0]
    assert fe.name == "fe_http"
    assert fe.default_backend == "be_web"
    assert len(fe.binds) >= 1


def test_parse_frontend_new_fields() -> None:
    """Timeout / maxconn / option fields in a frontend."""
    cfg = textwrap.dedent("""\

        frontend myfe
        bind *:80
        mode http
        default_backend mybackend
        timeout client 30s
        timeout http-request 10s
        timeout http-keep-alive 5s
        maxconn 10000
        option httplog
        option tcplog
        option forwardfor
        compression algo gzip
        compression type text/html text/css
    """)

    parsed = parse_config(cfg)
    assert len(parsed.frontends) == 1

    fe = parsed.frontends[0]
    assert fe.timeout_client == "30s"
    assert fe.timeout_http_request == "10s"
    assert fe.timeout_http_keep_alive == "5s"
    assert fe.maxconn == 10000
    assert fe.option_httplog is True
    assert fe.option_tcplog is True
    assert fe.option_forwardfor is True
    assert fe.compression_algo == "gzip"
    assert fe.compression_type == "text/html text/css"


def test_parse_frontend_maxconn_invalid() -> None:
    """Invalid maxconn in frontend is silently ignored."""

    config = textwrap.dedent("""\
        frontend fe
            bind *:80
            maxconn invalid
    """)

    parsed = parse_config(config)
    assert parsed.frontends[0].maxconn is None


def test_parse_frontend_inline_comment() -> None:
    """Inline comment in a frontend option is stripped."""

    config = textwrap.dedent("""\
        frontend fe
            bind *:80
            http-request set-header X-Test foo  # test header
    """)

    parsed = parse_config(config)
    opts = [o for o in parsed.frontends[0].options if o.directive == "http-request"]
    assert len(opts) == 1


def test_simple_option_directive_only() -> None:
    """Simple option is recognised."""

    config = textwrap.dedent("""\
        frontend fe_test
        bind *:80
        option httplog
    """)

    parsed = parse_config(config)
    assert parsed.frontends[0].name == "fe_test"


def test_option_split_directive_value() -> None:
    """Multi-word option is split into directive + value."""

    config = textwrap.dedent("""\
        frontend fe_split
        bind *:80
        http-request set-header X-Forwarded-Proto https
        http-response del-header server
        capture request header User-Agent len 64
    """)

    parsed = parse_config(config)
    fe = parsed.frontends[0]
    assert len(fe.options) >= 3

    opts = {o.directive: o for o in fe.options}
    assert opts["http-request"].value == "set-header X-Forwarded-Proto https"
    assert opts["http-response"].value == "del-header server"
    assert opts["capture"].value == "request header User-Agent len 64"


def test_option_no_value() -> None:
    """Single-word directive gets the rest as value."""

    config = textwrap.dedent("""\
        frontend fe_noval
        bind *:80
        http-request del-header Proxy
    """)

    parsed = parse_config(config)
    opts_by_dir = [o for o in parsed.frontends[0].options if o.directive == "http-request"]
    assert len(opts_by_dir) >= 1
    assert opts_by_dir[0].value == "del-header Proxy"


def test_option_with_comment() -> None:
    """Comment lines before a directive are attached."""

    config = textwrap.dedent("""\
        frontend fe_comment
        bind *:80
        # Security header cleanup
        http-request del-header Proxy
    """)

    parsed = parse_config(config)
    proxy_opts = [o for o in parsed.frontends[0].options if o.directive == "http-request"]
    assert len(proxy_opts) >= 1
    assert proxy_opts[0].comment == "Security header cleanup"


def test_option_order_preserved() -> None:
    """Options maintain insertion order."""

    config = textwrap.dedent("""\
        frontend fe_order
        bind *:80
        http-request set-header X-A one
        http-response del-header server
        tcp-request inspect-delay 10s
    """)

    parsed = parse_config(config)
    directives = [o.directive for o in parsed.frontends[0].options]
    assert directives == ["http-request", "http-response", "tcp-request"]


def test_stick_table_option() -> None:
    """`stick-table` directive is parsed as an option."""

    config = textwrap.dedent("""\
        frontend fe_stick
        bind *:80
        stick-table type ipv6 size 100k expire 90s store http_req_rate(15s)
    """)

    parsed = parse_config(config)
    stick_opts = [o for o in parsed.frontends[0].options if o.directive == "stick-table"]
    assert len(stick_opts) == 1
    assert "type ipv6" in stick_opts[0].value
    assert "size 100k" in stick_opts[0].value


def test_acl_as_option() -> None:
    """Non-routing ACL stored as a generic option."""

    config = textwrap.dedent("""\
        frontend fe_acl
        bind *:80
        acl whitelist_ips src 10.0.0.0/8
        http-request deny deny_status 429 if !whitelist_ips
    """)

    parsed = parse_config(config)
    acl_opts = [o for o in parsed.frontends[0].options if o.directive == "acl"]
    assert len(acl_opts) == 1
    assert "whitelist_ips" in acl_opts[0].value


def test_redirect_non_acl_as_option() -> None:
    """Non-ACL redirect stored as a generic option."""

    config = textwrap.dedent("""\
        frontend fe_redir
        bind *:80
        redirect scheme https code 301 if !{ ssl_fc }
    """)

    parsed = parse_config(config)
    redir_opts = [o for o in parsed.frontends[0].options if o.directive == "redirect"]
    assert len(redir_opts) == 1
    assert "scheme https" in redir_opts[0].value


def test_multiple_comments_before_option() -> None:
    """Multi-line comment block is joined."""

    config = textwrap.dedent("""\
        frontend fe_multicomment
        bind *:80
        # Line one
        # Line two
        http-request set-header X-Test foo
    """)

    parsed = parse_config(config)
    opts = [o for o in parsed.frontends[0].options if o.directive == "http-request"]
    assert len(opts) >= 1
    assert opts[0].comment is not None
    assert "Line one" in opts[0].comment
    assert "Line two" in opts[0].comment


def test_mixed_options_and_known_fields() -> None:
    """Known fields do NOT appear in the options list."""

    config = textwrap.dedent("""\
        frontend fe_mixed
        bind *:80
        mode http
        default_backend mybackend
        timeout client 30s
        maxconn 5000
        http-request set-header X-A value1
        option forwardfor
    """)

    parsed = parse_config(config)
    fe = parsed.frontends[0]
    assert fe.timeout_client == "30s"
    assert fe.maxconn == 5000
    assert fe.default_backend == "mybackend"

    opt_directives = [o.directive for o in fe.options]
    assert "http-request" in opt_directives
    assert "timeout" not in opt_directives
    assert "maxconn" not in opt_directives


def test_roundtrip_parser_preserves_split() -> None:
    """Complex config preserves directive / value split."""

    config = textwrap.dedent("""\
        frontend fe_complex
        bind *:80
        bind *:443 ssl crt /etc/haproxy/certs/site.pem
        mode http
        default_backend be_web
        option forwardfor except 127.0.0.0/8
        http-request set-header X-Forwarded-Port %[dst_port]
        http-request set-header X-Forwarded-Proto https if { ssl_fc }
        http-request del-header Proxy
        capture request header Host len 64
        stick-table type ipv6 size 100k expire 90s store http_req_rate(15s)
        http-request track-sc0 src
        acl whitelist_ips src 10.0.0.0/8
        http-request deny deny_status 429 if { sc_http_req_rate(0) gt 300 } !whitelist_ips
    """)

    parsed = parse_config(config)
    fe = parsed.frontends[0]
    for o in fe.options:
        assert o.directive, f"Empty directive found: {o}"
        assert isinstance(o.value, str), f"Value should be str: {o}"

    set_headers = [o for o in fe.options if o.directive == "http-request" and "set-header" in o.value]
    assert len(set_headers) >= 2

    del_headers = [o for o in fe.options if o.directive == "http-request" and "del-header" in o.value]
    assert len(del_headers) >= 1


def test_parse_frontend_non_acl_redirect_as_option() -> None:
    """Redirect not matching ACL pattern becomes a generic option."""

    config = textwrap.dedent("""\
        frontend fe
            bind *:80
            redirect scheme https code 301 if !{ ssl_fc }
    """)

    parsed = parse_config(config)
    redir = [o for o in parsed.frontends[0].options if o.directive == "redirect"]
    assert len(redir) == 1
    assert "scheme https" in redir[0].value


def test_parse_frontend_acl_use_backend() -> None:
    """ACL + `use_backend` pair is parsed."""

    config = textwrap.dedent("""\
        frontend fe
            bind *:80
            mode http
            acl ACL_example_com hdr(Host) -i example.com
            use_backend be_example if ACL_example_com
    """)

    parsed = parse_config(config)
    fe = parsed.frontends[0]
    assert len(fe.acls) == 1
    assert fe.acls[0].domain == "example.com"
    assert fe.acls[0].backend_name == "be_example"
    assert fe.acls[0].acl_match_type == "hdr"


def test_parse_frontend_acl_redirect() -> None:
    """ACL redirect branch is parsed."""

    config = textwrap.dedent("""\
        frontend fe
            bind *:80
            mode http
            acl ACL_old_site hdr(Host) -i old.example.com
            redirect prefix https://new.example.com code 301 if ACL_old_site
    """)

    parsed = parse_config(config)
    acl = parsed.frontends[0].acls[0]

    assert acl.is_redirect is True
    assert acl.redirect_target == "https://new.example.com"
    assert acl.redirect_code == 301
    assert acl.domain == "old.example.com"


def test_parse_frontend_acl_with_comment() -> None:
    """Preceding comment is attached to the ACL."""

    config = textwrap.dedent("""\
        frontend fe
            bind *:80
            mode http
            # Route to API backend
            acl ACL_api hdr(Host) -i api.example.com
            use_backend be_api if ACL_api
    """)

    parsed = parse_config(config)
    assert parsed.frontends[0].acls[0].comment == "Route to API backend"


def test_no_ssl_in_config() -> None:
    """Config without SSL produces no SSL certificates."""

    config = textwrap.dedent("""\
        frontend fe_http
        bind *:80
        mode http
        default_backend be_web

        backend be_web
        server s1 10.0.0.1:8080 check
    """)

    parsed = parse_config(config)
    assert len(parsed.ssl_certificates) == 0


def test_ssl_pem_file_in_frontend() -> None:
    """`ssl crt /path/to/file.pem` extracts one cert."""

    config = textwrap.dedent("""\
        frontend fe_https
        bind *:443 ssl crt /etc/haproxy/certs/site.pem
        mode http
        default_backend be_web

        backend be_web
        server s1 10.0.0.1:8080 check
    """)

    parsed = parse_config(config)
    assert len(parsed.ssl_certificates) == 1

    sc = parsed.ssl_certificates[0]
    assert sc.domain == "site.pem"
    assert sc.fullchain_path == "/etc/haproxy/certs/site.pem"
    assert sc.provider == "manual"
    assert sc.status == "active"
    assert sc.auto_renew is False
    assert "frontend fe_https" in (sc.comment or "")


def test_ssl_directory_in_frontend() -> None:
    """Directory path (no extension) is handled."""

    config = textwrap.dedent("""\
        frontend fe_https
        bind *:443 ssl crt /etc/haproxy/certs
        default_backend be_web

        backend be_web
        server s1 10.0.0.1:8080 check
    """)

    parsed = parse_config(config)
    assert len(parsed.ssl_certificates) == 1

    sc = parsed.ssl_certificates[0]
    assert sc.domain == "certs"
    assert sc.fullchain_path == "/etc/haproxy/certs"


def test_ssl_in_listen_block() -> None:
    """Listen block with ssl crt extracts cert."""

    config = textwrap.dedent("""\
        listen stats
        bind *:9000 ssl crt /etc/ssl/private/stats.pem
        mode http
        stats enable
        stats uri /stats
    """)

    parsed = parse_config(config)
    assert len(parsed.ssl_certificates) == 1

    sc = parsed.ssl_certificates[0]
    assert sc.domain == "stats.pem"
    assert "listen stats" in (sc.comment or "")


def test_letsencrypt_domain_extraction() -> None:
    """Letsencrypt-style path extracts the domain name."""

    config = textwrap.dedent("""\
        frontend fe_https
        bind *:443 ssl crt /etc/letsencrypt/live/example.com/fullchain.pem
        default_backend be_web

        backend be_web
        server s1 10.0.0.1:8080 check
    """)

    parsed = parse_config(config)
    assert len(parsed.ssl_certificates) == 1
    assert parsed.ssl_certificates[0].domain == "example.com"


def test_letsencrypt_wildcard_domain() -> None:
    """Letsencrypt wildcard cert path is handled."""

    config = textwrap.dedent("""\
        frontend fe_wild
        bind *:443 ssl crt /etc/letsencrypt/live/wildcard.example.org/fullchain.pem
        default_backend be_app
    """)

    parsed = parse_config(config)
    assert parsed.ssl_certificates[0].domain == "wildcard.example.org"


def test_multiple_ssl_binds_different_sections() -> None:
    """SSL certs from frontend and listen blocks are all extracted."""

    config = textwrap.dedent("""\
        frontend fe_https
        bind *:443 ssl crt /etc/letsencrypt/live/app.example.com/fullchain.pem
        default_backend be_app

        listen stats
        bind *:9000 ssl crt /etc/ssl/admin.pem
        stats enable

        backend be_app
        server s1 10.0.0.1:8080 check
    """)

    parsed = parse_config(config)
    assert len(parsed.ssl_certificates) == 2

    domains = {sc.domain for sc in parsed.ssl_certificates}
    assert "app.example.com" in domains
    assert "admin.pem" in domains


def test_duplicate_ssl_path_deduplicated() -> None:
    """Same cert path in multiple sections produces a single entry."""

    config = textwrap.dedent("""\
        frontend fe_one
        bind *:443 ssl crt /etc/haproxy/cert.pem
        default_backend be_a

        frontend fe_two
        bind *:8443 ssl crt /etc/haproxy/cert.pem
        default_backend be_b

        backend be_a
        server s1 10.0.0.1:80 check

        backend be_b
        server s2 10.0.0.2:80 check
    """)

    parsed = parse_config(config)
    assert len(parsed.ssl_certificates) == 1
    assert parsed.ssl_certificates[0].fullchain_path == "/etc/haproxy/cert.pem"


def test_ssl_with_additional_options() -> None:
    """Extra bind options (`alpn`, `strict-sni`) don't break extraction."""

    config = textwrap.dedent("""\
        frontend fe_https
        bind *:443 strict-sni ssl crt /etc/nethostssl alpn h2,http/1.1
        default_backend be_web
    """)

    parsed = parse_config(config)
    assert len(parsed.ssl_certificates) == 1

    sc = parsed.ssl_certificates[0]
    assert sc.domain == "nethostssl"
    assert sc.fullchain_path == "/etc/nethostssl"


def test_ssl_crt_with_quoted_path() -> None:
    """Quoted cert path is handled."""

    config = textwrap.dedent("""\
        frontend fe_https
        bind *:443 ssl crt "/etc/haproxy/my cert.pem"
        default_backend be_web
    """)

    parsed = parse_config(config)
    assert len(parsed.ssl_certificates) == 1
    assert parsed.ssl_certificates[0].fullchain_path == "/etc/haproxy/my cert.pem"


def test_ssl_cert_default_fields() -> None:
    """Extracted SSL certs have correct default values."""

    config = textwrap.dedent("""\
        frontend fe_https
        bind *:443 ssl crt /etc/haproxy/site.pem
        default_backend be_web
    """)

    parsed = parse_config(config)
    sc = parsed.ssl_certificates[0]
    assert sc.provider == "manual"
    assert sc.status == "active"
    assert sc.challenge_type == "http-01"
    assert sc.auto_renew is False
    assert sc.alt_domains is None
    assert sc.key_path is None
    assert sc.cert_path is None
    assert sc.comment is not None


def test_bind_without_ssl_keyword() -> None:
    """Bind without `ssl` keyword does NOT extract cert."""

    config = textwrap.dedent("""\
        frontend fe_http
        bind *:80
        default_backend be_web
    """)

    parsed = parse_config(config)
    assert len(parsed.ssl_certificates) == 0


def test_complex_bind_with_multiple_addresses() -> None:
    """Multi-address bind with ssl crt works."""

    config = textwrap.dedent("""\
        frontend fe_https
        bind ipv4@10.0.0.1:443,ipv6@::1:443 ssl crt /etc/letsencrypt/live/mysite.io/fullchain.pem alpn h2,http/1.1
        default_backend be_web
    """)

    parsed = parse_config(config)
    assert len(parsed.ssl_certificates) == 1
    assert parsed.ssl_certificates[0].domain == "mysite.io"


def test_multiple_frontends_different_certs() -> None:
    """Each frontend with a different cert produces separate entries."""

    config = textwrap.dedent("""\
        frontend fe_site_a
        bind *:443 ssl crt /etc/letsencrypt/live/site-a.com/fullchain.pem
        default_backend be_a

        frontend fe_site_b
        bind *:8443 ssl crt /etc/letsencrypt/live/site-b.com/fullchain.pem
        default_backend be_b

        backend be_a
        server s1 10.0.0.1:80 check

        backend be_b
        server s2 10.0.0.2:80 check
    """)

    parsed = parse_config(config)
    assert len(parsed.ssl_certificates) == 2

    domains = {sc.domain for sc in parsed.ssl_certificates}
    assert "site-a.com" in domains
    assert "site-b.com" in domains


def test_ssl_certificates_in_parsed_config_dataclass() -> None:
    """`ParsedConfig` has `ssl_certificates` as an empty list."""

    parsed = parse_config("")
    assert hasattr(parsed, "ssl_certificates")
    assert isinstance(parsed.ssl_certificates, list)
    assert len(parsed.ssl_certificates) == 0


def test_parsed_ssl_certificate_dataclass() -> None:
    """`ParsedSslCertificate` has expected defaults."""

    sc = ParsedSslCertificate(domain="test.com")
    assert sc.domain == "test.com"
    assert sc.cert_path is None
    assert sc.key_path is None
    assert sc.fullchain_path is None
    assert sc.provider == "manual"
    assert sc.status == "active"
    assert sc.challenge_type == "http-01"
    assert sc.auto_renew is False
    assert sc.alt_domains is None
    assert sc.comment is None


def test_non_standard_cert_domain_name() -> None:
    """Domain with dots in filename uses the filename as domain."""

    config = textwrap.dedent("""\
        frontend fe_https
        bind *:443 ssl crt /etc/ssl/certs/my.domain.com.pem
        default_backend be_web
    """)

    parsed = parse_config(config)
    assert parsed.ssl_certificates[0].domain == "my.domain.com"


def test_example_config_ssl_extraction() -> None:
    """Integration test: example config extracts multiple SSL certs."""

    config = textwrap.dedent("""\
        global
        log 127.0.0.1 local0
        ca-base /etc/ssl/certs
        crt-base /etc/ssl/private

        defaults
        mode http
        timeout connect 5s
        timeout client 30s
        timeout server 30s

        listen stats
        bind ipv4@127.0.0.1:9000 ssl crt /etc/nethostssl/default.pem
        mode http
        stats enable

        frontend http
        bind ipv4@10.0.0.1:443 strict-sni ssl crt /etc/nethostssl alpn h2,http/1.1
        mode http
        default_backend be_web

        backend be_web
        server s1 10.0.0.1:8080 check
    """)

    parsed = parse_config(config)
    assert len(parsed.ssl_certificates) == 2

    domains = {sc.domain for sc in parsed.ssl_certificates}
    assert "nethostssl" in domains
    assert "default.pem" in domains


def test_ssl_cert_source_comment() -> None:
    """Comment indicates which section the cert was extracted from."""

    config = textwrap.dedent("""\
        frontend fe_web
        bind *:443 ssl crt /etc/ssl/web.pem
        default_backend be_web

        listen api
        bind *:8443 ssl crt /etc/ssl/api.pem
        stats enable
    """)

    parsed = parse_config(config)
    assert len(parsed.ssl_certificates) == 2

    comments = {sc.domain: sc.comment for sc in parsed.ssl_certificates}
    assert "frontend fe_web" in (comments["web.pem"] or "")
    assert "listen api" in (comments["api.pem"] or "")


def test_case_insensitive_ssl_keyword() -> None:
    """SSL keyword matching is case-insensitive."""

    config = textwrap.dedent("""\
        frontend fe_https
        bind *:443 SSL CRT /etc/haproxy/cert.pem
        default_backend be_web
    """)

    parsed = parse_config(config)
    assert len(parsed.ssl_certificates) == 1


def test_multiple_bind_lines_one_frontend() -> None:
    """Only SSL bind lines produce certs."""

    config = textwrap.dedent("""\
        frontend fe_mixed
        bind *:80
        bind *:443 ssl crt /etc/ssl/site.pem
        default_backend be_web
    """)

    parsed = parse_config(config)
    assert len(parsed.ssl_certificates) == 1
    assert parsed.ssl_certificates[0].fullchain_path == "/etc/ssl/site.pem"


def test_parse_ssl_cert_no_basename() -> None:
    """Trailing slash still extracts something."""

    config = textwrap.dedent("""\
        frontend fe
            bind *:443 ssl crt /etc/certs/
            default_backend be
    """)

    parsed = parse_config(config)
    assert len(parsed.ssl_certificates) == 1


def test_parse_ssl_cert_fullchain_in_letsencrypt() -> None:
    """Letsencrypt `fullchain.pem` resolves domain from parent dir."""

    config = textwrap.dedent("""\
        frontend fe
            bind *:443 ssl crt /etc/letsencrypt/live/site.example.com/fullchain.pem
            default_backend be
    """)

    parsed = parse_config(config)
    assert parsed.ssl_certificates[0].domain == "site.example.com"


def test_parse_ssl_cert_crt_extension() -> None:
    """`.crt` extension in fullchain_path."""

    config = textwrap.dedent("""\
        frontend fe
            bind *:443 ssl crt /etc/ssl/server.crt
            default_backend be
    """)

    parsed = parse_config(config)
    assert parsed.ssl_certificates[0].fullchain_path == "/etc/ssl/server.crt"


def test_parse_ssl_cert_letsencrypt_bad_live_path() -> None:
    """Letsencrypt path with empty domain after `live/`."""

    config = textwrap.dedent("""\
        frontend fe
            bind *:443 ssl crt /etc/letsencrypt/live/
            default_backend be
    """)

    parsed = parse_config(config)
    assert len(parsed.ssl_certificates) == 1


def test_parse_backend() -> None:
    """Backend section is parsed."""

    parsed = parse_config(MINIMAL_CONFIG)
    assert len(parsed.backends) == 1

    be = parsed.backends[0]
    assert be.name == "be_web"
    assert be.balance == "roundrobin"
    assert len(be.servers) == 1
    assert be.servers[0].name == "web1"
    assert be.servers[0].port == 8080


def test_parse_multiple_backends() -> None:
    """Multiple backend sections."""

    config = textwrap.dedent("""\
        backend be_a
        mode http
        server s1 1.1.1.1:80 check

        backend be_b
        mode http
        server s2 2.2.2.2:80 check
    """)

    parsed = parse_config(config)
    assert len(parsed.backends) == 2

    names = {b.name for b in parsed.backends}
    assert "be_a" in names
    assert "be_b" in names


def test_parse_backend_new_fields() -> None:
    """Backend with all tier-1 fields."""

    cfg = textwrap.dedent("""\

        backend mybackend
        mode http
        balance leastconn
        cookie SRVID insert indirect nocache
        timeout server 30s
        timeout connect 5s
        timeout queue 60s
        http-check expect status 200
        default-server inter 3s fall 3 rise 2
        http-reuse aggressive
        hash-type consistent sdbm
        option httplog
        option tcplog
        compression algo gzip deflate
        compression type text/html text/css
        server srv1 10.0.0.1:80 check weight 100 ssl verify none backup
    """)

    parsed = parse_config(cfg)
    be = parsed.backends[0]
    assert be.cookie == "SRVID insert indirect nocache"
    assert be.timeout_server == "30s"
    assert be.timeout_connect == "5s"
    assert be.timeout_queue == "60s"
    assert be.http_check_expect == "status 200"
    assert be.default_server_options == "inter 3s fall 3 rise 2"
    assert be.http_reuse == "aggressive"
    assert be.hash_type == "consistent sdbm"
    assert be.option_httplog is True
    assert be.option_tcplog is True
    assert be.compression_algo == "gzip deflate"
    assert be.compression_type == "text/html text/css"

    srv = be.servers[0]
    assert srv.check_enabled is True
    assert srv.weight == 100
    assert srv.ssl_enabled is True
    assert srv.ssl_verify == "none"
    assert srv.backup is True


def test_parse_backend_comment() -> None:
    """Comment before directives is attached to `be.comment`."""

    config = textwrap.dedent("""\
        backend be_web
            # Main backend for web
            mode http
            server s1 10.0.0.1:80 check
    """)

    parsed = parse_config(config)
    assert parsed.backends[0].comment == "Main backend for web"


def test_parse_backend_retries_invalid() -> None:
    """Invalid retries falls back to extra_options."""

    config = textwrap.dedent("""\
        backend be
            retries abc
    """)

    parsed = parse_config(config)
    be = parsed.backends[0]
    assert be.retries is None
    assert be.extra_options is not None
    assert "retries" in be.extra_options


def test_parse_backend_retry_on() -> None:
    """`retry-on` directive."""

    config = textwrap.dedent("""\
        backend be
            retry-on conn-failure empty-response
    """)

    parsed = parse_config(config)
    assert parsed.backends[0].retry_on == "conn-failure empty-response"


def test_parse_backend_option_redispatch() -> None:
    """`option redispatch`."""

    config = textwrap.dedent("""\
        backend be
            option redispatch
    """)

    parsed = parse_config(config)
    assert parsed.backends[0].option_redispatch is True


def test_parse_backend_errorfile() -> None:
    """`errorfile` directive."""

    config = textwrap.dedent("""\
        backend be
            errorfile 503 /errors/503.http
    """)

    parsed = parse_config(config)
    assert parsed.backends[0].errorfile == "503 /errors/503.http"


def test_parse_backend_cookie() -> None:
    """`cookie` directive."""

    config = textwrap.dedent("""\
        backend be
            cookie SRVID insert indirect nocache
    """)

    parsed = parse_config(config)
    assert parsed.backends[0].cookie == "SRVID insert indirect nocache"


def test_parse_backend_timeouts() -> None:
    """`timeout server/connect/queue`."""

    config = textwrap.dedent("""\
        backend be
            timeout server 30s
            timeout connect 5s
            timeout queue 60s
    """)

    parsed = parse_config(config)
    be = parsed.backends[0]
    assert be.timeout_server == "30s"
    assert be.timeout_connect == "5s"
    assert be.timeout_queue == "60s"


def test_parse_backend_default_server() -> None:
    """`default-server` directive."""

    config = textwrap.dedent("""\
        backend be
            default-server inter 3s fall 3 rise 2
    """)

    parsed = parse_config(config)
    assert parsed.backends[0].default_server_options == "inter 3s fall 3 rise 2"


def test_parse_backend_http_reuse_hash_type() -> None:
    """`http-reuse` and `hash-type`."""

    config = textwrap.dedent("""\
        backend be
            http-reuse aggressive
            hash-type consistent sdbm
    """)

    parsed = parse_config(config)
    be = parsed.backends[0]
    assert be.http_reuse == "aggressive"
    assert be.hash_type == "consistent sdbm"


def test_parse_backend_compression() -> None:
    """`compression algo/type`."""

    config = textwrap.dedent("""\
        backend be
            compression algo gzip deflate
            compression type text/html text/css
    """)

    parsed = parse_config(config)
    be = parsed.backends[0]
    assert be.compression_algo == "gzip deflate"
    assert be.compression_type == "text/html text/css"


def test_parse_backend_auth_userlist() -> None:
    """`acl authorized http_auth(...)`."""

    config = textwrap.dedent("""\
        backend be
            acl authorized http_auth(admins)
            http-request auth realm Login unless authorized
    """)

    parsed = parse_config(config)
    assert parsed.backends[0].auth_userlist == "admins"


def test_parse_backend_http_check_connect() -> None:
    """`http-check connect` (silently handled)."""

    config = textwrap.dedent("""\
        backend be
            option httpchk
            http-check connect
            http-check send meth GET uri /health
    """)

    parsed = parse_config(config)
    be = parsed.backends[0]
    assert be.health_check_enabled is True
    assert be.health_check_method == "GET"
    assert be.health_check_uri == "/health"


def test_parse_backend_http_check_expect() -> None:
    """`http-check expect`."""

    config = textwrap.dedent("""\
        backend be
            http-check expect status 200
    """)

    parsed = parse_config(config)
    assert parsed.backends[0].http_check_expect == "status 200"


def test_parse_backend_with_inline_comment() -> None:
    """Inline comment on a backend directive is stripped."""

    config = textwrap.dedent("""\
        backend be
            mode http  # production mode
            server s1 10.0.0.1:80 check
    """)

    parsed = parse_config(config)
    assert parsed.backends[0].mode == "http"


def test_parse_backend_extra_options() -> None:
    """Unknown directives go to `extra_options`."""

    config = textwrap.dedent("""\
        backend be
            stick on src
            stick-table type ip size 1m expire 10s
    """)

    parsed = parse_config(config)
    be = parsed.backends[0]
    assert be.extra_options is not None
    assert "stick on src" in be.extra_options
    assert "stick-table" in be.extra_options


def test_parse_backend_option_tcplog() -> None:
    """`option tcplog` in backend."""

    config = textwrap.dedent("""\
        backend be
            option tcplog
    """)

    parsed = parse_config(config)
    assert parsed.backends[0].option_tcplog is True


def test_parse_backend_option_forwardfor() -> None:
    """`option forwardfor` in backend."""

    config = textwrap.dedent("""\
        backend be
            option forwardfor
    """)

    parsed = parse_config(config)
    assert parsed.backends[0].option_forwardfor is True


def test_parse_server_with_extra_params() -> None:
    """Server with extra params."""

    config = textwrap.dedent("""\
        backend be_test
        server s1 10.0.0.1:80 check maxconn 100
    """)

    parsed = parse_config(config)
    srv = parsed.backends[0].servers[0]
    assert srv.check_enabled is True
    assert srv.address == "10.0.0.1"
    assert srv.port == 80


def test_parse_server_fields() -> None:
    """Server with all tier-1/2 fields."""

    cfg = (
        "\nbackend testsrv\n"
        "    server s1 10.0.0.1:80 weight 50 check inter 3s rise 2 fall 3"
        " cookie srv1 send-proxy-v2 slowstart 60s resolvers mydns"
        " resolve-prefer ipv4 on-marked-down shutdown-sessions disabled\n"
    )
    parsed = parse_config(cfg)
    srv = parsed.backends[0].servers[0]

    assert srv.weight == 50
    assert srv.check_enabled is True
    assert srv.inter == "3s"
    assert srv.rise == 2
    assert srv.fall == 3
    assert srv.cookie_value == "srv1"
    assert srv.send_proxy_v2 is True
    assert srv.send_proxy is False
    assert srv.slowstart == "60s"
    assert srv.resolvers_ref == "mydns"
    assert srv.resolve_prefer == "ipv4"
    assert srv.on_marked_down == "shutdown-sessions"
    assert srv.disabled is True


def test_parse_server_maxconn_invalid() -> None:
    """Invalid maxconn falls back to extra_params."""

    config = textwrap.dedent("""\
        backend be
            server s1 10.0.0.1:80 maxconn abc
    """)

    parsed = parse_config(config)
    srv = parsed.backends[0].servers[0]
    assert srv.maxconn is None
    assert srv.extra_params is not None
    assert "maxconn" in srv.extra_params
    assert "abc" in srv.extra_params


def test_parse_server_maxqueue_invalid() -> None:
    """Invalid maxqueue falls back to extra_params."""

    config = textwrap.dedent("""\
        backend be
            server s1 10.0.0.1:80 maxqueue xyz
    """)

    parsed = parse_config(config)
    srv = parsed.backends[0].servers[0]
    assert srv.maxqueue is None
    assert srv.extra_params is not None
    assert "maxqueue" in srv.extra_params
    assert "xyz" in srv.extra_params


def test_parse_server_weight_invalid() -> None:
    """Invalid weight falls back to extra_params."""

    config = textwrap.dedent("""\
        backend be
            server s1 10.0.0.1:80 weight heavy
    """)

    parsed = parse_config(config)
    srv = parsed.backends[0].servers[0]
    assert srv.weight is None
    assert srv.extra_params is not None
    assert "weight" in srv.extra_params
    assert "heavy" in srv.extra_params


def test_parse_server_rise_fall_invalid() -> None:
    """Invalid rise/fall falls back to extra_params."""
    config = textwrap.dedent("""\
        backend be
            server s1 10.0.0.1:80 rise fast fall slow
    """)

    parsed = parse_config(config)
    srv = parsed.backends[0].servers[0]
    assert srv.rise is None
    assert srv.fall is None
    assert srv.extra_params is not None
    assert "rise" in srv.extra_params
    assert "fall" in srv.extra_params


def test_parse_server_send_proxy_v1() -> None:
    """`send-proxy` (v1) parsing."""

    config = textwrap.dedent("""\
        backend be
            server s1 10.0.0.1:80 send-proxy
    """)

    parsed = parse_config(config)
    srv = parsed.backends[0].servers[0]
    assert srv.send_proxy is True
    assert srv.send_proxy_v2 is False


def test_parse_server_unknown_tokens() -> None:
    """Unknown tokens fall back to extra_params."""

    config = textwrap.dedent("""\
        backend be
            server s1 10.0.0.1:80 check ca-file /etc/ssl/ca.pem sni str(example.com)
    """)

    parsed = parse_config(config)
    srv = parsed.backends[0].servers[0]
    assert srv.check_enabled is True
    assert srv.extra_params is not None
    assert "ca-file" in srv.extra_params


def test_parse_server_fastinter_downinter() -> None:
    """`fastinter` / `downinter` token parsing."""

    config = textwrap.dedent("""\
        backend be
            server s1 10.0.0.1:80 check inter 3s fastinter 1s downinter 5s
    """)

    parsed = parse_config(config)
    srv = parsed.backends[0].servers[0]
    assert srv.inter == "3s"
    assert srv.fastinter == "1s"
    assert srv.downinter == "5s"


def test_parse_userlist() -> None:
    """Userlist section is parsed."""

    config = textwrap.dedent("""\
        userlist myusers
        user admin password $6$rounds=5000$salt$hash
        user viewer password $5$otherhash
    """)

    parsed = parse_config(config)
    assert len(parsed.userlists) == 1

    ul = parsed.userlists[0]
    assert ul.name == "myusers"
    assert len(ul.entries) == 2


def test_parse_userlist_inline_comment() -> None:
    """Inline comment is stripped from userlist entries."""

    config = textwrap.dedent("""\
        userlist admins
            user admin password $6$hash  # admin user
    """)

    parsed = parse_config(config)
    assert len(parsed.userlists[0].entries) == 1
    assert parsed.userlists[0].entries[0].username == "admin"


def test_parse_listen() -> None:
    """Listen section is parsed."""

    config = textwrap.dedent("""\
        listen stats
        bind *:8404
        mode http
        stats enable
        stats uri /stats
    """)
    parsed = parse_config(config)
    assert len(parsed.listen_blocks) == 1

    lb = parsed.listen_blocks[0]
    assert lb.name == "stats"
    assert lb.binds == ["*:8404"]


def test_parse_listen_expanded_fields() -> None:
    """Listen block with all expanded fields."""

    config = textwrap.dedent("""\
        listen mysql-proxy
        bind *:3306
        mode tcp
        balance roundrobin
        maxconn 2000
        timeout client 30s
        timeout server 60s
        timeout connect 5s
        default-server inter 3s fall 3 rise 2
        option tcplog
        option forwardfor
        option mysql-check user haproxy
        server db1 10.0.0.1:3306 check
    """)

    parsed = parse_config(config)
    lb = parsed.listen_blocks[0]

    assert lb.name == "mysql-proxy"
    assert lb.binds == ["*:3306"]
    assert lb.mode == "tcp"
    assert lb.balance == "roundrobin"
    assert lb.maxconn == 2000
    assert lb.timeout_client == "30s"
    assert lb.timeout_server == "60s"
    assert lb.timeout_connect == "5s"
    assert lb.default_server_params == "inter 3s fall 3 rise 2"
    assert lb.option_tcplog is True
    assert lb.option_forwardfor is True
    assert lb.option_httplog is False
    assert lb.content is not None
    assert "option mysql-check user haproxy" in lb.content
    assert "server db1 10.0.0.1:3306 check" in lb.content


def test_parse_listen_timeout_server_connect() -> None:
    """Listen block timeout fields."""

    config = textwrap.dedent("""\
        listen proxy
            bind *:3306
            mode tcp
            timeout server 60s
            timeout connect 5s
            default-server inter 3s
    """)

    parsed = parse_config(config)
    lb = parsed.listen_blocks[0]
    assert lb.timeout_server == "60s"
    assert lb.timeout_connect == "5s"
    assert lb.default_server_params == "inter 3s"


def test_parse_listen_maxconn_invalid() -> None:
    """Invalid maxconn in listen block."""

    config = textwrap.dedent("""\
        listen proxy
            bind *:80
            maxconn invalid
    """)

    parsed = parse_config(config)
    lb = parsed.listen_blocks[0]
    assert lb.maxconn is None
    assert lb.content is not None
    assert "maxconn" in lb.content


def test_parse_listen_option_httplog() -> None:
    """`option httplog` in listen block."""

    config = textwrap.dedent("""\
        listen stats
            bind *:8080
            option httplog
    """)

    parsed = parse_config(config)
    assert parsed.listen_blocks[0].option_httplog is True


def test_no_resolvers() -> None:
    """No resolvers in empty config."""

    parsed = parse_config("")
    assert len(parsed.resolvers) == 0


def test_basic_resolver() -> None:
    """Basic resolver section."""

    config = textwrap.dedent("""\
        resolvers mydns
        nameserver dns1 8.8.8.8:53
        nameserver dns2 8.8.4.4:53
    """)

    parsed = parse_config(config)
    assert len(parsed.resolvers) == 1

    r = parsed.resolvers[0]
    assert r.name == "mydns"
    assert len(r.nameservers) == 2
    assert r.nameservers[0].name == "dns1"
    assert r.nameservers[0].address == "8.8.8.8"
    assert r.nameservers[0].port == 53
    assert r.nameservers[1].name == "dns2"


def test_resolver_with_timeouts() -> None:
    """Resolver with timeout fields."""

    config = textwrap.dedent("""\
        resolvers mydns
        nameserver dns1 8.8.8.8:53
        resolve_retries 3
        timeout resolve 1s
        timeout retry 1s
    """)

    parsed = parse_config(config)
    r = parsed.resolvers[0]
    assert r.resolve_retries == 3
    assert r.timeout_resolve == "1s"
    assert r.timeout_retry == "1s"


def test_resolver_with_hold_timers() -> None:
    """Resolver with hold timers."""

    config = textwrap.dedent("""\
        resolvers mydns
        nameserver dns1 8.8.8.8:53
        hold valid 10s
        hold other 30s
        hold refused 30s
        hold timeout 30s
        hold obsolete 30s
    """)

    parsed = parse_config(config)
    r = parsed.resolvers[0]
    assert r.hold_valid == "10s"
    assert r.hold_other == "30s"
    assert r.hold_refused == "30s"
    assert r.hold_timeout == "30s"
    assert r.hold_obsolete == "30s"


def test_resolver_with_hold_nx_aa() -> None:
    """`hold nx` and `hold aa` fields."""

    config = textwrap.dedent("""\
        resolvers mydns
        nameserver dns1 8.8.8.8:53
        hold nx 60s
        hold aa 5s
    """)

    parsed = parse_config(config)
    r = parsed.resolvers[0]
    assert r.hold_nx == "60s"
    assert r.hold_aa == "5s"


def test_resolver_with_parse_resolv_conf() -> None:
    """`parse-resolv-conf` directive."""

    config = textwrap.dedent("""\
        resolvers mydns
        parse-resolv-conf
        nameserver dns1 8.8.8.8:53
    """)

    parsed = parse_config(config)
    assert parsed.resolvers[0].parse_resolv_conf == 1


def test_resolver_without_parse_resolv_conf() -> None:
    """Resolver without `parse-resolv-conf`."""

    config = textwrap.dedent("""\
        resolvers mydns
        nameserver dns1 8.8.8.8:53
    """)

    parsed = parse_config(config)
    assert parsed.resolvers[0].parse_resolv_conf is None


def test_resolver_accepted_payload_size() -> None:
    """`accepted_payload_size` field."""

    config = textwrap.dedent("""\
        resolvers mydns
        nameserver dns1 8.8.8.8:53
        accepted_payload_size 8192
    """)

    parsed = parse_config(config)
    assert parsed.resolvers[0].accepted_payload_size == 8192


def test_resolver_all_fields() -> None:
    """Resolver with every possible field."""

    config = textwrap.dedent("""\
        resolvers full-dns
        nameserver dns1 8.8.8.8:53
        nameserver dns2 1.1.1.1:53
        resolve_retries 5
        timeout resolve 2s
        timeout retry 3s
        hold valid 10s
        hold other 30s
        hold refused 30s
        hold timeout 30s
        hold obsolete 30s
        hold nx 60s
        hold aa 5s
        accepted_payload_size 4096
        parse-resolv-conf
    """)

    parsed = parse_config(config)
    r = parsed.resolvers[0]
    assert r.name == "full-dns"
    assert len(r.nameservers) == 2
    assert r.resolve_retries == 5
    assert r.timeout_resolve == "2s"
    assert r.timeout_retry == "3s"
    assert r.hold_valid == "10s"
    assert r.hold_other == "30s"
    assert r.hold_refused == "30s"
    assert r.hold_timeout == "30s"
    assert r.hold_obsolete == "30s"
    assert r.hold_nx == "60s"
    assert r.hold_aa == "5s"
    assert r.accepted_payload_size == 4096
    assert r.parse_resolv_conf == 1


def test_multiple_resolver_sections() -> None:
    """Multiple resolver sections."""

    config = textwrap.dedent("""\
        resolvers dns-primary
        nameserver ns1 8.8.8.8:53

        resolvers dns-secondary
        nameserver ns2 1.1.1.1:53
    """)

    parsed = parse_config(config)
    assert len(parsed.resolvers) == 2

    names = {r.name for r in parsed.resolvers}
    assert "dns-primary" in names
    assert "dns-secondary" in names


def test_resolver_empty_nameservers() -> None:
    """Resolver with no nameservers."""

    config = textwrap.dedent("""\
        resolvers orphan
    """)

    parsed = parse_config(config)
    r = parsed.resolvers[0]
    assert r.name == "orphan"
    assert len(r.nameservers) == 0


def test_resolver_dataclass_defaults() -> None:
    """`ParsedResolver` default values."""

    r = ParsedResolver(name="test")
    assert r.resolve_retries is None
    assert r.timeout_resolve is None
    assert r.timeout_retry is None
    assert r.hold_valid is None
    assert r.hold_other is None
    assert r.hold_refused is None
    assert r.hold_timeout is None
    assert r.hold_obsolete is None
    assert r.hold_nx is None
    assert r.hold_aa is None
    assert r.accepted_payload_size is None
    assert r.parse_resolv_conf is None
    assert r.comment is None
    assert r.extra_options is None
    assert r.nameservers == []


def test_nameserver_dataclass_defaults() -> None:
    """`ParsedResolverNameserver` default values."""

    ns = ParsedResolverNameserver(name="dns1", address="8.8.8.8")
    assert ns.port == 53
    assert ns.order == 0


def test_resolver_nameserver_non_standard_port() -> None:
    """Nameserver on non-standard port."""

    config = textwrap.dedent("""\
        resolvers mydns
        nameserver dns1 10.0.0.1:5353
    """)

    parsed = parse_config(config)
    assert parsed.resolvers[0].nameservers[0].port == 5353


def test_resolver_with_extra_options() -> None:
    """Unknown directives go to `extra_options`."""

    config = textwrap.dedent("""\
        resolvers mydns
        nameserver dns1 8.8.8.8:53
        resolve_retries 3
        some-future-directive value
    """)

    parsed = parse_config(config)
    r = parsed.resolvers[0]
    assert r.extra_options is not None
    assert "some-future-directive" in r.extra_options


def test_resolver_nameserver_order() -> None:
    """Nameserver order is preserved."""

    config = textwrap.dedent("""\
        resolvers mydns
        nameserver dns1 8.8.8.8:53
        nameserver dns2 8.8.4.4:53
        nameserver dns3 1.1.1.1:53
    """)

    parsed = parse_config(config)
    r = parsed.resolvers[0]
    assert r.nameservers[0].order == 0
    assert r.nameservers[1].order == 1
    assert r.nameservers[2].order == 2


def test_parse_resolver_resolve_retries_invalid() -> None:
    """Invalid `resolve_retries` goes to `extra_options`."""

    config = textwrap.dedent("""\
        resolvers dns
            resolve_retries abc
    """)

    parsed = parse_config(config)
    r = parsed.resolvers[0]
    assert r.resolve_retries is None
    assert r.extra_options is not None
    assert "resolve_retries" in r.extra_options


def test_parse_resolver_accepted_payload_invalid() -> None:
    """Invalid `accepted_payload_size` goes to `extra_options`."""

    config = textwrap.dedent("""\
        resolvers dns
            accepted_payload_size big
    """)

    parsed = parse_config(config)
    r = parsed.resolvers[0]
    assert r.accepted_payload_size is None
    assert r.extra_options is not None
    assert "accepted_payload_size" in r.extra_options


def test_parse_resolver_hold_other_refused_timeout_obsolete() -> None:
    """`hold other/refused/timeout/obsolete` parsing."""

    config = textwrap.dedent("""\
        resolvers dns
            nameserver ns1 8.8.8.8:53
            hold other 10s
            hold refused 20s
            hold timeout 30s
            hold obsolete 40s
    """)

    parsed = parse_config(config)
    r = parsed.resolvers[0]
    assert r.hold_other == "10s"
    assert r.hold_refused == "20s"
    assert r.hold_timeout == "30s"
    assert r.hold_obsolete == "40s"


def test_no_peers() -> None:
    """No peers in empty config."""

    parsed = parse_config("")
    assert len(parsed.peers) == 0


def test_basic_peer_section() -> None:
    """Basic peer section."""

    config = textwrap.dedent("""\
        peers mypeers
        peer haproxy1 10.0.0.1:10000
        peer haproxy2 10.0.0.2:10000
    """)

    parsed = parse_config(config)
    assert len(parsed.peers) == 1

    ps = parsed.peers[0]
    assert ps.name == "mypeers"
    assert len(ps.entries) == 2
    assert ps.entries[0].name == "haproxy1"
    assert ps.entries[0].address == "10.0.0.1"
    assert ps.entries[0].port == 10000
    assert ps.entries[1].name == "haproxy2"


def test_multiple_peer_sections() -> None:
    """Multiple peer sections."""

    config = textwrap.dedent("""\
        peers cluster_a
        peer node1 10.0.1.1:10000

        peers cluster_b
        peer node2 10.0.2.1:10000
        peer node3 10.0.2.2:10000
    """)

    parsed = parse_config(config)
    assert len(parsed.peers) == 2

    names = {p.name for p in parsed.peers}
    assert "cluster_a" in names
    assert "cluster_b" in names


def test_peer_with_extra_options() -> None:
    """Unknown directives go to `extra_options`."""

    config = textwrap.dedent("""\
        peers mypeers
        peer haproxy1 10.0.0.1:10000
        table stick_table type ip size 1m expire 10m
    """)

    parsed = parse_config(config)
    ps = parsed.peers[0]
    assert len(ps.entries) == 1
    assert ps.extra_options is not None
    assert "table" in ps.extra_options or "stick_table" in ps.extra_options


def test_peer_empty_entries() -> None:
    """Peer section with no entries."""

    config = textwrap.dedent("""\
        peers orphan
    """)

    parsed = parse_config(config)
    ps = parsed.peers[0]
    assert ps.name == "orphan"
    assert len(ps.entries) == 0


def test_peer_entry_dataclass_defaults() -> None:
    """`ParsedPeerEntry` default values."""

    pe = ParsedPeerEntry(name="test", address="10.0.0.1", port=10000)
    assert pe.name == "test"
    assert pe.address == "10.0.0.1"
    assert pe.port == 10000


def test_peer_section_dataclass_defaults() -> None:
    """`ParsedPeerSection` default values."""

    ps = ParsedPeerSection(name="cluster")
    assert ps.entries == []
    assert ps.comment is None
    assert ps.extra_options is None
    assert ps.default_bind is None
    assert ps.default_server_options is None


def test_peer_with_default_bind() -> None:
    """`bind` directive in peers section."""

    config = textwrap.dedent("""\
        peers mypeers
        bind :10000 ssl crt /etc/ssl/cert.pem
        peer haproxy1 10.0.0.1:10000
    """)

    parsed = parse_config(config)
    ps = parsed.peers[0]
    assert ps.default_bind is not None
    assert ":10000" in ps.default_bind
    assert "ssl" in ps.default_bind


def test_peer_with_default_server() -> None:
    """`default-server` directive in peers section."""

    config = textwrap.dedent("""\
        peers mypeers
        default-server ssl verify none
        peer haproxy1 10.0.0.1:10000
    """)

    parsed = parse_config(config)
    ps = parsed.peers[0]
    assert ps.default_server_options is not None
    assert "ssl" in ps.default_server_options
    assert "verify none" in ps.default_server_options


def test_peer_with_bind_and_default_server() -> None:
    """Both `bind` and `default-server` in peers."""

    config = textwrap.dedent("""\
        peers mypeers
        bind :10000 ssl crt /etc/ssl/cert.pem
        default-server ssl verify none
        peer haproxy1 10.0.0.1:10000
        peer haproxy2 10.0.0.2:10000
    """)

    parsed = parse_config(config)
    ps = parsed.peers[0]
    assert ps.default_bind is not None
    assert ps.default_server_options is not None
    assert len(ps.entries) == 2


def test_peer_with_ipv6_address() -> None:
    """Peer with IPv6 address."""

    config = textwrap.dedent("""\
        peers v6cluster
        peer node1 ::1:10000
    """)

    parsed = parse_config(config)
    ps = parsed.peers[0]
    assert len(ps.entries) == 1
    assert ps.entries[0].address == "::1"


def test_three_peers_in_section() -> None:
    """Three peers in one section."""

    config = textwrap.dedent("""\
        peers mypeers
        peer haproxy1 10.2.100.1:10000
        peer haproxy2 10.2.100.2:10000
        peer haproxy3 10.2.100.3:10000
    """)

    parsed = parse_config(config)
    ps = parsed.peers[0]
    assert len(ps.entries) == 3

    addrs = [e.address for e in ps.entries]
    assert "10.2.100.1" in addrs
    assert "10.2.100.2" in addrs
    assert "10.2.100.3" in addrs


def test_parse_peer_default_server() -> None:
    """`default-server` in peers parser."""

    config = textwrap.dedent("""\
        peers cluster
            default-server ssl verify none
            peer node1 10.0.0.1:10000
    """)

    parsed = parse_config(config)
    assert parsed.peers[0].default_server_options == "ssl verify none"


def test_no_http_errors() -> None:
    """No http-errors in empty config."""

    parsed = parse_config("")
    assert len(parsed.http_errors) == 0


def test_basic_errorfile_section() -> None:
    """Basic errorfile section."""

    config = textwrap.dedent("""\
        http-errors custom-errors
        errorfile 503 /etc/haproxy/errors/503.http
        errorfile 504 /etc/haproxy/errors/504.http
    """)

    parsed = parse_config(config)
    assert len(parsed.http_errors) == 1

    he = parsed.http_errors[0]
    assert he.name == "custom-errors"
    assert len(he.entries) == 2
    assert he.entries[0].status_code == 503
    assert he.entries[0].type == "errorfile"
    assert he.entries[0].value == "/etc/haproxy/errors/503.http"
    assert he.entries[1].status_code == 504


def test_errorloc302_type() -> None:
    """`errorloc302` type."""

    config = textwrap.dedent("""\
        http-errors redirects
        errorloc302 503 https://maintenance.example.com
    """)

    parsed = parse_config(config)
    he = parsed.http_errors[0]
    assert he.entries[0].type == "errorloc302"
    assert he.entries[0].status_code == 503
    assert he.entries[0].value == "https://maintenance.example.com"


def test_errorloc303_type() -> None:
    """`errorloc303` type."""

    config = textwrap.dedent("""\
        http-errors redirect303
        errorloc303 500 https://error.example.com/500
    """)

    parsed = parse_config(config)
    assert parsed.http_errors[0].entries[0].type == "errorloc303"


def test_errorloc_type() -> None:
    """`errorloc` type."""

    config = textwrap.dedent("""\
        http-errors redirect_generic
        errorloc 502 https://sorry.example.com
    """)

    parsed = parse_config(config)
    assert parsed.http_errors[0].entries[0].type == "errorloc"


def test_multiple_http_errors_sections() -> None:
    """Multiple http-errors sections."""

    config = textwrap.dedent("""\
        http-errors custom-errors
        errorfile 503 /etc/haproxy/errors/503.http

        http-errors redirect-errors
        errorloc302 503 https://maintenance.example.com
    """)

    parsed = parse_config(config)
    assert len(parsed.http_errors) == 2

    names = {h.name for h in parsed.http_errors}
    assert "custom-errors" in names
    assert "redirect-errors" in names


def test_many_errorfiles() -> None:
    """Full set of errorfiles."""

    config = textwrap.dedent("""\
        http-errors full-set
        errorfile 400 /etc/haproxy/errors/400.http
        errorfile 403 /etc/haproxy/errors/403.http
        errorfile 408 /etc/haproxy/errors/408.http
        errorfile 500 /etc/haproxy/errors/500.http
        errorfile 502 /etc/haproxy/errors/502.http
        errorfile 503 /etc/haproxy/errors/503.http
        errorfile 504 /etc/haproxy/errors/504.http
    """)

    parsed = parse_config(config)
    he = parsed.http_errors[0]
    assert len(he.entries) == 7

    codes = [e.status_code for e in he.entries]
    assert codes == [400, 403, 408, 500, 502, 503, 504]
    assert all(e.type == "errorfile" for e in he.entries)


def test_http_error_entry_dataclass() -> None:
    """`ParsedHttpErrorEntry` defaults."""

    entry = ParsedHttpErrorEntry(status_code=503, type="errorfile", value="/errors/503.http")
    assert entry.status_code == 503
    assert entry.type == "errorfile"
    assert entry.value == "/errors/503.http"


def test_http_errors_section_dataclass_defaults() -> None:
    """`ParsedHttpErrorsSection` defaults."""

    section = ParsedHttpErrorsSection(name="test")
    assert section.entries == []
    assert section.comment is None
    assert section.extra_options is None


def test_http_errors_with_extra_options() -> None:
    """Unknown directives go to `extra_options`."""

    config = textwrap.dedent("""\
        http-errors custom-errors
        errorfile 503 /etc/haproxy/errors/503.http
        log global
        custom-directive value
    """)

    parsed = parse_config(config)
    he = parsed.http_errors[0]
    assert he.extra_options is not None
    assert "log global" in he.extra_options or "custom-directive" in he.extra_options


def test_http_errors_mixed_types() -> None:
    """Section with mixed errorfile and errorloc types."""

    config = textwrap.dedent("""\
        http-errors mixed
        errorfile 400 /etc/haproxy/errors/400.http
        errorloc302 503 https://maintenance.example.com
        errorloc303 502 https://error.example.com/502
        errorfile 504 /etc/haproxy/errors/504.http
    """)

    parsed = parse_config(config)
    he = parsed.http_errors[0]
    assert len(he.entries) == 4

    types = [e.type for e in he.entries]
    assert types == ["errorfile", "errorloc302", "errorloc303", "errorfile"]


def test_no_caches() -> None:
    """No caches in empty config."""

    parsed = parse_config("")
    assert len(parsed.caches) == 0


def test_basic_cache() -> None:
    """Basic cache section."""

    config = textwrap.dedent("""\
        cache my_cache
        total-max-size 4
        max-object-size 524288
        max-age 60
    """)

    parsed = parse_config(config)
    assert len(parsed.caches) == 1

    c = parsed.caches[0]
    assert c.name == "my_cache"
    assert c.total_max_size == 4
    assert c.max_object_size == 524288
    assert c.max_age == 60
    assert c.max_secondary_entries is None
    assert c.process_vary is None


def test_cache_all_fields() -> None:
    """Cache with all fields populated."""

    config = textwrap.dedent("""\
        cache static-cache
        total-max-size 64
        max-object-size 524288
        max-age 3600
        max-secondary-entries 10
        process-vary 1
    """)

    parsed = parse_config(config)
    c = parsed.caches[0]
    assert c.total_max_size == 64
    assert c.max_object_size == 524288
    assert c.max_age == 3600
    assert c.max_secondary_entries == 10
    assert c.process_vary == 1


def test_cache_minimal() -> None:
    """Minimal cache: only `total-max-size`."""

    config = textwrap.dedent("""\
        cache tiny
        total-max-size 1
    """)

    parsed = parse_config(config)
    c = parsed.caches[0]
    assert c.total_max_size == 1
    assert c.max_object_size is None
    assert c.max_age is None


def test_multiple_caches() -> None:
    """Multiple cache sections."""

    config = textwrap.dedent("""\
        cache cache_a
        total-max-size 32
        max-age 300

        cache cache_b
        total-max-size 64
        max-age 600
    """)

    parsed = parse_config(config)
    assert len(parsed.caches) == 2

    names = {c.name for c in parsed.caches}
    assert "cache_a" in names
    assert "cache_b" in names


def test_cache_with_extra_options() -> None:
    """Unknown directives go to `extra_options`."""

    config = textwrap.dedent("""\
        cache my_cache
        total-max-size 4
        max-age 60
        some-future-directive value
    """)

    parsed = parse_config(config)
    c = parsed.caches[0]
    assert c.extra_options is not None
    assert "some-future-directive" in c.extra_options


def test_cache_large_values() -> None:
    """Cache with large MB sizes."""

    config = textwrap.dedent("""\
        cache large
        total-max-size 1024
        max-object-size 10485760
        max-age 86400
    """)

    parsed = parse_config(config)
    c = parsed.caches[0]
    assert c.total_max_size == 1024
    assert c.max_object_size == 10485760
    assert c.max_age == 86400


def test_cache_section_dataclass_defaults() -> None:
    """`ParsedCacheSection` default values."""

    c = ParsedCacheSection(name="test")
    assert c.total_max_size is None
    assert c.max_object_size is None
    assert c.max_age is None
    assert c.max_secondary_entries is None
    assert c.process_vary is None
    assert c.comment is None
    assert c.extra_options is None


def test_process_vary_off() -> None:
    """`process-vary 0`."""

    config = textwrap.dedent("""\
        cache novary
        total-max-size 4
        process-vary 0
    """)

    parsed = parse_config(config)
    assert parsed.caches[0].process_vary == 0


def test_parse_cache_total_max_size_invalid() -> None:
    """Invalid `total-max-size` goes to `extra_options`."""

    config = textwrap.dedent("""\
        cache c1
            total-max-size big
    """)

    parsed = parse_config(config)
    c = parsed.caches[0]
    assert c.total_max_size is None
    assert c.extra_options is not None
    assert "total-max-size" in c.extra_options


def test_parse_cache_max_object_size_invalid() -> None:
    """Invalid `max-object-size` goes to `extra_options`."""

    config = textwrap.dedent("""\
        cache c1
            max-object-size huge
    """)

    parsed = parse_config(config)
    c = parsed.caches[0]
    assert c.max_object_size is None
    assert c.extra_options is not None
    assert "max-object-size" in c.extra_options


def test_parse_cache_max_age_invalid() -> None:
    """Invalid `max-age` goes to `extra_options`."""

    config = textwrap.dedent("""\
        cache c1
            max-age forever
    """)

    parsed = parse_config(config)
    c = parsed.caches[0]
    assert c.max_age is None
    assert c.extra_options is not None
    assert "max-age" in c.extra_options


def test_parse_cache_max_secondary_entries_invalid() -> None:
    """Invalid `max-secondary-entries` goes to `extra_options`."""

    config = textwrap.dedent("""\
        cache c1
            max-secondary-entries many
    """)

    parsed = parse_config(config)
    c = parsed.caches[0]
    assert c.max_secondary_entries is None
    assert c.extra_options is not None
    assert "max-secondary-entries" in c.extra_options


def test_parse_cache_process_vary_invalid() -> None:
    """Invalid `process-vary` goes to `extra_options`."""

    config = textwrap.dedent("""\
        cache c1
            process-vary yes
    """)

    parsed = parse_config(config)
    c = parsed.caches[0]
    assert c.process_vary is None
    assert c.extra_options is not None
    assert "process-vary" in c.extra_options


def test_basic_mailer_section() -> None:
    """Basic mailer section."""

    config = MINIMAL_CONFIG + textwrap.dedent("""
            mailers mymailers
            mailer smtp1 smtp.example.com:25
        """)

    parsed = parse_config(config)
    assert len(parsed.mailers) == 1
    assert parsed.mailers[0].name == "mymailers"
    assert len(parsed.mailers[0].entries) == 1
    assert parsed.mailers[0].entries[0].name == "smtp1"
    assert parsed.mailers[0].entries[0].address == "smtp.example.com"
    assert parsed.mailers[0].entries[0].port == 25


def test_mailer_with_timeout() -> None:
    """Mailer with timeout."""

    config = MINIMAL_CONFIG + textwrap.dedent("""
            mailers alert-mailers
            timeout mail 10s
            mailer smtp1 smtp.internal.net:587
        """)

    parsed = parse_config(config)
    ms = parsed.mailers[0]
    assert ms.timeout_mail == "10s"
    assert ms.entries[0].port == 587


def test_multiple_mailer_entries() -> None:
    """Multiple mailer entries."""

    config = MINIMAL_CONFIG + textwrap.dedent("""
            mailers multi-smtp
            timeout mail 30s
            mailer primary mail.primary.com:25
            mailer secondary mail.secondary.com:587
            mailer tertiary mail.tertiary.com:2525
    """)

    parsed = parse_config(config)
    ms = parsed.mailers[0]
    assert len(ms.entries) == 3
    assert ms.entries[0].name == "primary"
    assert ms.entries[1].name == "secondary"
    assert ms.entries[2].name == "tertiary"
    assert ms.entries[0].order == 0
    assert ms.entries[1].order == 1
    assert ms.entries[2].order == 2


def test_multiple_mailer_sections() -> None:
    """Multiple mailer sections."""

    config = MINIMAL_CONFIG + textwrap.dedent("""
            mailers primary-mailers
            mailer smtp1 smtp1.example.com:25

            mailers backup-mailers
            timeout mail 5s
            mailer smtp-bak backup.example.com:587
        """)

    parsed = parse_config(config)
    assert len(parsed.mailers) == 2
    assert parsed.mailers[0].name == "primary-mailers"
    assert parsed.mailers[1].name == "backup-mailers"
    assert parsed.mailers[1].timeout_mail == "5s"


def test_mailer_ignores_comments() -> None:
    """Comments are ignored in mailer sections."""

    config = MINIMAL_CONFIG + textwrap.dedent("""
            mailers commented
            # This is a comment
            timeout mail 10s
            mailer smtp1 smtp.example.com:25
            # Another comment
            mailer smtp2 backup.example.com:587
        """)

    parsed = parse_config(config)
    ms = parsed.mailers[0]
    assert len(ms.entries) == 2
    assert ms.timeout_mail == "10s"


def test_mailer_empty_entries() -> None:
    """Mailer section with no entries."""

    config = MINIMAL_CONFIG + textwrap.dedent("""
            mailers empty-mailers
            timeout mail 15s
        """)

    parsed = parse_config(config)
    ms = parsed.mailers[0]
    assert ms.name == "empty-mailers"
    assert ms.timeout_mail == "15s"
    assert len(ms.entries) == 0


def test_mailer_entry_dataclass_defaults() -> None:
    """`ParsedMailerEntry` default values."""

    entry = ParsedMailerEntry(name="test", address="localhost")
    assert entry.port == 25
    assert entry.order == 0


def test_mailer_section_dataclass_defaults() -> None:
    """`ParsedMailerSection` default values."""

    section = ParsedMailerSection(name="test")
    assert section.timeout_mail is None
    assert section.comment is None
    assert section.extra_options is None
    assert section.entries == []


def test_mailer_with_extra_options() -> None:
    """Unknown directives go to `extra_options`."""

    config = MINIMAL_CONFIG + textwrap.dedent("""
            mailers mymailers
            timeout mail 10s
            mailer smtp1 smtp.example.com:25
            log global
            custom-directive value
        """)

    parsed = parse_config(config)
    ms = parsed.mailers[0]
    assert ms.extra_options is not None
    assert "log global" in ms.extra_options or "custom-directive" in ms.extra_options


def test_mailer_high_port() -> None:
    """Mailer on a high port."""

    config = MINIMAL_CONFIG + textwrap.dedent("""
            mailers custom-port
            mailer relay relay.internal.net:2525
        """)

    parsed = parse_config(config)
    assert parsed.mailers[0].entries[0].port == 2525
    assert parsed.mailers[0].entries[0].address == "relay.internal.net"


def test_mailer_smtp_auth_metadata() -> None:
    """`_pm_mailer_auth` metadata comment for SMTP authentication."""

    config = MINIMAL_CONFIG + textwrap.dedent("""
            mailers auth-mailers
            timeout mail 10s
            mailer smtp1 smtp.gmail.com:587
            # _pm_mailer_auth smtp1 smtp_auth=true smtp_user=user@gmail.com smtp_password=app-pass use_tls=false use_starttls=true
        """)

    parsed = parse_config(config)
    ms = parsed.mailers[0]
    assert len(ms.entries) == 1

    e = ms.entries[0]
    assert e.smtp_auth is True
    assert e.smtp_user == "user@gmail.com"
    assert e.smtp_password == "app-pass"
    assert e.use_tls is False
    assert e.use_starttls is True


def test_mailer_smtp_auth_multiple_entries() -> None:
    """SMTP auth metadata for multiple mailer entries."""

    config = MINIMAL_CONFIG + textwrap.dedent("""
            mailers multi-auth
            mailer smtp1 smtp.example.com:587
            # _pm_mailer_auth smtp1 smtp_auth=true smtp_user=admin smtp_password=secret use_tls=true use_starttls=false
            mailer smtp2 backup.example.com:25
        """)

    parsed = parse_config(config)
    ms = parsed.mailers[0]
    assert len(ms.entries) == 2
    assert ms.entries[0].smtp_auth is True
    assert ms.entries[0].smtp_user == "admin"
    assert ms.entries[0].use_tls is True
    assert ms.entries[1].smtp_auth is False
    assert ms.entries[1].smtp_user is None


def test_mailer_no_auth_metadata() -> None:
    """Entries without auth metadata keep defaults."""

    config = MINIMAL_CONFIG + textwrap.dedent("""
            mailers plain-mailers
            mailer relay relay.example.com:25
    """)

    parsed = parse_config(config)
    e = parsed.mailers[0].entries[0]
    assert e.smtp_auth is False
    assert e.smtp_user is None
    assert e.smtp_password is None
    assert e.use_tls is False
    assert e.use_starttls is False


def test_mailer_entry_dataclass_smtp_auth_defaults() -> None:
    """`ParsedMailerEntry` SMTP auth defaults."""

    entry = ParsedMailerEntry(name="test", address="localhost")
    assert entry.smtp_auth is False
    assert entry.smtp_user is None
    assert entry.smtp_password is None
    assert entry.use_tls is False
    assert entry.use_starttls is False


def test_mailer_smtp_auth_tls_only() -> None:
    """TLS without STARTTLS."""

    config = MINIMAL_CONFIG + textwrap.dedent("""
            mailers tls-mailers
            mailer smtp1 smtp.example.com:465
            # _pm_mailer_auth smtp1 smtp_auth=true smtp_user=user smtp_password=pass use_tls=true use_starttls=false
        """)

    parsed = parse_config(config)
    e = parsed.mailers[0].entries[0]
    assert e.smtp_auth is True
    assert e.use_tls is True
    assert e.use_starttls is False


def test_example_config_integration() -> None:
    """Integration test: parse example config with multiple section types."""

    config = textwrap.dedent("""\
        global
        log 127.0.0.1 local0

        defaults
        mode http

        peers mypeers
        peer haproxy1 10.2.100.1:10000
        peer haproxy2 10.2.100.2:10000
        peer haproxy3 10.2.100.3:10000

        http-errors custom-errors
        errorfile 400 /etc/haproxy/errors/400.http
        errorfile 503 /etc/haproxy/errors/503.http

        http-errors redirect-errors
        errorloc302 503 https://maintenance.example.com

        cache static-cache
        total-max-size 64
        max-object-size 524288
        max-age 3600
        max-secondary-entries 10
        process-vary 1
    """)

    parsed = parse_config(config)
    assert len(parsed.peers) == 1
    assert len(parsed.peers[0].entries) == 3
    assert len(parsed.http_errors) == 2
    assert len(parsed.caches) == 1
    assert parsed.caches[0].total_max_size == 64


def test_resolver_comment_parsed() -> None:
    """Resolver section comment is captured from initial `#` lines."""

    config = textwrap.dedent("""\
        resolvers opendns
            # Cisco OpenDNS
            nameserver dns1 208.67.222.222:53
            resolve_retries 3
            timeout resolve 1s
            timeout retry 1s
    """)
    parsed = parse_config(config)
    assert len(parsed.resolvers) == 1
    assert parsed.resolvers[0].comment == "Cisco OpenDNS"


def test_resolver_multiline_comment_parsed() -> None:
    """Multi-line resolver comment is captured."""

    config = textwrap.dedent("""\
        resolvers mydns
            # Primary DNS
            # Used for all lookups
            nameserver dns1 8.8.8.8:53
    """)
    parsed = parse_config(config)
    assert parsed.resolvers[0].comment == "Primary DNS\nUsed for all lookups"


def test_resolver_no_comment() -> None:
    """Resolver without comment has `comment=None`."""

    config = textwrap.dedent("""\
        resolvers mydns
            nameserver dns1 8.8.8.8:53
    """)
    parsed = parse_config(config)
    assert parsed.resolvers[0].comment is None


def test_peer_comment_parsed() -> None:
    """Peer section comment is captured."""

    config = textwrap.dedent("""\
        peers mycluster
            # HA cluster peers
            peer node1 10.0.0.1:10000
    """)
    parsed = parse_config(config)
    assert len(parsed.peers) == 1
    assert parsed.peers[0].comment == "HA cluster peers"


def test_mailer_comment_parsed() -> None:
    """Mailer section comment is captured."""

    config = textwrap.dedent("""\
        mailers alerts
            # Alert mailers
            timeout mail 10s
            mailer smtp1 smtp.example.com:25
    """)
    parsed = parse_config(config)
    assert len(parsed.mailers) == 1
    assert parsed.mailers[0].comment == "Alert mailers"


def test_mailer_comment_skips_pm_metadata() -> None:
    """Mailer comment does not capture `_pm_mailer_auth` metadata."""

    config = textwrap.dedent("""\
        mailers mymailers
            # _pm_mailer_auth smtp1 smtp_auth=true smtp_user=user@example.com smtp_password=secret use_tls=false use_starttls=true
            timeout mail 10s
            mailer smtp1 smtp.example.com:587
    """)
    parsed = parse_config(config)
    assert parsed.mailers[0].comment is None


def test_http_errors_comment_parsed() -> None:
    """Http-errors section comment is captured."""

    config = textwrap.dedent("""\
        http-errors custom
            # Custom error pages
            errorfile 503 /errors/503.http
    """)
    parsed = parse_config(config)
    assert len(parsed.http_errors) == 1
    assert parsed.http_errors[0].comment == "Custom error pages"


def test_cache_comment_parsed() -> None:
    """Cache section comment is captured."""

    config = textwrap.dedent("""\
        cache static
            # Static asset cache
            total-max-size 4
            max-object-size 524288
            max-age 60
    """)
    parsed = parse_config(config)
    assert len(parsed.caches) == 1
    assert parsed.caches[0].comment == "Static asset cache"


def test_frontend_comment_parsed() -> None:
    """Frontend section comment is captured."""

    config = textwrap.dedent("""\
        frontend fe_web
            # Main web frontend
            bind *:80
            mode http
            default_backend be_web
    """)
    parsed = parse_config(config)
    assert len(parsed.frontends) == 1
    assert parsed.frontends[0].comment == "Main web frontend"


def test_backend_comment_parsed() -> None:
    """Backend section comment is captured."""

    config = textwrap.dedent("""\
        backend be_web
            # Application servers
            mode http
            balance roundrobin
            server web1 10.0.0.1:8080 check
    """)
    parsed = parse_config(config)
    assert len(parsed.backends) == 1
    assert parsed.backends[0].comment == "Application servers"


def test_listen_comment_parsed() -> None:
    """Listen block comment is captured."""

    config = textwrap.dedent("""\
        listen stats
            # Stats dashboard
            bind *:8404
            mode http
            stats enable
    """)
    parsed = parse_config(config)
    assert len(parsed.listen_blocks) == 1
    assert parsed.listen_blocks[0].comment == "Stats dashboard"
