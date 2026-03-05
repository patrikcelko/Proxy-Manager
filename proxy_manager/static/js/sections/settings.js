/*
Settings Section
================

Manages HAProxy global and defaults directives with categorized
tabs, preset template libraries, inline search, drag-reorder,
and add/edit/delete modals with quick-add template grids.
*/

/* Category definitions for grouping global directives */
const GLOBAL_CATS = {
    all: { label: 'All' },
    general: { label: 'General' },
    logging: { label: 'Logging' },
    stats: { label: 'Statistics' },
    usergroup: { label: 'User & Group' },
    ssl: { label: 'SSL Tuning' },
    performance: { label: 'Performance' },
};

/* Category definitions for grouping defaults directives */
const DEFAULTS_CATS = {
    all: { label: 'All' },
    general: { label: 'General' },
    timeouts: { label: 'Timeouts' },
    http: { label: 'HTTP Options' },
    tcp: { label: 'TCP Options' },
    errors: { label: 'Error Pages' },
    health: { label: 'Health & Servers' },
    compression: { label: 'Compression' },
};

/* Classifies a global directive into its category using regex patterns */
function categorizeGlobal(directive) {
    const d = (directive || '').toLowerCase().trim();
    if (/^(ssl-|ca-base|crt-base|issuers-chain|tune\.ssl)/.test(d)) return 'ssl';
    if (/^log/.test(d)) return 'logging';
    if (/^stats/.test(d)) return 'stats';
    if (/^(user|group|uid|gid)\b/.test(d)) return 'usergroup';
    if (/^(maxconn|maxsess|maxssl|maxpipes|maxconnrate|maxsslrate|nbthread|nbproc|cpu-map|spread-checks|tune\.)/.test(d)) return 'performance';
    return 'general';
}

/* Classifies a defaults directive into its category using regex patterns */
function categorizeDefaults(directive) {
    const d = (directive || '').toLowerCase().trim();
    if (/^timeout/.test(d)) return 'timeouts';
    if (/^(errorfile|errorloc)/.test(d)) return 'errors';
    if (/^compression/.test(d)) return 'compression';
    if (/^default-server/.test(d)) return 'health';
    if (/^(rate-limit|monitor-uri)/.test(d)) return 'http';
    if (/^(http-reuse|load-server-state)/.test(d)) return 'general';
    if (/^option\s+(tcp|clitcpka|srvtcpka|dontlog-normal|log-health|splice|tcp-smart)/.test(d)) return 'tcp';
    if (/^option/.test(d)) return 'http';
    return 'general';
}

