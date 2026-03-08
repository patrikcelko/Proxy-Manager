/**
 * Settings Section
 * ================
 *
 * Manages HAProxy global and defaults directives with category
 * filtering, preset quick-add templates, drag-reorder support,
 * and full CRUD operations via modal forms.
 */

import { api, toast } from "../core/api";
import { icon, SVG } from "../core/icons";
import { openModal, closeModal } from "../core/ui";
import { escHtml, escJsonAttr, filterPresetGrid, searchPresetGrid } from "../core/utils";
import type { Setting, SettingPreset, CategoryDef } from "../types";

/* Category definitions  */

/** Category tabs for the global settings section. */
export const GLOBAL_CATS: Record<string, CategoryDef> = {
    all: { label: "All" },
    process: { label: "Process" },
    perf: { label: "Performance" },
    ssl: { label: "SSL/TLS" },
    logging: { label: "Logging" },
    security: { label: "Security" },
    dns: { label: "DNS" },
    tuning: { label: "Tuning" },
    other: { label: "Other" },
};

/** Category tabs for the defaults settings section. */
export const DEFAULTS_CATS: Record<string, CategoryDef> = {
    all: { label: "All" },
    timeout: { label: "Timeouts" },
    logging: { label: "Logging" },
    http: { label: "HTTP" },
    balance: { label: "Balancing" },
    health: { label: "Health" },
    retry: { label: "Retry" },
    perf: { label: "Performance" },
    other: { label: "Other" },
};

/** Assigns a global directive to one of the GLOBAL_CATS categories. */
export function categorizeGlobal(dir: string): string {
    const d = (dir || "").toLowerCase().trim();
    if (/^(daemon|nbproc|nbthread|uid|gid|user|group|chroot|pidfile|node|description|hard-stop-after|external-check|insecure|pp2-never-send-local|close-spread-time|cluster-secret|expose-experimental|grace|limited-quic|localpeer|numa-cpu-mapping|presetenv|resetenv|setcwd|setenv|strict-limits|wurfl-|51degrees-|deviceatlas-)/.test(d)) return "process";
    if (/^(maxconn|maxpipes|maxsslconn|maxsslrate|maxconnrate|maxsessrate|maxzlibmem|noepoll|nopoll|nosplice|spread-checks|busy-polling|max-spread-checks|maxcompcpuusage|ulimit-n|fd-hard-limit|memory-hot-size|no\s*quic|quic-cc-algo|quic-socket)/.test(d)) return "perf";
    if (/^(ssl-|ca-base|crt-base|issuers-chain-path|ssl_|tune.ssl|httpclient.ssl)/.test(d)) return "ssl";
    if (/^(log\b|log-send-hostname|log-tag|httpclient.resolvers.prefer)/.test(d)) return "logging";
    if (/^(stats\b|h1-case-adjust|h2-header-table-size|http-err-codes|http-fail-codes|httpclient.retries|httpclient.timeout|set-var|lua-|debug|quiet|zero-warning|anonkey)/.test(d)) return "security";
    if (/^(server-state-|tune\.)/.test(d)) return "tuning";
    return "other";
}

/** Assigns a defaults directive to one of the DEFAULTS_CATS categories. */
export function categorizeDefaults(dir: string): string {
    const d = (dir || "").toLowerCase().trim();
    if (/^timeout/.test(d)) return "timeout";
    if (/^(log\b|option\s+(httplog|dontlognull|tcplog|logasap|log-))/.test(d)) return "logging";
    if (/^(option\s+(forwardfor|http-server-close|http-keep-alive|httpclose|http-use-htx|prefer-last-server)|http-request|http-response|compression|http-after-response|http-check|http-reuse|h1-case-adjust|errorloc|errorfile)/.test(d)) return "http";
    if (/^(balance|hash-type|source)/.test(d)) return "balance";
    if (/^(option\s+(httpchk|ssl-hello-chk|smtpchk|pgsql-check|mysql-check|redis-check|ldap-check|tcp-check)|external-check|default-server)/.test(d)) return "health";
    if (/^(retries|retry-on|option\s+redispatch)/.test(d)) return "retry";
    if (/^(maxconn|fullconn|rate-limit|backlog|option\s+(splice-|nolinger|tcp-smart|contstats|idle-close-on-response|independ))/.test(d)) return "perf";
    return "other";
}

