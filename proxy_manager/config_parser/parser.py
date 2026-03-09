"""
HAProxy configuration parser
=============================

Parses HAProxy config text into structured data suitable for database import.
"""

import contextlib
import re
from dataclasses import dataclass, field


@dataclass
class ParsedDirective:
    """A single directive line."""

    directive: str
    value: str = ""
    comment: str | None = None
    order: int = 0


@dataclass
class ParsedServer:
    """A server directive within a backend."""

    name: str
    address: str
    port: int
    check_enabled: bool = False
    maxconn: int | None = None
    maxqueue: int | None = None
    extra_params: str | None = None
    order: int = 0
    # Tier-1/2 fields
    weight: int | None = None
    ssl_enabled: bool = False
    ssl_verify: str | None = None
    backup: bool = False
    inter: str | None = None
    fastinter: str | None = None
    downinter: str | None = None
    rise: int | None = None
    fall: int | None = None
    cookie_value: str | None = None
    send_proxy: bool = False
    send_proxy_v2: bool = False
    slowstart: str | None = None
    resolve_prefer: str | None = None
    resolvers_ref: str | None = None
    on_marked_down: str | None = None
    disabled: bool = False


@dataclass
class ParsedAcl:
    """An ACL + use_backend / redirect pair."""

    domain: str
    backend_name: str = ""
    acl_match_type: str = "hdr_dom"
    is_redirect: bool = False
    redirect_target: str | None = None
    redirect_code: int = 308
    comment: str | None = None
    order: int = 0
    enabled: bool = True


@dataclass
class ParsedUserlistEntry:
    """A user entry in a userlist."""

    username: str
    password_hash: str
    order: int = 0


@dataclass
class ParsedUserlist:
    """A userlist block."""

    name: str
    entries: list[ParsedUserlistEntry] = field(default_factory=list)


@dataclass
class ParsedBackend:
    """A backend block."""

    name: str
    mode: str | None = None
    balance: str | None = None
    option_forwardfor: bool = False
    option_redispatch: bool = False
    retries: int | None = None
    retry_on: str | None = None
    auth_userlist: str | None = None
    health_check_enabled: bool = False
    health_check_method: str | None = None
    health_check_uri: str | None = None
    errorfile: str | None = None
    comment: str | None = None
    extra_options: str | None = None
    servers: list[ParsedServer] = field(default_factory=list)
    # Tier-1 fields
    cookie: str | None = None
    timeout_server: str | None = None
    timeout_connect: str | None = None
    timeout_queue: str | None = None
    http_check_expect: str | None = None
    default_server_options: str | None = None
    http_reuse: str | None = None
    hash_type: str | None = None
    option_httplog: bool = False
    option_tcplog: bool = False
    compression_algo: str | None = None
    compression_type: str | None = None


@dataclass
class ParsedFrontend:
    """A frontend block."""

    name: str
    default_backend: str | None = None
    mode: str = "http"
    comment: str | None = None
    binds: list[str] = field(default_factory=list)
    options: list[ParsedDirective] = field(default_factory=list)
    acls: list[ParsedAcl] = field(default_factory=list)
    # Tier-1 fields
    timeout_client: str | None = None
    timeout_http_request: str | None = None
    timeout_http_keep_alive: str | None = None
    maxconn: int | None = None
    option_httplog: bool = False
    option_tcplog: bool = False
    option_forwardfor: bool = False
    compression_algo: str | None = None
    compression_type: str | None = None


@dataclass
class ParsedListenBlock:
    """A listen block."""

    name: str
    binds: list[str] = field(default_factory=list)
    mode: str = "http"
    balance: str | None = None
    maxconn: int | None = None
    timeout_client: str | None = None
    timeout_server: str | None = None
    timeout_connect: str | None = None
    default_server_params: str | None = None
    option_httplog: bool = False
    option_tcplog: bool = False
    option_forwardfor: bool = False
    content: str | None = None
    comment: str | None = None


@dataclass
class ParsedResolverNameserver:
    """A nameserver entry in a resolvers block."""

    name: str
    address: str
    port: int = 53
    order: int = 0


@dataclass
class ParsedResolver:
    """A resolvers block."""

    name: str
    resolve_retries: int | None = None
    timeout_resolve: str | None = None
    timeout_retry: str | None = None
    hold_valid: str | None = None
    hold_other: str | None = None
    hold_refused: str | None = None
    hold_timeout: str | None = None
    hold_obsolete: str | None = None
    hold_nx: str | None = None
    hold_aa: str | None = None
    accepted_payload_size: int | None = None
    parse_resolv_conf: int | None = None
    comment: str | None = None
    extra_options: str | None = None
    nameservers: list[ParsedResolverNameserver] = field(default_factory=list)


@dataclass
class ParsedPeerEntry:
    """A peer entry in a peers block."""

    name: str
    address: str
    port: int = 10000
    order: int = 0


@dataclass
class ParsedPeerSection:
    """A peers block."""

    name: str
    comment: str | None = None
    extra_options: str | None = None
    default_bind: str | None = None
    default_server_options: str | None = None
    entries: list[ParsedPeerEntry] = field(default_factory=list)