/* Comprehensive preset directives for global settings organized by category */
const GLOBAL_PRESETS = {
    general: [
        { d: 'daemon', v: '', h: 'Fork process into background (production mode)' },
        { d: 'master-worker', v: '', h: 'Run in master-worker mode with seamless reloads (HAProxy 1.9+)' },
        { d: 'chroot', v: '/var/lib/haproxy', h: 'Changes root directory for security isolation' },
        { d: 'node', v: 'haproxy-01', h: 'Set the node name (shown in stats)' },
        { d: 'description', v: 'Main HAProxy load balancer', h: 'Description shown in stats page' },
        { d: 'pidfile', v: '/run/haproxy.pid', h: 'Write PID to this file' },
        { d: 'hard-stop-after', v: '30s', h: 'Maximum time for graceful stop before force kill' },
        { d: 'grace', v: '10000', h: 'Grace period after SIGUSR1 in milliseconds' },
        { d: 'localpeer', v: 'haproxy-01', h: 'Set local peer name for stick-table replication' },
        { d: 'cluster-secret', v: '', h: 'Shared secret for cluster communication' },
        { d: 'expose-experimental-directives', v: '', h: 'Allow experimental directives (e.g. QUIC/HTTP3)' },
        { d: 'external-check', v: '', h: 'Allow external check scripts to run' },
        { d: 'insecure-fork-wanted', v: '', h: 'Disable security warning about forking' },
        { d: 'quiet', v: '', h: 'Suppress output messages on startup' },
        { d: 'zero-warning', v: '', h: 'Treat warnings as errors (strict mode)' },
        { d: 'close-spread-time', v: '1000', h: 'Time window to spread connection closing (ms)' },
        { d: 'nosplice', v: '', h: 'Disable kernel TCP splicing' },
        { d: 'noepoll', v: '', h: 'Disable epoll for debugging' },
        { d: 'pp2-never-send-local', v: '', h: 'Never send PROXY protocol v2 for local connections' },
        { d: 'numa-cpu-mapping', v: '', h: 'Enable NUMA-aware CPU thread mapping' },
        { d: 'set-dumpable', v: '', h: 'Allow core dumps even after chroot/setuid' },
        { d: 'server-state-base', v: '/var/lib/haproxy/state', h: 'Directory for server state persistence files' },
        { d: 'server-state-file', v: 'global', h: 'Global server state file for session persistence across reloads' },
        { d: 'mworker-max-reloads', v: '3', h: 'Max queued reloads in master-worker mode before killing old workers' },
        { d: 'strict-limits', v: '', h: 'Enforce strict memory limits (refuse to start if insufficient)' },
    ],
    logging: [
        { d: 'log', v: '/dev/log local0', h: 'Send logs to local syslog facility 0' },
        { d: 'log', v: '/dev/log local1 notice', h: 'Send notice+ logs to syslog facility 1' },
        { d: 'log', v: '127.0.0.1:514 local0', h: 'Send logs to remote syslog server' },
        { d: 'log', v: '127.0.0.1:514 local0 info', h: 'Info+ level to remote syslog' },
        { d: 'log', v: 'stderr format short daemon', h: 'Log to stderr (container/Docker environments)' },
        { d: 'log-send-hostname', v: '', h: 'Include hostname in syslog messages' },
        { d: 'log-send-hostname', v: 'haproxy-node-1', h: 'Use custom hostname in syslog' },
        { d: 'log-tag', v: 'haproxy', h: 'Tag prepended to syslog messages' },
    ],
    stats: [
        { d: 'stats socket', v: '/run/haproxy/admin.sock mode 660 level admin', h: 'Unix socket for Runtime API access' },
        { d: 'stats socket', v: '/run/haproxy/admin.sock mode 660 level admin expose-fd listeners', h: 'Runtime API with fd passing for seamless reload' },
        { d: 'stats socket', v: 'ipv4@127.0.0.1:9999 level admin', h: 'TCP socket for remote Runtime API' },
        { d: 'stats timeout', v: '30s', h: 'Timeout for stats socket idle connections' },
        { d: 'stats maxconn', v: '10', h: 'Max concurrent stats socket connections' },
        { d: 'stats bind-process', v: 'all', h: 'Which processes handle stats socket' },
    ],
    usergroup: [
        { d: 'user', v: 'haproxy', h: 'Drop privileges to this user after startup' },
        { d: 'group', v: 'haproxy', h: 'Drop privileges to this group after startup' },
        { d: 'uid', v: '99', h: 'Drop privileges to this numeric UID' },
        { d: 'gid', v: '99', h: 'Drop privileges to this numeric GID' },
    ],
    ssl: [
        { d: 'ca-base', v: '/etc/ssl/certs', h: 'Default directory for CA certificate files' },
        { d: 'crt-base', v: '/etc/ssl/private', h: 'Default directory for certificate (PEM) files' },
        { d: 'ssl-default-bind-ciphers', v: 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384', h: 'Cipher list for incoming SSL/TLS connections' },
        { d: 'ssl-default-bind-ciphersuites', v: 'TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256', h: 'TLSv1.3 cipher suites for bind lines' },
        { d: 'ssl-default-bind-curves', v: 'X25519:P-256:P-384', h: 'Named EC curves for ECDHE key exchange on bind' },
        { d: 'ssl-default-bind-options', v: 'prefer-client-ciphers no-sslv3 no-tlsv10 no-tlsv11 no-tls-tickets', h: 'SSL security options for bind (disable old protocols)' },
        { d: 'ssl-default-server-ciphers', v: 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256', h: 'Cipher list for outgoing server connections' },
        { d: 'ssl-default-server-ciphersuites', v: 'TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256', h: 'TLSv1.3 cipher suites for server connections' },
        { d: 'ssl-default-server-curves', v: 'X25519:P-256:P-384', h: 'Named EC curves for ECDHE on server connections' },
        { d: 'ssl-default-server-options', v: 'no-sslv3 no-tlsv10 no-tlsv11 no-tls-tickets', h: 'SSL security options for server connections' },
        { d: 'ssl-dh-param-file', v: '/etc/haproxy/dhparams.pem', h: 'Custom DH parameters file for DHE key exchange' },
        { d: 'ssl-server-verify', v: 'required', h: 'Verify server certificates (none/required)' },
        { d: 'ssl-mode-async', v: '', h: 'Enable asynchronous SSL for OpenSSL engine offloading' },
        { d: 'ssl-skip-self-issued-ca', v: '', h: 'Skip self-issued CA certificates in chain sent to clients' },
        { d: 'ssl-load-extra-files', v: 'all', h: 'Automatically load .ocsp, .sctl, .issuer alongside certs' },
        { d: 'issuers-chain-path', v: '/etc/haproxy/issuer', h: 'Path to OCSP issuer certificate chain' },
        { d: 'tune.ssl.default-dh-param', v: '2048', h: 'Default DH parameter size in bits' },
        { d: 'tune.ssl.cachesize', v: '20000', h: 'Number of SSL sessions in cache' },
        { d: 'tune.ssl.lifetime', v: '300', h: 'SSL session cache lifetime (seconds)' },
        { d: 'tune.ssl.maxrecord', v: '1419', h: 'Maximum SSL record size (fits PMTU)' },
        { d: 'tune.ssl.capture-buffer-size', v: '96', h: 'Capture buffer for SSL/TLS key logging' },
        { d: 'tune.ssl.force-private-cache', v: '', h: 'Force per-thread SSL session cache (no sharing)' },
        { d: 'tune.ssl.keylog', v: '', h: 'Enable SSL keylog for TLS traffic analysis (debug)' },
    ],
    performance: [
        { d: 'maxconn', v: '50000', h: 'Maximum per-process concurrent connections' },
        { d: 'maxconnrate', v: '500', h: 'Maximum new connections per second' },
        { d: 'maxsessrate', v: '500', h: 'Maximum new sessions per second' },
        { d: 'maxsslconn', v: '10000', h: 'Maximum concurrent SSL connections' },
        { d: 'maxsslrate', v: '500', h: 'Maximum new SSL connections per second' },
        { d: 'maxpipes', v: '1000', h: 'Maximum pipes for kernel splicing' },
        { d: 'nbthread', v: '4', h: 'Number of threads per process (recommended)' },
        { d: 'nbproc', v: '1', h: 'Number of HAProxy processes (deprecated, use nbthread)' },
        { d: 'cpu-map', v: 'auto:1/1-4 0-3', h: 'Pin threads to CPU cores' },
        { d: 'spread-checks', v: '5', h: 'Randomize health check intervals by 0\u201350%' },
        { d: 'tune.bufsize', v: '16384', h: 'Request/response buffer size (bytes)' },
        { d: 'tune.maxrewrite', v: '1024', h: 'Reserved space for header rewriting' },
        { d: 'tune.comp.maxlevel', v: '1', h: 'Maximum compression level (1=fast, 9=best)' },
        { d: 'tune.http.maxhdr', v: '101', h: 'Maximum number of HTTP headers allowed' },
        { d: 'tune.http.logurilen', v: '1024', h: 'Maximum URI length captured in logs' },
        { d: 'tune.h2.header-table-size', v: '4096', h: 'HTTP/2 HPACK header table size (bytes)' },
        { d: 'tune.h2.initial-window-size', v: '65535', h: 'HTTP/2 initial flow-control window (bytes)' },
        { d: 'tune.h2.max-concurrent-streams', v: '100', h: 'HTTP/2 max concurrent streams per connection' },
        { d: 'tune.h2.max-frame-size', v: '16384', h: 'HTTP/2 max frame size (bytes, 16384\u201316777215)' },
        { d: 'tune.rcvbuf.client', v: '0', h: 'Client-side receive buffer (0 = OS default)' },
        { d: 'tune.sndbuf.client', v: '0', h: 'Client-side send buffer (0 = OS default)' },
        { d: 'tune.rcvbuf.server', v: '0', h: 'Server-side receive buffer (0 = OS default)' },
        { d: 'tune.sndbuf.server', v: '0', h: 'Server-side send buffer (0 = OS default)' },
        { d: 'tune.zlib.memlevel', v: '8', h: 'Zlib compression memory level (1\u20139)' },
        { d: 'tune.vars.global-max-size', v: '0', h: 'Maximum size of global variables (0 = unlimited)' },
        { d: 'tune.idle-pool.shared', v: 'on', h: 'Share idle connections across threads' },
        { d: 'tune.maxaccept', v: '64', h: 'Max connections accepted per event loop' },
        { d: 'tune.runqueue-depth', v: '200', h: 'Max tasks processed per scheduler run' },
        { d: 'tune.memory.hot-size', v: '0', h: 'Hot memory cache per thread (0 = auto)' },
    ],
};

/* Comprehensive preset directives for defaults settings organized by category */
const DEFAULTS_PRESETS = {
    general: [
        { d: 'mode', v: 'http', h: 'Default proxy mode: http or tcp' },
        { d: 'log', v: 'global', h: 'Inherit log settings from global section' },
        { d: 'maxconn', v: '3000', h: 'Default maximum connections per frontend' },
        { d: 'fullconn', v: '1000', h: 'Connection count for dynamic cookie calculations' },
        { d: 'backlog', v: '10000', h: 'TCP backlog queue length' },
        { d: 'balance', v: 'roundrobin', h: 'Default load balancing algorithm' },
        { d: 'retries', v: '3', h: 'Number of retries on connection failure' },
        { d: 'retry-on', v: 'all-retryable-errors', h: 'Conditions that trigger connection retries (HAProxy 2.0+)' },
        { d: 'cookie', v: 'SERVERID insert indirect nocache', h: 'Session persistence cookie configuration' },
        { d: 'http-reuse', v: 'safe', h: 'Connection reuse strategy: never / safe / aggressive / always' },
        { d: 'load-server-state-from-file', v: 'global', h: 'Load server states from file on reload (requires server-state-file in global)' },
        { d: 'unique-id-format', v: '%{+X}o\\ %ci:%cp_%fi:%fp_%Ts_%rt:%pid', h: 'Unique request ID format for tracing' },
        { d: 'unique-id-header', v: 'X-Request-ID', h: 'Header to inject the unique request ID into' },
    ],
    timeouts: [
        { d: 'timeout connect', v: '5s', h: 'Max time to wait for server connection' },
        { d: 'timeout client', v: '30s', h: 'Max inactivity time on client side' },
        { d: 'timeout server', v: '30s', h: 'Max inactivity time on server side' },
        { d: 'timeout http-request', v: '10s', h: 'Max time to wait for complete HTTP request headers' },
        { d: 'timeout http-keep-alive', v: '10s', h: 'Max idle time for HTTP keep-alive connections' },
        { d: 'timeout queue', v: '30s', h: 'Max time waiting in queue for a free server slot' },
        { d: 'timeout tunnel', v: '3600s', h: 'Max inactivity for bidirectional tunnels (WebSockets)' },
        { d: 'timeout check', v: '10s', h: 'Extra read timeout for health check responses' },
        { d: 'timeout tarpit', v: '60s', h: 'Duration to hold tarpitted connections' },
        { d: 'timeout client-fin', v: '30s', h: 'Inactivity timeout after client FIN (half-close)' },
        { d: 'timeout server-fin', v: '30s', h: 'Inactivity timeout after server FIN (half-close)' },
    ],
    http: [
        { d: 'option httplog', v: '', h: 'Enable detailed HTTP request logging (method, URI, status)' },
        { d: 'option dontlognull', v: '', h: 'Skip logging of connections with no data (health checks)' },
        { d: 'option http-server-close', v: '', h: 'Close server connection after response for reuse' },
        { d: 'option forwardfor', v: 'except 127.0.0.0/8', h: 'Insert X-Forwarded-For header with client IP' },
        { d: 'option redispatch', v: '', h: 'Redistribute sessions on server failure' },
        { d: 'option http-keep-alive', v: '', h: 'Enable HTTP keep-alive on both sides' },
        { d: 'option httpclose', v: '', h: 'Force connection close after each request' },
        { d: 'option http-pretend-keepalive', v: '', h: 'Send keepalive to server even when client closes' },
        { d: 'option prefer-last-server', v: '', h: 'Prefer last used server for same client' },
        { d: 'option disable-h2-upgrade', v: '', h: 'Disable HTTP/2 upgrade negotiation' },
        { d: 'option http-buffer-request', v: '', h: 'Buffer the entire request before forwarding' },
        { d: 'option logasap', v: '', h: 'Log as soon as request is received (before response)' },
        { d: 'option http-use-htx', v: '', h: 'Force use of HTX message representation' },
        { d: 'option http-restrict-req-hdr-names', v: 'reject', h: 'Reject requests with invalid header names' },
        { d: 'option abortonclose', v: '', h: 'Abort queued requests when client closes early' },
        { d: 'monitor-uri', v: '/haproxy-health', h: 'Quick health-check URI (returns 200 without forwarding)' },
    ],
    tcp: [
        { d: 'option tcplog', v: '', h: 'Enable basic TCP connection logging' },
        { d: 'option tcp-smart-accept', v: '', h: 'Delay accept until data arrives (save resources)' },
        { d: 'option tcp-smart-connect', v: '', h: 'Delay connect until request data available' },
        { d: 'option clitcpka', v: '', h: 'Enable TCP keepalive on client side' },
        { d: 'option srvtcpka', v: '', h: 'Enable TCP keepalive on server side' },
        { d: 'option dontlog-normal', v: '', h: 'Only log errors, skip normal successful connections' },
        { d: 'option log-health-checks', v: '', h: 'Log health check transitions (UP/DOWN)' },
        { d: 'option splice-auto', v: '', h: 'Auto-detect kernel splicing support' },
        { d: 'option splice-request', v: '', h: 'Enable kernel splicing for requests' },
        { d: 'option splice-response', v: '', h: 'Enable kernel splicing for responses' },
        { d: 'option transparent', v: '', h: 'Use client address as source for server connections' },
        { d: 'option nolinger', v: '', h: 'Immediately close connections (RST instead of FIN)' },
        { d: 'rate-limit sessions', v: '100', h: 'Limit incoming sessions per second per frontend' },
    ],
    errors: [
        { d: 'errorfile 400', v: '/etc/haproxy/errors/400.http', h: 'Custom error page: 400 Bad Request' },
        { d: 'errorfile 403', v: '/etc/haproxy/errors/403.http', h: 'Custom error page: 403 Forbidden' },
        { d: 'errorfile 408', v: '/etc/haproxy/errors/408.http', h: 'Custom error page: 408 Request Timeout' },
        { d: 'errorfile 500', v: '/etc/haproxy/errors/500.http', h: 'Custom error page: 500 Internal Server Error' },
        { d: 'errorfile 502', v: '/etc/haproxy/errors/502.http', h: 'Custom error page: 502 Bad Gateway' },
        { d: 'errorfile 503', v: '/etc/haproxy/errors/503.http', h: 'Custom error page: 503 Service Unavailable' },
        { d: 'errorfile 504', v: '/etc/haproxy/errors/504.http', h: 'Custom error page: 504 Gateway Timeout' },
        { d: 'errorloc', v: '503 http://maintenance.example.com/', h: 'Redirect to URL on error (303 See Other)' },
        { d: 'errorloc302', v: '503 http://maintenance.example.com/', h: 'Redirect to URL on error (302 Found)' },
        { d: 'errorloc303', v: '503 http://maintenance.example.com/', h: 'Redirect to URL on error (303 See Other)' },
    ],
    health: [
        { d: 'default-server', v: 'inter 3s fall 3 rise 2', h: 'Default check: 3s interval, 3 fails = DOWN, 2 ok = UP' },
        { d: 'default-server', v: 'inter 5s fall 3 rise 2 maxconn 256', h: 'Check with connection limit per server' },
        { d: 'default-server', v: 'check', h: 'Enable health checks for all servers by default' },
        { d: 'default-server', v: 'init-addr libc,none', h: 'DNS resolution: try libc, then skip if unresolvable' },
        { d: 'default-server', v: 'resolvers mydns', h: 'Use named DNS resolver for server addresses' },
        { d: 'default-server', v: 'inter 10s fastinter 2s downinter 5s', h: 'Adaptive check intervals: normal/fast/down' },
        { d: 'default-server', v: 'on-error mark-down on-marked-down shutdown-sessions', h: 'Error handling: mark down and close sessions' },
    ],
    compression: [
        { d: 'compression', v: 'algo gzip', h: 'Enable gzip compression algorithm' },
        { d: 'compression', v: 'algo deflate', h: 'Enable deflate compression algorithm' },
        { d: 'compression', v: 'algo identity', h: 'Identity (no compression) - used for disabling' },
        { d: 'compression', v: 'type text/html text/plain text/css application/javascript application/json', h: 'MIME types eligible for compression' },
        { d: 'compression', v: 'offload', h: 'Remove Accept-Encoding from server requests (HAProxy handles compression)' },
    ],
};

/* State */
let currentGlobalTab = 'all';
let currentDefaultsTab = 'all';
let allGlobalSettings = [];
let allDefaultsSettings = [];
let globalSearchQuery = '';
let defaultsSearchQuery = '';

/* Updates the search query and re-renders the settings table for the given kind */
function filterSettings(kind) {
    const q = document.getElementById(`${kind}-search`)?.value || '';
    if (kind === 'global') globalSearchQuery = q;
    else defaultsSearchQuery = q;
    renderSettingsTable(kind);
}

/* Fetches settings from the API for global or defaults and renders them */
async function loadSettings(kind) {
    const endpoint = kind === 'global' ? '/api/global-settings' : '/api/default-settings';
    try {
        const d = await api(endpoint);
        const rows = d.items || d;
        if (kind === 'global') allGlobalSettings = rows;
        else allDefaultsSettings = rows;
        renderSettingsTable(kind);
    } catch (err) { toast(err.message, 'error'); }
}

/* Renders the settings table with category tabs, search filtering, and reorder controls */
function renderSettingsTable(kind) {
    const cats = kind === 'global' ? GLOBAL_CATS : DEFAULTS_CATS;
    const categorizeFn = kind === 'global' ? categorizeGlobal : categorizeDefaults;
    const rows = kind === 'global' ? allGlobalSettings : allDefaultsSettings;
    const searchQ = (kind === 'global' ? globalSearchQuery : defaultsSearchQuery).toLowerCase().trim();
    const activeTab = kind === 'global' ? currentGlobalTab : currentDefaultsTab;

    // Count per category (before search filter)
    const counts = {};
    Object.keys(cats).forEach(k => counts[k] = 0);
    counts.all = rows.length;
    rows.forEach(r => {
        const cat = categorizeFn(r.directive);
        counts[cat] = (counts[cat] || 0) + 1;
    });

    // Render tabs
    const tabsEl = document.getElementById(`${kind}-tabs`);
    tabsEl.innerHTML = Object.entries(cats).map(([key, cat]) =>
        `<button class="stab ${key === activeTab ? 'active' : ''}" onclick="switchSettingsTab('${kind}','${key}')">
            ${cat.label}
            <span class="stab-count">${counts[key] || 0}</span>
        </button>`
    ).join('');

    // Filter by tab
    let filtered = activeTab === 'all' ? [...rows] : rows.filter(r => categorizeFn(r.directive) === activeTab);

    // Filter by search
    if (searchQ) {
        filtered = filtered.filter(r =>
            (r.directive || '').toLowerCase().includes(searchQ) ||
            (r.value || '').toLowerCase().includes(searchQ) ||
            (r.comment || '').toLowerCase().includes(searchQ)
        );
    }

    // Sort by sort_order for display
    filtered.sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0));

    const tbody = document.querySelector(`#${kind}-table tbody`);
    const empty = document.getElementById(`${kind}-empty`);
    const wrap = document.querySelector(`#${kind}-table`).parentElement;
    if (!filtered.length) { wrap.style.display = 'none'; empty.style.display = 'block'; return; }
    wrap.style.display = 'block'; empty.style.display = 'none';

    const allFiltered = filtered; // for reorder context
    tbody.innerHTML = filtered.map((r, idx) => {
        const catBadge = categorizeFn(r.directive);
        const catLabel = cats[catBadge]?.label || catBadge;
        const isFirst = idx === 0;
        const isLast = idx === filtered.length - 1;
        return `<tr class="sett-row" data-id="${r.id}" data-order="${r.sort_order}">
            <td>
                <span class="sett-directive">${escHtml(r.directive)}</span>
                <span class="sett-cat-badge">${escHtml(catLabel)}</span>
            </td>
            <td class="mono sett-value">${escHtml(r.value || '')}</td>
            <td class="muted sett-comment">${escHtml(r.comment || '')}</td>
            <td class="sett-order-cell">
                <div class="reorder-group">
                    <button class="reorder-btn${isFirst ? ' disabled' : ''}" onclick="reorderSetting('${kind}',${r.id},'up')" title="Move up" ${isFirst ? 'disabled' : ''}>
                        ${icon('chevron-up', 12, 2.5)}
                    </button>
                    <span class="reorder-num">${r.sort_order}</span>
                    <button class="reorder-btn${isLast ? ' disabled' : ''}" onclick="reorderSetting('${kind}',${r.id},'down')" title="Move down" ${isLast ? 'disabled' : ''}>
                        ${icon('chevron-down', 12, 2.5)}
                    </button>
                </div>
            </td>
            <td class="actions">
                <button class="btn-icon" onclick="openSettingModal('${kind}',${escJsonAttr(r)})">${SVG.edit}</button>
                <button class="btn-icon danger" onclick="deleteSetting('${kind}',${r.id})">${SVG.del}</button>
            </td>
        </tr>`;
    }).join('');
}