/** Quick-add presets for common global directives. */
export const GLOBAL_PRESETS: SettingPreset[] = [
    { d: "log", v: "/dev/log local0", h: "Log to local syslog facility 0", c: "logging" },
    { d: "log", v: "/dev/log local1 notice", h: "Log notice-level to facility 1", c: "logging" },
    { d: "log", v: "127.0.0.1:514 local0", h: "Send logs to remote syslog on localhost", c: "logging" },
    { d: "log-send-hostname", v: "", h: "Include hostname in syslog messages", c: "logging" },
    { d: "log-tag", v: "haproxy", h: 'Set syslog tag to "haproxy"', c: "logging" },
    { d: "daemon", v: "", h: "Run HAProxy in background as a daemon", c: "process" },
    { d: "nbthread", v: "4", h: "Use 4 threads for processing", c: "process" },
    { d: "nbthread", v: "auto", h: "Auto-detect thread count from CPU cores", c: "process" },
    { d: "pidfile", v: "/var/run/haproxy.pid", h: "Write PID to file for management", c: "process" },
    { d: "chroot", v: "/var/lib/haproxy", h: "Chroot to directory for security", c: "process" },
    { d: "user", v: "haproxy", h: "Run as unprivileged user", c: "process" },
    { d: "group", v: "haproxy", h: "Run under haproxy group", c: "process" },
    { d: "hard-stop-after", v: "30s", h: "Force stop after 30s during graceful shutdown", c: "process" },
    { d: "node", v: "haproxy-01", h: "Set node name for stats page identification", c: "process" },
    { d: "description", v: "HAProxy Load Balancer", h: "Human-readable instance description", c: "process" },
    { d: "maxconn", v: "10000", h: "Global connection limit (moderate)", c: "perf" },
    { d: "maxconn", v: "50000", h: "Global connection limit (high)", c: "perf" },
    { d: "maxconn", v: "100000", h: "Global connection limit (very high)", c: "perf" },
    { d: "maxsslconn", v: "10000", h: "Maximum concurrent SSL connections", c: "perf" },
    { d: "maxconnrate", v: "1000", h: "Max new connections per second", c: "perf" },
    { d: "maxsessrate", v: "1000", h: "Max new sessions per second", c: "perf" },
    { d: "maxsslrate", v: "1000", h: "Max new SSL handshakes per second", c: "perf" },
    { d: "maxpipes", v: "1000", h: "Max pipes for splice offloading", c: "perf" },
    { d: "spread-checks", v: "5", h: "Spread health checks over 0-5% of interval", c: "perf" },
    { d: "maxzlibmem", v: "128", h: "Max RAM (MB) for zlib compression", c: "perf" },
    { d: "ulimit-n", v: "200000", h: "Max file descriptors (auto if unset)", c: "perf" },
    { d: "ssl-default-bind-ciphers", v: "ECDHE+AESGCM:!SHA1", h: "Strong TLS 1.2 cipher suite for binds", c: "ssl" },
    { d: "ssl-default-bind-ciphersuites", v: "TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256", h: "TLS 1.3 cipher suites for binds", c: "ssl" },
    { d: "ssl-default-bind-options", v: "ssl-min-ver TLSv1.2 no-tls-tickets", h: "Enforce TLS 1.2+ with no tickets", c: "ssl" },
    { d: "ssl-default-server-ciphers", v: "ECDHE+AESGCM:!SHA1", h: "Strong TLS 1.2 cipher suite for servers", c: "ssl" },
    { d: "ssl-default-server-options", v: "ssl-min-ver TLSv1.2 no-tls-tickets", h: "Enforce TLS 1.2+ for servers", c: "ssl" },
    { d: "ca-base", v: "/etc/ssl/certs", h: "Default CA certificate directory", c: "ssl" },
    { d: "crt-base", v: "/etc/ssl/private", h: "Default certificate directory", c: "ssl" },
    { d: "ssl-dh-param-file", v: "/etc/haproxy/dhparams.pem", h: "DH parameters file for forward secrecy", c: "ssl" },
    { d: "tune.ssl.default-dh-param", v: "2048", h: "Default DH parameter size (bits)", c: "ssl" },
    { d: "tune.ssl.cachesize", v: "20000", h: "SSL session cache entries", c: "ssl" },
    { d: "tune.ssl.lifetime", v: "300", h: "SSL session cache TTL (seconds)", c: "ssl" },
    { d: "tune.ssl.maxrecord", v: "1419", h: "Optimize SSL record size for PMTU", c: "ssl" },
    { d: "stats socket", v: "/var/run/haproxy.sock mode 660 level admin", h: "Unix stats socket with admin access", c: "security" },
    { d: "stats socket", v: "/var/run/haproxy.sock mode 660 level operator", h: "Unix stats socket with operator access", c: "security" },
    { d: "stats timeout", v: "30s", h: "Stats socket idle timeout", c: "security" },
    { d: "tune.bufsize", v: "16384", h: "Buffer size per connection (16 KB)", c: "tuning" },
    { d: "tune.bufsize", v: "32768", h: "Buffer size per connection (32 KB)", c: "tuning" },
    { d: "tune.maxrewrite", v: "1024", h: "Header rewrite buffer space (bytes)", c: "tuning" },
    { d: "tune.http.maxhdr", v: "101", h: "Max HTTP headers per request", c: "tuning" },
    { d: "tune.comp.maxlevel", v: "5", h: "Compression level (1=fast, 9=best)", c: "tuning" },
    { d: "tune.h2.header-table-size", v: "4096", h: "HTTP/2 HPACK table size", c: "tuning" },
    { d: "tune.h2.max-concurrent-streams", v: "100", h: "HTTP/2 max concurrent streams", c: "tuning" },
    { d: "tune.h2.initial-window-size", v: "65535", h: "HTTP/2 initial flow-control window", c: "tuning" },
    { d: "server-state-file", v: "/var/lib/haproxy/server-state", h: "Persist server states across reloads", c: "tuning" },
    { d: "server-state-base", v: "/var/lib/haproxy/states/", h: "Directory for per-backend state files", c: "tuning" },
];