@dataclass
class ParsedMailerEntry:
    """A mailer entry in a mailers block."""

    name: str
    address: str
    port: int = 25
    smtp_auth: bool = False
    smtp_user: str | None = None
    smtp_password: str | None = None
    use_tls: bool = False
    use_starttls: bool = False
    order: int = 0


@dataclass
class ParsedMailerSection:
    """A mailers block."""

    name: str
    timeout_mail: str | None = None
    comment: str | None = None
    extra_options: str | None = None
    entries: list[ParsedMailerEntry] = field(default_factory=list)


@dataclass
class ParsedHttpErrorEntry:
    """An error entry in an http-errors block."""

    status_code: int
    type: str = "errorfile"
    value: str = ""
    order: int = 0


@dataclass
class ParsedHttpErrorsSection:
    """An http-errors block."""

    name: str
    comment: str | None = None
    extra_options: str | None = None
    entries: list[ParsedHttpErrorEntry] = field(default_factory=list)


@dataclass
class ParsedCacheSection:
    """A cache block."""

    name: str
    total_max_size: int | None = None
    max_object_size: int | None = None
    max_age: int | None = None
    max_secondary_entries: int | None = None
    process_vary: int | None = None
    comment: str | None = None
    extra_options: str | None = None


@dataclass
class ParsedSslCertificate:
    """An SSL certificate extracted from bind lines."""

    domain: str  # derived from cert path or section
    cert_path: str | None = None
    key_path: str | None = None
    fullchain_path: str | None = None
    provider: str = "manual"  # imported certs are manual
    status: str = "active"
    challenge_type: str = "http-01"
    auto_renew: bool = False
    alt_domains: str | None = None
    comment: str | None = None


@dataclass
class ParsedConfig:
    """Complete parsed HAProxy configuration."""

    global_settings: list[ParsedDirective] = field(default_factory=list)
    default_settings: list[ParsedDirective] = field(default_factory=list)
    userlists: list[ParsedUserlist] = field(default_factory=list)
    frontends: list[ParsedFrontend] = field(default_factory=list)
    backends: list[ParsedBackend] = field(default_factory=list)
    listen_blocks: list[ParsedListenBlock] = field(default_factory=list)
    resolvers: list[ParsedResolver] = field(default_factory=list)
    peers: list[ParsedPeerSection] = field(default_factory=list)
    mailers: list[ParsedMailerSection] = field(default_factory=list)
    http_errors: list[ParsedHttpErrorsSection] = field(default_factory=list)
    caches: list[ParsedCacheSection] = field(default_factory=list)
    ssl_certificates: list[ParsedSslCertificate] = field(default_factory=list)


# Regex patterns
_SECTION_RE = re.compile(
    r"^(global|defaults|frontend|backend|listen|userlist|resolvers|peers|mailers|http-errors|cache)\s*(.*?)\s*$",
    re.IGNORECASE,
)
_SERVER_RE = re.compile(r"^server\s+(\S+)\s+(\S+):(\d+)\s*(.*)?$", re.IGNORECASE)
_ACL_HDR_RE = re.compile(
    r"^acl\s+\S+\s+(hdr_dom|hdr)\(Host\)\s+-i\s+(\S+)$",
    re.IGNORECASE,
)
_USE_BACKEND_RE = re.compile(r"^use_backend\s+(\S+)\s+if\s+", re.IGNORECASE)
_REDIRECT_RE = re.compile(r"^redirect\s+prefix\s+(\S+)\s+code\s+(\d+)\s+if\s+", re.IGNORECASE)
_BIND_RE = re.compile(r"^bind\s+", re.IGNORECASE)
_SSL_CRT_RE = re.compile(r'\bssl\b.*?\bcrt\s+(?:"([^"]+)"|\'([^\']+)\'|(\S+))', re.IGNORECASE)
_COMMENT_BLOCK_RE = re.compile(r"^\s*#\s*(.*)")


def _strip_inline_comment(line: str) -> tuple[str, str | None]:
    """Split a line into content and inline comment."""

    quote_char: str | None = None
    for i, ch in enumerate(line):
        if quote_char:
            if ch == quote_char:
                quote_char = None
        elif ch in ('"', "'"):
            quote_char = ch
        elif ch == "#" and i > 0:
            return line[:i].rstrip(), line[i + 1 :].strip()

    return line, None