/* Swaps sort_order of a setting with its neighbor and reloads the table */
async function reorderSetting(kind, id, direction) {
    const rows = kind === 'global' ? allGlobalSettings : allDefaultsSettings;
    const sorted = [...rows].sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0));
    const idx = sorted.findIndex(r => r.id === id);
    if (idx < 0) return;

    const swapIdx = direction === 'up' ? idx - 1 : idx + 1;
    if (swapIdx < 0 || swapIdx >= sorted.length) return;

    const endpoint = kind === 'global' ? '/api/global-settings' : '/api/default-settings';
    const current = sorted[idx];
    const swap = sorted[swapIdx];
    const curOrder = current.sort_order ?? 0;
    const swpOrder = swap.sort_order ?? 0;

    // Ensure different orders (if same, offset them)
    const newCurOrder = swpOrder;
    const newSwpOrder = curOrder === swpOrder ? curOrder + (direction === 'up' ? 1 : -1) : curOrder;

    try {
        await Promise.all([
            api(`${endpoint}/${current.id}`, {
                method: 'PUT',
                body: JSON.stringify({ directive: current.directive, value: current.value, comment: current.comment, sort_order: newCurOrder })
            }),
            api(`${endpoint}/${swap.id}`, {
                method: 'PUT',
                body: JSON.stringify({ directive: swap.directive, value: swap.value, comment: swap.comment, sort_order: newSwpOrder })
            })
        ]);
        await loadSettings(kind);
        toast('Order updated', 'info');
    } catch (err) { toast(err.message, 'error'); }
}