/** Quick-add presets for common defaults directives. */
export const DEFAULTS_PRESETS: SettingPreset[] = [
    { d: "timeout connect", v: "5s", h: "Max time to connect to server", c: "timeout" },
    { d: "timeout client", v: "30s", h: "Client-side inactivity timeout", c: "timeout" },
    { d: "timeout server", v: "30s", h: "Server-side inactivity timeout", c: "timeout" },
    { d: "timeout http-request", v: "10s", h: "Max time to receive full client request", c: "timeout" },
    { d: "timeout http-keep-alive", v: "5s", h: "Idle time between HTTP requests", c: "timeout" },
    { d: "timeout queue", v: "30s", h: "Max time waiting in queue for a slot", c: "timeout" },
    { d: "timeout check", v: "5s", h: "Health check response timeout", c: "timeout" },
    { d: "timeout tunnel", v: "1h", h: "Tunnel/WebSocket idle timeout", c: "timeout" },
    { d: "timeout tarpit", v: "60s", h: "Duration to hold tarpitted connections", c: "timeout" },
    { d: "timeout client-fin", v: "5s", h: "Timeout for half-closed client connections", c: "timeout" },
    { d: "timeout server-fin", v: "5s", h: "Timeout for half-closed server connections", c: "timeout" },
    { d: "log", v: "global", h: "Use global log configuration", c: "logging" },
    { d: "option httplog", v: "", h: "Enable detailed HTTP request logging", c: "logging" },
    { d: "option dontlognull", v: "", h: "Don't log connections with no data", c: "logging" },
    { d: "option tcplog", v: "", h: "Enable TCP connection logging", c: "logging" },
    { d: "option logasap", v: "", h: "Log as soon as possible (before response)", c: "logging" },
    { d: "option log-health-checks", v: "", h: "Log the result of health checks", c: "logging" },
    { d: "mode", v: "http", h: "Set default mode to HTTP (Layer 7)", c: "http" },
    { d: "mode", v: "tcp", h: "Set default mode to TCP (Layer 4)", c: "http" },
    { d: "option forwardfor", v: "except 127.0.0.0/8", h: "Add X-Forwarded-For header", c: "http" },
    { d: "option http-server-close", v: "", h: "Close server conn after each response", c: "http" },
    { d: "option http-keep-alive", v: "", h: "Enable HTTP keep-alive connections", c: "http" },
    { d: "option httpclose", v: "", h: "Force close HTTP connections", c: "http" },
    { d: "http-reuse", v: "safe", h: "Reuse idle server connections (safe mode)", c: "http" },
    { d: "http-reuse", v: "aggressive", h: "Aggressively reuse server connections", c: "http" },
    { d: "compression algo", v: "gzip", h: "Default compression using gzip", c: "http" },
    { d: "compression type", v: "text/html text/plain text/css application/json application/javascript", h: "Content types to compress", c: "http" },
    { d: "errorfile 400", v: "/etc/haproxy/errors/400.http", h: "Custom error page for 400 Bad Request", c: "http" },
    { d: "errorfile 403", v: "/etc/haproxy/errors/403.http", h: "Custom error page for 403 Forbidden", c: "http" },
    { d: "errorfile 500", v: "/etc/haproxy/errors/500.http", h: "Custom error page for 500 Internal", c: "http" },
    { d: "errorfile 502", v: "/etc/haproxy/errors/502.http", h: "Custom error page for 502 Bad Gateway", c: "http" },
    { d: "errorfile 503", v: "/etc/haproxy/errors/503.http", h: "Custom error page for 503 Unavailable", c: "http" },
    { d: "balance", v: "roundrobin", h: "Round-robin load balancing (default)", c: "balance" },
    { d: "balance", v: "leastconn", h: "Send to server with fewest connections", c: "balance" },
    { d: "balance", v: "source", h: "Hash source IP for session persistence", c: "balance" },
    { d: "hash-type", v: "consistent", h: "Consistent hashing for minimal disruption", c: "balance" },
    { d: "option httpchk", v: "HEAD /health HTTP/1.1\\r\\nHost:\\ localhost", h: "HTTP health check with HEAD request", c: "health" },
    { d: "option httpchk", v: "GET /status HTTP/1.1\\r\\nHost:\\ localhost", h: "HTTP health check with GET request", c: "health" },
    { d: "option ssl-hello-chk", v: "", h: "Check SSL handshake capability", c: "health" },
    { d: "option tcp-check", v: "", h: "Enable scriptable TCP health checks", c: "health" },
    { d: "option pgsql-check", v: "user haproxy", h: "PostgreSQL connection check", c: "health" },
    { d: "option mysql-check", v: "user haproxy", h: "MySQL connection check", c: "health" },
    { d: "option redis-check", v: "", h: "Redis PING health check", c: "health" },
    { d: "option ldap-check", v: "", h: "LDAP bind health check", c: "health" },
    { d: "option smtpchk", v: "HELO localhost", h: "SMTP health check", c: "health" },
    { d: "default-server", v: "inter 3s fall 3 rise 2", h: "Default server check parameters", c: "health" },
    { d: "default-server", v: "inter 5s fall 3 rise 2 maxconn 256", h: "Default with connection limit", c: "health" },
    { d: "retries", v: "3", h: "Retry failed connections 3 times", c: "retry" },
    { d: "option redispatch", v: "", h: "Allow retry on different server", c: "retry" },
    { d: "retry-on", v: "all-retryable-errors", h: "Retry on all retryable errors", c: "retry" },
    { d: "retry-on", v: "conn-failure empty-response response-timeout", h: "Retry on connection failures", c: "retry" },
    { d: "maxconn", v: "3000", h: "Default max connections per frontend", c: "perf" },
    { d: "fullconn", v: "1000", h: "Connection count for weight calculation", c: "perf" },
    { d: "option splice-auto", v: "", h: "Auto splice for zero-copy (Linux)", c: "perf" },
    { d: "option nolinger", v: "", h: "Reset connections on close (no TIME_WAIT)", c: "perf" },
    { d: "option tcp-smart-accept", v: "", h: "Delay accept until data arrives", c: "perf" },
    { d: "option tcp-smart-connect", v: "", h: "Delay SYN until data ready to send", c: "perf" },
    { d: "option contstats", v: "", h: "Continuous traffic stats per connection", c: "perf" },
    { d: "option idle-close-on-response", v: "", h: "Close idle backend connections on response", c: "perf" },
    { d: "backlog", v: "10000", h: "TCP listen backlog queue size", c: "perf" },
];