def _parse_server_line(text: str) -> ParsedServer | None:
    """Parse a 'server' directive into a ParsedServer."""

    m = _SERVER_RE.match(text)
    if not m:
        return None

    name = m.group(1)
    address = m.group(2)
    port = int(m.group(3))
    rest = (m.group(4) or "").strip()

    check_enabled = False
    maxconn = None
    maxqueue = None
    weight = None
    ssl_enabled = False
    ssl_verify = None
    backup = False
    inter = None
    fastinter = None
    downinter = None
    rise = None
    fall = None
    cookie_value = None
    send_proxy = False
    send_proxy_v2 = False
    slowstart = None
    resolve_prefer = None
    resolvers_ref = None
    on_marked_down = None
    disabled = False
    extra_parts = []

    tokens = rest.split()
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        tok_lower = tok.lower()

        if tok_lower == "check":
            check_enabled = True
            i += 1
        elif tok_lower == "maxconn" and i + 1 < len(tokens):
            try:
                maxconn = int(tokens[i + 1])
            except ValueError:
                extra_parts.append(tok)
                extra_parts.append(tokens[i + 1])
            i += 2
        elif tok_lower == "maxqueue" and i + 1 < len(tokens):
            try:
                maxqueue = int(tokens[i + 1])
            except ValueError:
                extra_parts.append(tok)
                extra_parts.append(tokens[i + 1])
            i += 2
        elif tok_lower == "weight" and i + 1 < len(tokens):
            try:
                weight = int(tokens[i + 1])
            except ValueError:
                extra_parts.append(tok)
                extra_parts.append(tokens[i + 1])
            i += 2
        elif tok_lower == "ssl":
            ssl_enabled = True
            i += 1
        elif tok_lower == "verify" and i + 1 < len(tokens):
            ssl_verify = tokens[i + 1]
            i += 2
        elif tok_lower == "backup":
            backup = True
            i += 1
        elif tok_lower == "inter" and i + 1 < len(tokens):
            inter = tokens[i + 1]
            i += 2
        elif tok_lower == "fastinter" and i + 1 < len(tokens):
            fastinter = tokens[i + 1]
            i += 2
        elif tok_lower == "downinter" and i + 1 < len(tokens):
            downinter = tokens[i + 1]
            i += 2
        elif tok_lower == "rise" and i + 1 < len(tokens):
            try:
                rise = int(tokens[i + 1])
            except ValueError:
                extra_parts.append(tok)
                extra_parts.append(tokens[i + 1])
            i += 2
        elif tok_lower == "fall" and i + 1 < len(tokens):
            try:
                fall = int(tokens[i + 1])
            except ValueError:
                extra_parts.append(tok)
                extra_parts.append(tokens[i + 1])
            i += 2
        elif tok_lower == "cookie" and i + 1 < len(tokens):
            cookie_value = tokens[i + 1]
            i += 2
        elif tok_lower == "send-proxy-v2":
            send_proxy_v2 = True
            i += 1
        elif tok_lower == "send-proxy":
            send_proxy = True
            i += 1
        elif tok_lower == "slowstart" and i + 1 < len(tokens):
            slowstart = tokens[i + 1]
            i += 2
        elif tok_lower == "resolve-prefer" and i + 1 < len(tokens):
            resolve_prefer = tokens[i + 1]
            i += 2
        elif tok_lower == "resolvers" and i + 1 < len(tokens):
            resolvers_ref = tokens[i + 1]
            i += 2
        elif tok_lower == "on-marked-down" and i + 1 < len(tokens):
            on_marked_down = tokens[i + 1]
            i += 2
        elif tok_lower == "disabled":
            disabled = True
            i += 1
        else:
            extra_parts.append(tok)
            i += 1

    extra = " ".join(extra_parts) if extra_parts else None
    return ParsedServer(
        name=name,
        address=address,
        port=port,
        check_enabled=check_enabled,
        maxconn=maxconn,
        maxqueue=maxqueue,
        extra_params=extra,
        weight=weight,
        ssl_enabled=ssl_enabled,
        ssl_verify=ssl_verify,
        backup=backup,
        inter=inter,
        fastinter=fastinter,
        downinter=downinter,
        rise=rise,
        fall=fall,
        cookie_value=cookie_value,
        send_proxy=send_proxy,
        send_proxy_v2=send_proxy_v2,
        slowstart=slowstart,
        resolve_prefer=resolve_prefer,
        resolvers_ref=resolvers_ref,
        on_marked_down=on_marked_down,
        disabled=disabled,
    )


def parse_config(config_text: str) -> ParsedConfig:
    """Parse HAProxy configuration text into structured data."""

    result = ParsedConfig()
    lines = config_text.splitlines()

    # Split into sections
    sections: list[tuple[str, str, list[str]]] = []
    current_type: str | None = None
    current_name: str = ""
    current_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_type is not None:
                current_lines.append("")
            continue

        m = _SECTION_RE.match(stripped)
        if m and not line[0].isspace():
            # Found a new section
            if current_type is not None:
                sections.append((current_type, current_name, current_lines))
            current_type = m.group(1).lower()
            current_name = m.group(2).strip()
            current_lines = []
        elif current_type is not None:
            current_lines.append(stripped)

    if current_type is not None:
        sections.append((current_type, current_name, current_lines))

    # Process each section
    for sec_type, sec_name, sec_lines in sections:
        if sec_type == "global":
            _parse_global(result, sec_lines)
        elif sec_type == "defaults":
            _parse_defaults(result, sec_lines)
        elif sec_type == "userlist":
            _parse_userlist(result, sec_name, sec_lines)
        elif sec_type == "frontend":
            _parse_frontend(result, sec_name, sec_lines)
        elif sec_type == "backend":
            _parse_backend(result, sec_name, sec_lines)
        elif sec_type == "listen":
            _parse_listen(result, sec_name, sec_lines)
        elif sec_type == "resolvers":
            _parse_resolvers(result, sec_name, sec_lines)
        elif sec_type == "peers":
            _parse_peers(result, sec_name, sec_lines)
        elif sec_type == "mailers":
            _parse_mailers(result, sec_name, sec_lines)
        elif sec_type == "http-errors":
            _parse_http_errors(result, sec_name, sec_lines)
        elif sec_type == "cache":
            _parse_cache(result, sec_name, sec_lines)

    # Extract SSL certificates from bind lines in frontends and listen blocks
    _extract_ssl_certificates(result)

    return result