/* Switches the active category tab and reloads settings */
function switchSettingsTab(kind, tab) {
    if (kind === 'global') currentGlobalTab = tab;
    else currentDefaultsTab = tab;
    loadSettings(kind);
}

/* Opens the Quick Add modal for global settings with preset templates */
function openGlobalQuickAdd() {
    openSettingsAddModal('global', GLOBAL_PRESETS, GLOBAL_CATS);
}

/* Opens the Quick Add modal for defaults settings with preset templates */
function openDefaultsQuickAdd() {
    openSettingsAddModal('defaults', DEFAULTS_PRESETS, DEFAULTS_CATS);
}

/* Opens the add-setting modal with a grid of preset templates and a custom form */
function openSettingsAddModal(kind, presetsDict, catsDict) {
    const kindLabel = kind === 'global' ? 'Global' : 'Default';
    const allPresets = Object.values(presetsDict).flat();
    const catKeys = Object.keys(presetsDict);
    const catLabels = {};
    Object.entries(catsDict).forEach(([k, v]) => { if (k !== 'all') catLabels[k] = v.label || k; });

    /* Build cards with category attribute */
    let globalIdx = 0;
    const cardsHtml = catKeys.map(cat => {
        return (presetsDict[cat] || []).map(p => {
            const idx = globalIdx++;
            return `<div class="dir-card" data-preset-idx="${idx}" data-scat="${escHtml(cat)}" data-search-text="${escHtml((p.d + ' ' + p.v + ' ' + p.h).toLowerCase())}" onclick="applySettingPreset(${idx})">
                <div class="dir-card-name">${escHtml(p.d)}</div>
                ${p.v ? `<div class="dir-card-val">${escHtml(p.v)}</div>` : ''}
                <div class="dir-card-desc">${escHtml(p.h)}</div>
            </div>`;
        }).join('');
    }).join('');

    /* Category tabs - "All" is default */
    const tabsHtml = `<button class="stab active" onclick="filterSettingsPresets('${kind}','all')">All</button>` +
        catKeys.filter(k => catLabels[k]).map(k =>
            `<button class="stab" onclick="filterSettingsPresets('${kind}','${k}')">${catLabels[k]}</button>`
        ).join('');

    const STI = {
        templates: icon('grid', 15),
        directive: icon('code', 15),
        opts: icon('settings', 15),
    };

    openModal(`
        <h3>Add ${kindLabel} Setting</h3>
        <p class="modal-subtitle">Add a ${kindLabel.toLowerCase()} HAProxy directive. Pick a template or enter a custom directive below.</p>

        ${allPresets.length ? `
            <div class="form-section-title">${STI.templates} Quick Add Templates <span class="stab-count">${allPresets.length}</span></div>
            <div class="stabs" style="margin-bottom:.6rem">${tabsHtml}</div>
            <div class="preset-search-wrap" style="margin-bottom:.75rem">
                ${icon('search')}
                <input id="preset-filter" placeholder="Search templates..." oninput="filterSettingsPresetSearch('${kind}')">
            </div>
            <div class="dir-grid" id="preset-grid">${cardsHtml}</div>
            <hr class="form-divider">
        ` : ''}

        <div class="form-section-title">${STI.directive} Directive Details</div>
        <div class="form-row"><div><label>Directive</label>
            <input id="m-directive" placeholder="e.g. maxconn, log, timeout connect">
            <div class="form-help">HAProxy configuration directive name</div></div>
        <div><label>Value</label>
            <input id="m-value" placeholder="e.g. 50000">
            <div class="form-help">Directive parameter or value</div></div></div>

        <hr class="form-divider">
        <div class="form-collapsible-head" onclick="toggleCollapsible(this)">
            ${STI.opts} Options ${SVG.chevron}
        </div>
        <div class="form-collapsible-body">
            <div class="form-row"><div><label>Comment</label>
                <input id="m-comment" placeholder="Optional description">
                <div class="form-help">Internal note for documentation</div></div>
            <div><label>Sort Order</label>
                <input type="number" id="m-sort" value="0">
                <div class="form-help">Lower numbers appear first in the config</div></div></div>
        </div>

        <div class="modal-actions">
            <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="saveSetting('${kind}',null)">Save</button>
        </div>
    `, { wide: true });
    window._currentPresets = allPresets;
    window._currentPresetsCat = 'all';
}