/** Currently active settings tab (`"global"` or `"defaults"`). */
let settTab: string = "global";

/** Returns the correct API base path for the active (or given) settings tab. */
function settingsApiBase(tab?: string): string {
    const t = tab || settTab;
    return t === "global" ? "/api/global-settings" : "/api/default-settings";
}

/** Fetches settings from the API and renders the table for the given tab. */
export async function loadSettings(tab?: string): Promise<void> {
    if (tab) settTab = tab;
    try {
        const d: { items: Setting[] } = await api(settingsApiBase());
        const items: Setting[] = d.items || d;
        renderSettingsTable(items);
        switchSettingsTab(settTab);
    } catch (err) {
        toast((err as Error).message, "error");
    }
}

/** Renders the settings table rows with category tabs and reorder controls. */
export function renderSettingsTable(items: Setting[]): void {
    const cats = settTab === "global" ? GLOBAL_CATS : DEFAULTS_CATS;
    const catFn = settTab === "global" ? categorizeGlobal : categorizeDefaults;

    const tbody = document.querySelector(`#${settTab}-table tbody`) as HTMLTableSectionElement | null;
    const empty = document.getElementById(`${settTab}-empty`);
    const wrap = document.querySelector(`#${settTab}-table`)?.parentElement as HTMLElement | null;
    if (!items.length) {
        if (wrap) wrap.style.display = "none";
        if (empty) empty.style.display = "block";
        return;
    }
    if (wrap) wrap.style.display = "block";
    if (empty) empty.style.display = "none";

    items.sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0));

    const catTabs = Object.entries(cats)
        .map(([k, v]) => {
            const cnt = k === "all" ? items.length : items.filter((i) => catFn(i.directive) === k).length;
            if (k !== "all" && cnt === 0) return "";
            return `<button class="stab${k === "all" ? " active" : ""}" onclick="filterSettingsCat('${k}')">${v.label} <span class="stab-count">${cnt}</span></button>`;
        })
        .join("");

    const tabsEl = document.getElementById(`${settTab}-tabs`);
    if (tabsEl) tabsEl.innerHTML = catTabs;

    if (tbody) tbody.innerHTML = items
        .map((s, idx) => {
            const isFirst = idx === 0;
            const isLast = idx === items.length - 1;
            const cat = catFn(s.directive);
            return `<tr data-sett-cat="${cat}" data-entity-name="${s.id}">
            <td class="sett-directive">${escHtml(s.directive)}</td>
            <td class="mono sett-value">${escHtml(s.value)}</td>
            <td class="sett-order-cell">
                <div class="reorder-group">
                    <button class="reorder-btn${isFirst ? " disabled" : ""}" onclick="reorderSetting(${s.id},'up')" title="Move up" ${isFirst ? "disabled" : ""}>${icon("chevron-up", 12, 2.5)}</button>
                    <span class="reorder-num">${s.sort_order}</span>
                    <button class="reorder-btn${isLast ? " disabled" : ""}" onclick="reorderSetting(${s.id},'down')" title="Move down" ${isLast ? "disabled" : ""}>${icon("chevron-down", 12, 2.5)}</button>
                </div>
            </td>
            <td class="muted sett-comment">${escHtml(s.comment || "")}</td>
            <td class="actions"><button class="btn-icon" onclick='openSettingModal(${escJsonAttr(s)})'>${SVG.edit}</button>
                <button class="btn-icon danger" onclick="deleteSetting(${s.id})">${SVG.del}</button></td>
        </tr>`;
        })
        .join("");
}