def _extract_ssl_certificates(result: ParsedConfig) -> None:
    """Extract SSL certificate paths from bind lines across all frontends
    and listen blocks, creating ParsedSslCertificate entries."""

    seen_paths: set[str] = set()

    def _process_bind_line(bind_line: str, source_name: str) -> None:
        """Extract SSL certificate info from a bind directive."""

        m = _SSL_CRT_RE.search(bind_line)
        if not m:
            return
        # Pick the matched group: group(1) = double-quoted, group(2) = single-quoted, group(3) = unquoted
        crt_path = (m.group(1) or m.group(2) or m.group(3)).strip()
        if crt_path in seen_paths:
            return
        seen_paths.add(crt_path)

        # Derive a domain name from the cert path
        # e.g. /etc/letsencrypt/live/example.com/fullchain.pem -> example.com
        # e.g. /etc/nethostssl/default.pem -> default.pem (filename)
        # e.g. /etc/nethostssl -> nethostssl (directory-based cert bundle)
        import os

        parts = crt_path.split("/")
        domain = None

        # Check for letsencrypt-style path: /etc/letsencrypt/live/<domain>/...
        if "letsencrypt" in crt_path and "live" in parts:
            try:
                live_idx = parts.index("live")
                if live_idx + 1 < len(parts):
                    candidate = parts[live_idx + 1]
                    if "." in candidate:
                        domain = candidate
            except (ValueError, IndexError):
                pass

        if not domain:
            # Try to extract from filename or directory
            basename = os.path.basename(crt_path)
            if basename and "." in basename:
                name_part = os.path.splitext(basename)[0]
                # If it looks like a real domain name (has a dot and a TLD-like part)
                domain = name_part if "." in name_part and name_part not in ("fullchain", "cert", "privkey", "chain") else basename
            elif basename:
                # No extension - likely a directory path, use the last component
                domain = basename
            else:
                # Use the parent directory name
                parent = os.path.basename(os.path.dirname(crt_path))
                domain = parent if parent else crt_path

        # Determine cert/key/fullchain paths based on pattern
        cert_path = None
        fullchain_path = crt_path

        result.ssl_certificates.append(
            ParsedSslCertificate(
                domain=domain,
                cert_path=cert_path,
                fullchain_path=fullchain_path,
                comment=f"Imported from {source_name} bind line",
                provider="manual",
                status="active",
                auto_renew=False,
            )
        )

    # Scan frontend binds
    for fe in result.frontends:
        for bind_line in fe.binds:
            _process_bind_line(bind_line, f"frontend {fe.name}")

    # Scan listen block binds
    for lb in result.listen_blocks:
        for bind_line in lb.binds:
            _process_bind_line(bind_line, f"listen {lb.name}")


def _parse_settings_section(lines: list[str]) -> list[ParsedDirective]:
    """Parse a simple directive/value settings section (global or defaults)."""

    directives: list[ParsedDirective] = []
    order = 0
    comment_buf: list[str] = []
    for line in lines:
        if not line:
            continue
        cm = _COMMENT_BLOCK_RE.match(line)
        if line.startswith("#"):
            comment_buf.append(cm.group(1) if cm else line[1:])
            continue
        content, inline_comment = _strip_inline_comment(line)
        if not content:
            continue
        parts = content.split(None, 1)
        directive = parts[0]
        value = parts[1] if len(parts) > 1 else ""
        comment = "\n".join(comment_buf) if comment_buf else inline_comment
        comment_buf = []
        directives.append(ParsedDirective(directive=directive, value=value, comment=comment, order=order))
        order += 1
    return directives


def _parse_global(result: ParsedConfig, lines: list[str]) -> None:
    """Parse the `global` settings section."""

    result.global_settings.extend(_parse_settings_section(lines))


def _parse_defaults(result: ParsedConfig, lines: list[str]) -> None:
    """Parse the `defaults` settings section."""

    result.default_settings.extend(_parse_settings_section(lines))