/* Filters the preset template grid by category tab */
function filterSettingsPresets(kind, cat) {
    window._currentPresetsCat = cat;
    const catLabels = kind === 'global' ? GLOBAL_CATS : DEFAULTS_CATS;
    const label = cat === 'all' ? cat : (catLabels[cat]?.label || cat);
    filterPresetGrid('preset-grid', 'preset-filter', 'scat', label);
}

/* Filters preset templates by search text input */
function filterSettingsPresetSearch(kind) {
    const q = (document.getElementById('preset-filter')?.value || '').toLowerCase().trim();
    if (!q) { filterSettingsPresets(kind, window._currentPresetsCat || 'all'); return; }
    searchPresetGrid('preset-grid', 'preset-filter', 'scat');
}

/* Fills the directive form with values from a selected preset template */
function applySettingPreset(idx) {
    const p = window._currentPresets[idx];
    if (!p) return;
    document.getElementById('m-directive').value = p.d;
    document.getElementById('m-value').value = p.v;
    document.getElementById('m-comment').value = p.h;
    // Scroll down to the form
    document.getElementById('m-directive').scrollIntoView({ behavior: 'smooth', block: 'center' });
}

/* Opens the edit modal for an existing setting with pre-filled values */
function openSettingModal(kind, existing) {
    const kindLabel = kind === 'global' ? 'Global' : 'Default';

    const SEI = {
        directive: icon('code', 15),
        opts: icon('settings', 15),
    };

    openModal(`
        <h3>Edit ${kindLabel} Setting</h3>
        <p class="modal-subtitle">Modify the HAProxy ${kindLabel.toLowerCase()} directive, its value, and metadata.</p>

        <div class="form-section-title">${SEI.directive} Directive Details</div>
        <div class="form-row"><div><label>Directive</label>
            <input id="m-directive" value="${escHtml(existing.directive || '')}">
            <div class="form-help">HAProxy configuration directive name</div></div>
        <div><label>Value</label>
            <input id="m-value" value="${escHtml(existing.value || '')}">
            <div class="form-help">Directive parameter or value</div></div></div>

        <hr class="form-divider">
        <div class="form-collapsible-head" onclick="toggleCollapsible(this)">
            ${SEI.opts} Options ${SVG.chevron}
        </div>
        <div class="form-collapsible-body">
            <div class="form-row"><div><label>Comment</label>
                <input id="m-comment" value="${escHtml(existing.comment || '')}">
                <div class="form-help">Internal note for documentation</div></div>
            <div><label>Sort Order</label>
                <input type="number" id="m-sort" value="${existing.sort_order ?? 0}">
                <div class="form-help">Lower numbers appear first in the config</div></div></div>
        </div>

        <div class="modal-actions">
            <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="saveSetting('${kind}',${existing.id})">Save</button>
        </div>
    `);
}

/* Saves a new or existing setting via POST/PUT to the API */
async function saveSetting(kind, id) {
    const endpoint = kind === 'global' ? '/api/global-settings' : '/api/default-settings';
    const body = {
        directive: document.getElementById('m-directive').value,
        value: document.getElementById('m-value').value,
        comment: document.getElementById('m-comment').value,
        sort_order: parseInt(document.getElementById('m-sort').value) || 0
    };
    try {
        if (id) await api(`${endpoint}/${id}`, { method: 'PUT', body: JSON.stringify(body) });
        else await api(endpoint, { method: 'POST', body: JSON.stringify(body) });
        closeModal();
        toast(id ? 'Setting updated' : 'Setting added');
        loadSettings(kind);
    } catch (err) { toast(err.message, 'error'); }
}

/* Deletes a setting after confirmation */
async function deleteSetting(kind, id) {
    const endpoint = kind === 'global' ? '/api/global-settings' : '/api/default-settings';
    await crudDelete(`${endpoint}/${id}`, 'Delete this setting?', () => loadSettings(kind));
}