/** Swaps the sort order of a setting with its neighbour in the given direction. */
export function reorderSetting(id: number, direction: string): void {
    const rows = [...document.querySelectorAll(`#${settTab}-table tbody tr`)] as HTMLTableRowElement[];
    const ids = rows.map((r) => {
        const btn = r.querySelector(".reorder-btn:not(.disabled)") as HTMLButtonElement | null;
        const onclick = btn?.getAttribute("onclick") || "";
        const m = onclick.match(/reorderSetting\((\d+)/);
        return m ? parseInt(m[1]) : null;
    });

    const sortedItems = rows.map((r) => {
        const cells = r.querySelectorAll("td");
        return {
            directive: cells[0]?.textContent || "",
            value: cells[1]?.textContent || "",
            sort_order: parseInt(r.querySelector(".reorder-num")?.textContent || "0"),
        };
    });

    const idx = ids.indexOf(id);
    if (idx < 0) return;

    const swapIdx = direction === "up" ? idx - 1 : idx + 1;
    if (swapIdx < 0 || swapIdx >= rows.length) return;

    const curOrder = sortedItems[idx].sort_order;
    const swapOrder = sortedItems[swapIdx].sort_order;

    const newCurOrder = swapOrder;
    const newSwapOrder = curOrder === swapOrder ? curOrder + (direction === "up" ? 1 : -1) : curOrder;

    const curId = id;
    const swapId = ids[swapIdx];
    if (swapId == null) return;

    Promise.all([
        api(`${settingsApiBase()}/${curId}`, { method: "PUT", body: JSON.stringify({ sort_order: newCurOrder }) }),
        api(`${settingsApiBase()}/${swapId}`, { method: "PUT", body: JSON.stringify({ sort_order: newSwapOrder }) }),
    ])
        .then(() => {
            loadSettings();
            toast("Order updated", "info");
        })
        .catch((err: Error) => toast(err.message, "error"));
}

/** Activates the given settings tab and updates the section label. */
export function switchSettingsTab(tab: string): void {
    settTab = tab;
    document.querySelectorAll<HTMLElement>(".sett-tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === tab));
    const globalLabel = document.getElementById("settings-section-label");
    if (globalLabel) globalLabel.textContent = tab === "global" ? "Global Settings" : "Defaults";
}

/** Filters the settings table rows to show only the selected category. */
export function filterSettingsCat(cat: string): void {
    const tabs = document.getElementById(`${settTab}-tabs`);
    if (tabs)
        tabs.querySelectorAll(".stab").forEach((t) => {
            const text = t.textContent?.trim().split(" ")[0];
            const catLabel = cat === "all" ? "All" : (settTab === "global" ? GLOBAL_CATS : DEFAULTS_CATS)[cat]?.label;
            t.classList.toggle("active", text === catLabel);
        });
    document.querySelectorAll<HTMLElement>(`#${settTab}-table tbody tr[data-sett-cat]`).forEach((r) => {
        r.style.display = cat === "all" || r.dataset.settCat === cat ? "" : "none";
    });
}

/** Filters settings table rows by free-text search input. */
export function filterSettings(tab: string): void {
    const input = document.getElementById(`${tab}-search`) as HTMLInputElement | null;
    const q = (input?.value || "").toLowerCase();
    document.querySelectorAll<HTMLElement>(`#${tab}-table tbody tr`).forEach((r) => {
        const text = r.textContent?.toLowerCase() || "";
        r.style.display = !q || text.includes(q) ? "" : "none";
    });
}

/** Opens the quick-add modal for global presets. */
export function openGlobalQuickAdd(): void {
    openSettingsAddModal("global");
}

/** Opens the quick-add modal for defaults presets. */
export function openDefaultsQuickAdd(): void {
    openSettingsAddModal("defaults");
}

/** Renders the preset template grid modal for the given settings type. */
export function openSettingsAddModal(type: string): void {
    const presets = type === "global" ? GLOBAL_PRESETS : DEFAULTS_PRESETS;
    const cats = [...new Set(presets.map((p) => p.c))];
    const gridId = "settAddGrid";

    const IC = { templates: icon("grid", 15), directive: icon("code", 15), opts: icon("settings", 15) };

    openModal(
        `
        <h3>Add ${type === "global" ? "Global" : "Defaults"} Setting</h3>
        <p class="modal-subtitle">Choose a template to auto-fill the form, or configure manually below.</p>

        <div class="form-collapsible" style="margin-bottom:1rem">
            <div class="form-collapsible-head open" onclick="toggleCollapsible(this)">${IC.templates} Templates <span class="stab-count">${presets.length}</span> ${SVG.chevron}</div>
            <div class="form-collapsible-body open">
                <div class="stabs" style="margin-bottom:.5rem">
                    <button class="stab active" onclick="filterSettingsPresets('all')">All</button>
                    ${cats.map((c) => `<button class="stab" onclick="filterSettingsPresets('${c}')">${c}</button>`).join("")}
                </div>
                <div class="preset-search-wrap" style="margin-bottom:.75rem">
                    ${icon("search")}
                    <input id="sett-preset-filter" placeholder="Search presets..." oninput="searchSettPresets()">
                </div>
                <div class="dir-grid" id="${gridId}">${presets
                    .map(
                        (p, i) =>
                            `<div class="dir-card" data-pcat="${escHtml(p.c)}" data-search-text="${escHtml((p.d + " " + p.v + " " + p.h).toLowerCase())}"
                     onclick="applySettingPreset('${type}',${i})">
                    <div class="dir-card-name">${escHtml(p.d)}</div>
                    ${p.v ? `<div class="dir-card-val">${escHtml(p.v)}</div>` : ""}
                    <div class="dir-card-desc">${escHtml(p.h)}</div>
                </div>`,
                    )
                    .join("")}
                </div>
            </div>
        </div>

        <hr class="form-divider">
        <div class="form-section-title">${IC.directive} Directive</div>
        <div class="form-row"><div><label>Directive <span class="required">*</span></label><input id="m-directive" value="" placeholder="e.g. maxconn, timeout connect">
            <div class="form-help">HAProxy directive name</div></div>
        <div><label>Value</label><input id="m-value" value="" placeholder="e.g. 10000, 30s">
            <div class="form-help">Directive value or parameters</div></div></div>
        <hr class="form-divider">
        <div class="form-collapsible-head" onclick="toggleCollapsible(this)">${IC.opts} Options ${SVG.chevron}</div>
        <div class="form-collapsible-body">
            <div class="form-row"><div><label>Sort Order</label><input type="number" id="m-sort" value="0">
                <div class="form-help">Lower numbers appear first in config output</div></div>
            <div><label>Comment</label><input id="m-comment" value="" placeholder="Optional description">
                <div class="form-help">Internal note for documentation</div></div></div>
        </div>
        <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="saveSetting(null)">Create Setting</button></div>
    `,
        { wide: true },
    );
}

/** Filters the preset grid cards by category tab. */
export function filterSettingsPresets(cat: string): void {
    filterPresetGrid("settAddGrid", "sett-preset-filter", "pcat", cat);
}

/** Filters the preset grid cards by free-text search input. */
export function searchSettPresets(): void {
    searchPresetGrid("settAddGrid", "sett-preset-filter", "pcat");
}

/** Applies a preset directive by filling the form fields in the modal. */
export async function applySettingPreset(type: string, idx: number): Promise<void> {
    const presets = type === "global" ? GLOBAL_PRESETS : DEFAULTS_PRESETS;
    const p = presets[idx];
    if (!p) return;

    const dirEl = document.getElementById("m-directive") as HTMLInputElement | null;
    const valEl = document.getElementById("m-value") as HTMLInputElement | null;
    const commentEl = document.getElementById("m-comment") as HTMLInputElement | null;

    if (dirEl) dirEl.value = p.d;
    if (valEl) valEl.value = p.v;
    if (commentEl) commentEl.value = p.h;

    // Scroll to the directive field so the user sees the filled form
    dirEl?.focus();
    dirEl?.scrollIntoView({ behavior: "smooth", block: "center" });
    toast("Template applied - review and save", "info");
}

/** Opens the setting edit/create modal, optionally pre-filled with existing data. */
export function openSettingModal(existing: Setting | null = null): void {
    const s = existing || ({} as Partial<Setting>);
    const IC = { directive: icon("code", 15), opts: icon("settings", 15) };

    openModal(`
        <h3>${s.id ? "Edit" : "New"} Setting</h3>
        <p class="modal-subtitle">Configure an HAProxy global or defaults directive.</p>
        <div class="form-section-title">${IC.directive} Directive</div>
        <div class="form-row"><div><label>Directive</label><input id="m-directive" value="${escHtml(s.directive || "")}" placeholder="e.g. maxconn, timeout connect">
            <div class="form-help">HAProxy directive name</div></div>
        <div><label>Value</label><input id="m-value" value="${escHtml(s.value || "")}" placeholder="e.g. 10000, 30s">
            <div class="form-help">Directive value or parameters</div></div></div>
        <hr class="form-divider">
        <div class="form-collapsible-head" onclick="toggleCollapsible(this)">${IC.opts} Options ${SVG.chevron}</div>
        <div class="form-collapsible-body">
            <div class="form-row"><div><label>Sort Order</label><input type="number" id="m-sort" value="${s.sort_order || 0}">
                <div class="form-help">Lower numbers appear first in config output</div></div>
            <div><label>Comment</label><input id="m-comment" value="${escHtml(s.comment || "")}" placeholder="Optional description">
                <div class="form-help">Internal note for documentation</div></div></div>
        </div>
        <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="saveSetting(${s.id || "null"})">Save</button></div>
    `);
}

/** Persists a new or updated setting to the API and reloads the table. */
export async function saveSetting(id: number | null): Promise<void> {
    const body = {
        directive: (document.getElementById("m-directive") as HTMLInputElement).value,
        value: (document.getElementById("m-value") as HTMLInputElement).value,
        sort_order: parseInt((document.getElementById("m-sort") as HTMLInputElement).value) || 0,
        comment: (document.getElementById("m-comment") as HTMLInputElement).value || null,
    };
    try {
        if (id) await api(`${settingsApiBase()}/${id}`, { method: "PUT", body: JSON.stringify(body) });
        else await api(settingsApiBase(), { method: "POST", body: JSON.stringify(body) });
        closeModal();
        toast(id ? "Updated" : "Created");
        loadSettings();
    } catch (err) {
        toast((err as Error).message, "error");
    }
}

/** Deletes a setting after user confirmation and reloads the table. */
export async function deleteSetting(id: number): Promise<void> {
    if (!confirm("Delete this setting?")) return;
    try {
        await api(`${settingsApiBase()}/${id}`, { method: "DELETE" });
        toast("Deleted");
        loadSettings();
    } catch (err) {
        toast((err as Error).message, "error");
    }
}