def _parse_userlist(result: ParsedConfig, name: str, lines: list[str]) -> None:
    """Parse a `userlist` section into structured data."""

    ul = ParsedUserlist(name=name)
    order = 0
    for line in lines:
        if not line or line.startswith("#"):
            continue
        content, _ = _strip_inline_comment(line)
        if not content:
            continue
        parts = content.split()
        if parts[0].lower() == "user" and len(parts) >= 4 and parts[2].lower() == "password":
            ul.entries.append(
                ParsedUserlistEntry(
                    username=parts[1],
                    password_hash=parts[3],
                    order=order,
                )
            )
            order += 1
    result.userlists.append(ul)


def _parse_frontend(result: ParsedConfig, name: str, lines: list[str]) -> None:
    """Parse a `frontend` section with binds, options, and ACL rules."""

    fe = ParsedFrontend(name=name)
    acl_order = 0

    # Collect ACL definitions and their corresponding use_backend / redirect lines
    acl_domains: dict[str, tuple[str, str]] = {}  # acl_name -> (match_type, domain)
    comment_buf: list[str] = []
    pending_acls: dict[str, str | None] = {}  # acl_name -> comment
    option_order = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1

        if not line:
            continue

        if line.startswith("#"):
            cm = _COMMENT_BLOCK_RE.match(line)
            comment_buf.append(cm.group(1) if cm else line[1:])
            continue

        content, _ = _strip_inline_comment(line)
        if not content:
            continue

        # Bind directives
        if _BIND_RE.match(content):
            bind_val = content[5:].strip()
            fe.binds.append(bind_val)
            comment_buf = []
            continue

        # Mode
        if content.lower().startswith("mode "):
            fe.mode = content.split(None, 1)[1].strip()
            comment_buf = []
            continue

        # Default backend
        if content.lower().startswith("default_backend "):
            fe.default_backend = content.split(None, 1)[1].strip()
            comment_buf = []
            continue

        # Typed frontend fields
        lower_content = content.lower()
        if lower_content.startswith("timeout client "):
            fe.timeout_client = content.split()[-1]
            comment_buf = []
            continue
        if lower_content.startswith("timeout http-request "):
            fe.timeout_http_request = content.split()[-1]
            comment_buf = []
            continue
        if lower_content.startswith("timeout http-keep-alive "):
            fe.timeout_http_keep_alive = content.split()[-1]
            comment_buf = []
            continue
        if lower_content.startswith("maxconn "):
            with contextlib.suppress(ValueError, IndexError):
                fe.maxconn = int(content.split(None, 1)[1])
            comment_buf = []
            continue
        if lower_content == "option httplog":
            fe.option_httplog = True
            comment_buf = []
            continue
        if lower_content == "option tcplog":
            fe.option_tcplog = True
            comment_buf = []
            continue
        if lower_content == "option forwardfor":
            fe.option_forwardfor = True
            comment_buf = []
            continue
        if lower_content.startswith("compression algo "):
            fe.compression_algo = content.split(None, 2)[2].strip()
            comment_buf = []
            continue
        if lower_content.startswith("compression type "):
            fe.compression_type = content.split(None, 2)[2].strip()
            comment_buf = []
            continue

        # ACL definition
        acl_m = _ACL_HDR_RE.match(content)
        if acl_m:
            acl_name = content.split()[1]
            match_type = acl_m.group(1)
            domain = acl_m.group(2)
            acl_domains[acl_name] = (match_type, domain)
            comment_text = "\n".join(comment_buf) if comment_buf else None
            pending_acls[acl_name] = comment_text
            comment_buf = []
            continue

        # use_backend
        ub_m = _USE_BACKEND_RE.match(content)
        if ub_m:
            backend_name = ub_m.group(1)
            # Find the ACL name referenced
            acl_name_match = re.search(r"if\s+(\S+)", content)
            if acl_name_match:
                ref = acl_name_match.group(1)
                if ref in acl_domains:
                    match_type, domain = acl_domains[ref]
                    comment_text = pending_acls.get(ref)
                    fe.acls.append(
                        ParsedAcl(
                            domain=domain,
                            backend_name=backend_name,
                            acl_match_type=match_type,
                            comment=comment_text,
                            order=acl_order,
                        )
                    )
                    acl_order += 1
            comment_buf = []
            continue

        # Redirect
        if content.lower().startswith("redirect "):
            redir_m = _REDIRECT_RE.match(content)
            if redir_m:
                target = redir_m.group(1)
                code = int(redir_m.group(2))
                acl_name_match = re.search(r"if\s+(\S+)", content)
                if acl_name_match:
                    ref = acl_name_match.group(1)
                    if ref in acl_domains:
                        _, domain = acl_domains[ref]
                        comment_text = pending_acls.get(ref)
                        fe.acls.append(
                            ParsedAcl(
                                domain=domain,
                                is_redirect=True,
                                redirect_target=target,
                                redirect_code=code,
                                comment=comment_text,
                                order=acl_order,
                            )
                        )
                        acl_order += 1
                comment_buf = []
                continue

            # Non-ACL redirects are options
            opt_parts = content.split(None, 1)
            opt_comment = "\n".join(comment_buf) if comment_buf else None
            fe.options.append(
                ParsedDirective(
                    directive=opt_parts[0],
                    value=opt_parts[1] if len(opt_parts) > 1 else "",
                    comment=opt_comment,
                    order=option_order,
                )
            )
            option_order += 1
            comment_buf = []
            continue

        # Everything else is an option
        opt_comment = "\n".join(comment_buf) if comment_buf else None
        comment_buf = []
        opt_parts = content.split(None, 1)
        fe.options.append(
            ParsedDirective(
                directive=opt_parts[0],
                value=opt_parts[1] if len(opt_parts) > 1 else "",
                comment=opt_comment,
                order=option_order,
            )
        )
        option_order += 1

    result.frontends.append(fe)


def _parse_backend(result: ParsedConfig, name: str, lines: list[str]) -> None:
    """Parse a `backend` section with server entries."""

    be = ParsedBackend(name=name)
    server_order = 0
    extra_lines: list[str] = []
    comment_buf: list[str] = []

    for line in lines:
        if not line:
            continue
        if line.startswith("#"):
            cm = _COMMENT_BLOCK_RE.match(line)
            comment_text = cm.group(1) if cm else line[1:]
            if not be.comment:
                comment_buf.append(comment_text)
            continue

        content, _ = _strip_inline_comment(line)
        if not content:
            continue

        lower = content.lower()

        if comment_buf and not be.comment:
            be.comment = "\n".join(comment_buf)
            comment_buf = []

        # Server line
        srv = _parse_server_line(content)
        if srv:
            srv.order = server_order
            server_order += 1
            be.servers.append(srv)
            continue

        # Known directives
        if lower.startswith("mode "):
            be.mode = content.split(None, 1)[1].strip()
        elif lower.startswith("balance "):
            be.balance = content.split(None, 1)[1].strip()
        elif lower == "option forwardfor":
            be.option_forwardfor = True
        elif lower.startswith("option redispatch"):
            be.option_redispatch = True
        elif lower == "option httplog":
            be.option_httplog = True
        elif lower == "option tcplog":
            be.option_tcplog = True
        elif lower.startswith("retries "):
            try:
                be.retries = int(content.split(None, 1)[1])
            except (ValueError, IndexError):
                extra_lines.append(content)
        elif lower.startswith("retry-on "):
            be.retry_on = content.split(None, 1)[1].strip()
        elif lower.startswith("option httpchk"):
            be.health_check_enabled = True
        elif lower.startswith("http-check send"):
            parts = content.split()
            for j, tok in enumerate(parts):
                if tok.lower() == "meth" and j + 1 < len(parts):
                    be.health_check_method = parts[j + 1]
                if tok.lower() == "uri" and j + 1 < len(parts):
                    be.health_check_uri = parts[j + 1]
        elif lower.startswith("http-check expect"):
            be.http_check_expect = content.split(None, 2)[2].strip() if len(content.split(None, 2)) > 2 else content
        elif lower.startswith("errorfile "):
            be.errorfile = content.split(None, 1)[1].strip()
        elif lower.startswith("cookie "):
            be.cookie = content.split(None, 1)[1].strip()
        elif lower.startswith("timeout server "):
            be.timeout_server = content.split()[-1]
        elif lower.startswith("timeout connect "):
            be.timeout_connect = content.split()[-1]
        elif lower.startswith("timeout queue "):
            be.timeout_queue = content.split()[-1]
        elif lower.startswith("default-server "):
            be.default_server_options = content.split(None, 1)[1].strip()
        elif lower.startswith("http-reuse "):
            be.http_reuse = content.split(None, 1)[1].strip()
        elif lower.startswith("hash-type "):
            be.hash_type = content.split(None, 1)[1].strip()
        elif lower.startswith("compression algo "):
            be.compression_algo = content.split(None, 2)[2].strip()
        elif lower.startswith("compression type "):
            be.compression_type = content.split(None, 2)[2].strip()
        elif lower.startswith("acl authorized http_auth"):
            m = re.match(r"acl\s+authorized\s+http_auth\((\S+)\)", content, re.IGNORECASE)
            if m:
                be.auth_userlist = m.group(1)
        elif lower.startswith("http-request auth"):
            pass  # Already handled by auth_userlist
        elif lower.startswith("http-check connect"):
            pass  # Handled by health_check_enabled
        else:
            extra_lines.append(content)

    if extra_lines:
        be.extra_options = "\n".join(extra_lines)

    result.backends.append(be)


def _parse_listen(result: ParsedConfig, name: str, lines: list[str]) -> None:
    """Parse a `listen` section with bind entries."""

    binds: list[str] = []
    mode = "http"
    balance: str | None = None
    maxconn: int | None = None
    timeout_client: str | None = None
    timeout_server: str | None = None
    timeout_connect: str | None = None
    default_server_params: str | None = None
    option_httplog = False
    option_tcplog = False
    option_forwardfor = False
    content_lines: list[str] = []
    comment_buf: list[str] = []

    for line in lines:
        if not line:
            continue
        if line.startswith("#"):
            comment_buf.append(line[1:].strip())
            continue

        content, _ = _strip_inline_comment(line)
        if not content:
            continue

        lower = content.lower()
        if lower.startswith("bind "):
            binds.append(content[5:].strip())
        elif lower.startswith("mode "):
            mode = content.split(None, 1)[1].strip()
        elif lower.startswith("balance "):
            balance = content.split(None, 1)[1].strip()
        elif lower.startswith("maxconn "):
            try:
                maxconn = int(content.split(None, 1)[1].strip())
            except (ValueError, IndexError):
                content_lines.append(content)
        elif lower.startswith("timeout client "):
            timeout_client = content.split(None, 2)[2].strip()
        elif lower.startswith("timeout server "):
            timeout_server = content.split(None, 2)[2].strip()
        elif lower.startswith("timeout connect "):
            timeout_connect = content.split(None, 2)[2].strip()
        elif lower.startswith("default-server "):
            default_server_params = content.split(None, 1)[1].strip()
        elif lower.strip() == "option httplog":
            option_httplog = True
        elif lower.strip() == "option tcplog":
            option_tcplog = True
        elif lower.strip() == "option forwardfor":
            option_forwardfor = True
        else:
            content_lines.append(content)

    comment = "\n".join(comment_buf) if comment_buf else None
    result.listen_blocks.append(
        ParsedListenBlock(
            name=name,
            binds=binds,
            mode=mode,
            balance=balance,
            maxconn=maxconn,
            timeout_client=timeout_client,
            timeout_server=timeout_server,
            timeout_connect=timeout_connect,
            default_server_params=default_server_params,
            option_httplog=option_httplog,
            option_tcplog=option_tcplog,
            option_forwardfor=option_forwardfor,
            content="\n".join(content_lines) if content_lines else None,
            comment=comment,
        )
    )


_NS_RE = re.compile(r"^nameserver\s+(\S+)\s+(\S+):(\d+)", re.IGNORECASE)
_PEER_RE = re.compile(r"^peer\s+(\S+)\s+(\S+):(\d+)", re.IGNORECASE)
_MAILER_RE = re.compile(r"^mailer\s+(\S+)\s+(\S+):(\d+)", re.IGNORECASE)
_ERRORFILE_RE = re.compile(r"^(errorfile|errorloc302|errorloc303|errorloc)\s+(\d+)\s+(\S+)", re.IGNORECASE)


def _parse_resolvers(result: ParsedConfig, name: str, lines: list[str]) -> None:
    """Parse a `resolvers` section with nameserver entries."""

    r = ParsedResolver(name=name)
    ns_order = 0
    extra_lines: list[str] = []

    for line in lines:
        if not line or line.startswith("#"):
            continue
        content, _ = _strip_inline_comment(line)
        if not content:
            continue
        lower = content.lower()

        m = _NS_RE.match(content)
        if m:
            r.nameservers.append(ParsedResolverNameserver(name=m.group(1), address=m.group(2), port=int(m.group(3)), order=ns_order))
            ns_order += 1
            continue

        if lower.startswith("resolve_retries "):
            try:
                r.resolve_retries = int(content.split(None, 1)[1])
            except (ValueError, IndexError):
                extra_lines.append(content)
        elif lower.startswith("timeout resolve "):
            r.timeout_resolve = content.split()[-1]
        elif lower.startswith("timeout retry "):
            r.timeout_retry = content.split()[-1]
        elif lower.startswith("hold valid "):
            r.hold_valid = content.split()[-1]
        elif lower.startswith("hold other "):
            r.hold_other = content.split()[-1]
        elif lower.startswith("hold refused "):
            r.hold_refused = content.split()[-1]
        elif lower.startswith("hold timeout "):
            r.hold_timeout = content.split()[-1]
        elif lower.startswith("hold obsolete "):
            r.hold_obsolete = content.split()[-1]
        elif lower.startswith("hold nx "):
            r.hold_nx = content.split()[-1]
        elif lower.startswith("hold aa "):
            r.hold_aa = content.split()[-1]
        elif lower.startswith("accepted_payload_size "):
            try:
                r.accepted_payload_size = int(content.split(None, 1)[1])
            except (ValueError, IndexError):
                extra_lines.append(content)
        elif lower.strip() == "parse-resolv-conf":
            r.parse_resolv_conf = 1
        else:
            extra_lines.append(content)

    if extra_lines:
        r.extra_options = "\n".join(extra_lines)
    result.resolvers.append(r)


def _parse_peers(result: ParsedConfig, name: str, lines: list[str]) -> None:
    """Parse a `peers` section with peer entries."""

    ps = ParsedPeerSection(name=name)
    entry_order = 0
    extra_lines: list[str] = []

    for line in lines:
        if not line or line.startswith("#"):
            continue
        content, _ = _strip_inline_comment(line)
        if not content:
            continue
        lower = content.lower()

        m = _PEER_RE.match(content)
        if m:
            ps.entries.append(ParsedPeerEntry(name=m.group(1), address=m.group(2), port=int(m.group(3)), order=entry_order))
            entry_order += 1
            continue

        if lower.startswith("bind "):
            ps.default_bind = content.split(None, 1)[1] if len(content.split(None, 1)) > 1 else ""
            continue
        if lower.startswith("default-server "):
            ps.default_server_options = content.split(None, 1)[1] if len(content.split(None, 1)) > 1 else ""
            continue

        extra_lines.append(content)

    if extra_lines:
        ps.extra_options = "\n".join(extra_lines)
    result.peers.append(ps)


_PM_MAILER_AUTH_RE = re.compile(
    r"^#\s*_pm_mailer_auth\s+(?P<mailer>\S+)"
    r"\s+smtp_auth=(?P<smtp_auth>\S+)"
    r"\s+smtp_user=(?P<smtp_user>\S*)"
    r"\s+smtp_password=(?P<smtp_password>\S*)"
    r"\s+use_tls=(?P<use_tls>\S+)"
    r"\s+use_starttls=(?P<use_starttls>\S+)",
    re.IGNORECASE,
)


def _parse_mailers(result: ParsedConfig, name: str, lines: list[str]) -> None:
    """Parse a `mailers` section with mailer entries."""

    ms = ParsedMailerSection(name=name)
    entry_order = 0
    extra_lines: list[str] = []
    # Collect auth metadata keyed by mailer entry name.
    auth_meta: dict[str, dict[str, str]] = {}

    for line in lines:
        if not line:
            continue
        # Check for special proxy-manager auth metadata comments first.
        stripped = line.strip()
        am = _PM_MAILER_AUTH_RE.match(stripped)
        if am:
            auth_meta[am.group("mailer")] = am.groupdict()
            continue
        if stripped.startswith("#"):
            continue
        content, _ = _strip_inline_comment(line)
        if not content:
            continue
        lower = content.lower()

        if lower.startswith("timeout mail "):
            ms.timeout_mail = content.split()[-1]
            continue

        m = _MAILER_RE.match(content)
        if m:
            ms.entries.append(
                ParsedMailerEntry(
                    name=m.group(1),
                    address=m.group(2),
                    port=int(m.group(3)),
                    order=entry_order,
                )
            )
            entry_order += 1
            continue

        extra_lines.append(content)

    # Apply collected auth metadata to matching entries.
    for entry in ms.entries:
        meta = auth_meta.get(entry.name)
        if meta:
            entry.smtp_auth = meta.get("smtp_auth", "").lower() in ("true", "1", "yes")
            entry.smtp_user = meta.get("smtp_user") or None
            entry.smtp_password = meta.get("smtp_password") or None
            entry.use_tls = meta.get("use_tls", "").lower() in ("true", "1", "yes")
            entry.use_starttls = meta.get("use_starttls", "").lower() in ("true", "1", "yes")

    if extra_lines:
        ms.extra_options = "\n".join(extra_lines)
    result.mailers.append(ms)


def _parse_http_errors(result: ParsedConfig, name: str, lines: list[str]) -> None:
    """Parse an `http-errors` section with error file entries."""

    sec = ParsedHttpErrorsSection(name=name)
    entry_order = 0
    extra_lines: list[str] = []

    for line in lines:
        if not line or line.startswith("#"):
            continue
        content, _ = _strip_inline_comment(line)
        if not content:
            continue

        m = _ERRORFILE_RE.match(content)
        if m:
            sec.entries.append(
                ParsedHttpErrorEntry(
                    status_code=int(m.group(2)),
                    type=m.group(1).lower(),
                    value=m.group(3),
                    order=entry_order,
                )
            )
            entry_order += 1
            continue

        extra_lines.append(content)

    if extra_lines:
        sec.extra_options = "\n".join(extra_lines)
    result.http_errors.append(sec)


def _parse_cache(result: ParsedConfig, name: str, lines: list[str]) -> None:
    """Parse a `cache` section."""

    c = ParsedCacheSection(name=name)
    extra_lines: list[str] = []

    for line in lines:
        if not line or line.startswith("#"):
            continue
        content, _ = _strip_inline_comment(line)
        if not content:
            continue
        lower = content.lower()

        if lower.startswith("total-max-size "):
            try:
                c.total_max_size = int(content.split(None, 1)[1])
            except (ValueError, IndexError):
                extra_lines.append(content)
        elif lower.startswith("max-object-size "):
            try:
                c.max_object_size = int(content.split(None, 1)[1])
            except (ValueError, IndexError):
                extra_lines.append(content)
        elif lower.startswith("max-age "):
            try:
                c.max_age = int(content.split(None, 1)[1])
            except (ValueError, IndexError):
                extra_lines.append(content)
        elif lower.startswith("max-secondary-entries "):
            try:
                c.max_secondary_entries = int(content.split(None, 1)[1])
            except (ValueError, IndexError):
                extra_lines.append(content)
        elif lower.startswith("process-vary "):
            try:
                c.process_vary = int(content.split(None, 1)[1])
            except (ValueError, IndexError):
                extra_lines.append(content)
        else:
            extra_lines.append(content)

    if extra_lines:
        c.extra_options = "\n".join(extra_lines)
    result.caches.append(c)
