/**
 * Frontends section
 * =================
 *
 * Manages HAProxy frontend definitions with bind addresses,
 * options/directives, categorised option tabs, IP access rules,
 * bind preset templates, and option preset templates.
 */

import { api, toast } from "../core/api";
import { icon, SVG } from "../core/icons";
import { openModal, closeModal } from "../core/ui";
import { escHtml, escJsonAttr, crudDelete, filterPresetGrid, searchPresetGrid } from "../core/utils";
import { state } from "../state";
import type { Frontend, FrontendBind, FrontendOption, CategoryDef, BindPreset, FrontendOptionPreset } from "../types";


/** Category definitions for classifying frontend options into tabs. */
export const FE_OPT_CATS: Record<string, CategoryDef> = {
    all: { label: "All" },
    logging: { label: "Logging" },
    http: { label: "HTTP" },
    security: { label: "Security" },
    routing: { label: "Routing" },
    timeout: { label: "Timeouts" },
    acl: { label: "ACL / Match" },
    perf: { label: "Performance" },
    other: { label: "Other" },
};

/** Classifies a frontend option directive into its category using regex patterns. */
export function categorizeFrontendOpt(dir: string): string {
    const d = (dir || "").toLowerCase().trim();
    if (/^option\s+(httplog|dontlognull|logasap|log-|tcplog)|^log\b/.test(d)) return "logging";
    if (/^(option\s+(forwardfor|http-server-close|http-keep-alive|httpclose|http-use-htx|prefer-last-server))|^http-request|^http-response|^compression|^http-after-response/.test(d)) return "http";
    if (/^(rate-limit|stick-table|http-request\s+(deny|tarpit|reject|track|sc-)|filter|tcp-request\s+(connection\s+reject|content\s+reject))/.test(d)) return "security";
    if (/^(use_backend|default_backend|redirect|reqrep|reqadd|rspadd|reqirep|reqdeny|reqideny)/.test(d)) return "routing";
    if (/^timeout/.test(d)) return "timeout";
    if (/^acl\b/.test(d)) return "acl";
    if (/^(maxconn|option\s+(splice-|nolinger|tcp-smart)|tune\.|fullconn|no\s+option|backlog)/.test(d)) return "perf";
    return "other";
}

/** Renders bind addresses as coloured chips, splitting multi-bind lines and extracting shared SSL suffix. */
export function renderBindChips(bindLine: string): string {
    const parts = (bindLine || "").split(",").map((p) => p.trim()).filter(Boolean);
    if (parts.length <= 1) return `<span class="bind-chip">${escHtml(bindLine)}</span>`;
    const addrParts = parts.map((p) => {
        const t = p.split(/\s+/);
        return { addr: t[0], rest: t.slice(1).join(" ") };
    });
    const firstRest = addrParts[0].rest;
    const allSameRest = addrParts.every((a) => a.rest === firstRest);
    let sharedSuffix = "";
    if (allSameRest && firstRest) {
        sharedSuffix = firstRest;
    } else {
        const lastRest = addrParts[addrParts.length - 1].rest;
        if (lastRest && addrParts.slice(0, -1).every((a) => !a.rest)) sharedSuffix = lastRest;
    }
    const addrs = sharedSuffix ? addrParts.map((a) => a.addr) : parts;
    return addrs.map((a) => `<span class="bind-chip">${escHtml(a)}</span>`).join("") + (sharedSuffix ? `<span class="bind-opts-suffix">${escHtml(sharedSuffix)}</span>` : "");
}


/** Fetches all frontends from the API and renders the cards grid. */
export async function loadFrontends(): Promise<void> {
    try {
        const d = await api("/api/frontends");
        state.allFrontends = d.items || d;
        renderFrontends(state.allFrontends);
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Filters the frontends grid by search query across name, mode, backend, comment, binds, and options. */
export function filterFrontends(): void {
    const q = ((document.getElementById("frontend-search") as HTMLInputElement).value || "").toLowerCase();
    if (!q) {
        renderFrontends(state.allFrontends);
        return;
    }
    renderFrontends(
        state.allFrontends.filter(
            (f) =>
                f.name.toLowerCase().includes(q) ||
                (f.mode || "").toLowerCase().includes(q) ||
                (f.default_backend || "").toLowerCase().includes(q) ||
                (f.comment || "").toLowerCase().includes(q) ||
                (f.binds || []).some((b) => (b.bind_line || "").toLowerCase().includes(q)) ||
                (f.options || []).some((o) => ((o.directive || "") + " " + (o.value || "") + " " + (o.comment || "")).toLowerCase().includes(q)),
        ),
    );
}

/** Renders the complete frontends card grid with entity cards, bind lists, option tabs, and IP access rules. */
export function renderFrontends(list: Frontend[]): void {
    const grid = document.getElementById("frontends-grid") as HTMLElement;
    const empty = document.getElementById("frontends-empty") as HTMLElement;
    if (!list.length) {
        grid.innerHTML = "";
        grid.style.display = "none";
        empty.style.display = "block";
        return;
    }
    grid.style.display = "flex";
    empty.style.display = "none";

    const FI = {
        bind: icon("monitor", 13),
        ssl: icon("lock", 13),
        route: icon("chevron-right", 13),
        opts: icon("terminal", 13),
        shield: icon("shield", 13),
        compress: icon("minimize", 13),
        log: icon("file-text", 13),
        forward: icon("arrow-right", 13),
    };

    grid.innerHTML = list
        .map((f) => {
            const bc = (f.binds || []).length;
            const oc = (f.options || []).length;

            const hasSSL = (f.binds || []).some((b) => /\bssl\b/i.test(b.bind_line));
            const ports = [
                ...new Set(
                    (f.binds || []).flatMap((b) => {
                        const matches = b.bind_line.match(/:(\d+)/g) || [];
                        return matches.map((m) => m.replace(":", ""));
                    }),
                ),
            ].slice(0, 4);

            const summaryPills: string[] = [];
            if (ports.length) summaryPills.push(`<span class="fe-summary-pill">${FI.bind} ${ports.join(", ")}</span>`);
            if (hasSSL) summaryPills.push(`<span class="fe-summary-pill fe-pill-ssl">${FI.ssl} SSL</span>`);
            if (f.option_forwardfor) summaryPills.push(`<span class="fe-summary-pill">${FI.forward} XFF</span>`);
            if (f.compression_algo) summaryPills.push(`<span class="fe-summary-pill">${FI.compress} gzip</span>`);
            if (f.option_httplog) summaryPills.push(`<span class="fe-summary-pill">${FI.log} log</span>`);

            const binds = (f.binds || [])
                .map(
                    (b) => `<li>
            <span class="el-main bind-parsed">${renderBindChips(b.bind_line)}</span>
            <span class="el-actions">
                <button class="btn-icon" onclick='event.stopPropagation();openBindModal(${f.id},${escJsonAttr(b)})'>${SVG.editSm}</button>
                <button class="btn-icon danger" onclick="event.stopPropagation();deleteBind(${f.id},${b.id})">${SVG.delSm}</button>
            </span></li>`,
                )
                .join("");

            const ipRules: FrontendOption[] = [];
            const regularOpts: FrontendOption[] = [];
            (f.options || []).forEach((o) => {
                const fullDir = ((o.directive || "") + " " + (o.value || "")).toLowerCase();
                if (/tcp-request\s+(connection|content)\s+(reject|accept).*src\s|http-request\s+(deny|allow).*src\s|acl\s+\S+\s+src\s/.test(fullDir)) {
                    ipRules.push(o);
                } else {
                    regularOpts.push(o);
                }
            });

            const optsByCategory: Record<string, FrontendOption[]> = {};
            regularOpts.forEach((o) => {
                const fullDir = (o.directive || "") + " " + (o.value || "");
                const cat = categorizeFrontendOpt(fullDir);
                (optsByCategory[cat] = optsByCategory[cat] || []).push(o);
            });

            const feCardId = `fe-opts-${f.id}`;
            const feIpId = `fe-ip-${f.id}`;
            const catTabs = Object.entries(FE_OPT_CATS)
                .map(([k, v]) => {
                    const cnt = k === "all" ? regularOpts.length : (optsByCategory[k] || []).length;
                    if (k !== "all" && cnt === 0) return "";
                    return `<button class="stab${k === "all" ? " active" : ""}" onclick="filterFeOpts(${f.id},'${k}')">${v.label} <span class="stab-count">${cnt}</span></button>`;
                })
                .join("");

            const opts = regularOpts
                .map((o) => {
                    const fullDir = (o.directive || "") + " " + (o.value || "");
                    return `<li data-fe-cat="${categorizeFrontendOpt(fullDir)}">
            <span class="el-main">
                <span class="sett-directive">${escHtml(o.directive)}</span>
                ${o.value ? `<span class="mono sett-value">${escHtml(o.value)}</span>` : ""}
                ${o.comment ? `<span class="muted sett-comment" title="${escHtml(o.comment)}">${escHtml(o.comment)}</span>` : ""}
            </span>
            <span class="el-actions">
                <button class="btn-icon" onclick='event.stopPropagation();openOptionModal(${f.id},${escJsonAttr(o)})'>${SVG.editSm}</button>
                <button class="btn-icon danger" onclick="event.stopPropagation();deleteOption(${f.id},${o.id})">${SVG.delSm}</button>
            </span></li>`;
                })
                .join("");

            const ipList = ipRules
                .map((o) => {
                    const fullDir = (o.directive || "") + " " + (o.value || "");
                    const isDeny = /deny|reject/i.test(fullDir);
                    return `<li>
                <span class="el-main">
                    <span class="badge ${isDeny ? "badge-danger" : "badge-ok"}" style="font-size:.65rem;margin-right:.35rem">${isDeny ? "DENY" : "ALLOW"}</span>
                    <span class="sett-directive">${escHtml(o.directive)}</span>
                    ${o.value ? `<span class="mono sett-value">${escHtml(o.value)}</span>` : ""}
                </span>
                <span class="el-actions">
                    <button class="btn-icon" onclick='event.stopPropagation();openOptionModal(${f.id},${escJsonAttr(o)})'>${SVG.editSm}</button>
                    <button class="btn-icon danger" onclick="event.stopPropagation();deleteOption(${f.id},${o.id})">${SVG.delSm}</button>
                </span></li>`;
                })
                .join("");

            const details: { l: string; v: string }[] = [];
            if (f.timeout_client) details.push({ l: "Client Timeout", v: f.timeout_client });
            if (f.timeout_http_request) details.push({ l: "HTTP Request Timeout", v: f.timeout_http_request });
            if (f.timeout_http_keep_alive) details.push({ l: "HTTP Keep-Alive", v: f.timeout_http_keep_alive });
            if (f.maxconn) details.push({ l: "Max Connections", v: String(f.maxconn) });
            if (f.compression_algo) details.push({ l: "Compression", v: `${f.compression_algo}${f.compression_type ? " (" + f.compression_type + ")" : ""}` });

            return `<div class="entity-card">
            <div class="entity-header" onclick="toggleEntityCard(this)">
                <span class="entity-title">${escHtml(f.name)}</span>
                <div class="entity-badges">
                    <span class="badge">${escHtml(f.mode || "http")}</span>
                    ${f.default_backend ? `<span class="badge badge-info">${FI.route} ${escHtml(f.default_backend)}</span>` : ""}
                </div>
                <div class="fe-summary-pills">${summaryPills.join("")}</div>
                <div class="entity-counts">
                    <span class="entity-count-item">${bc} bind${bc !== 1 ? "s" : ""}</span>
                    <span class="entity-count-item">${oc} opt${oc !== 1 ? "s" : ""}</span>
                </div>
                <div class="entity-actions">
                    <button class="btn-icon" onclick='event.stopPropagation();openFrontendModal(${escJsonAttr(f)})'>${SVG.edit}</button>
                    <button class="btn-icon danger" onclick="event.stopPropagation();deleteFrontend(${f.id})">${SVG.del}</button>
                    ${SVG.chevron}
                </div>
            </div>
            <div class="entity-body">
                ${details.length ? `<div class="entity-section fe-details-section"><div class="fe-detail-grid">${details.map((d) => `<div class="fe-detail-item"><span class="fe-detail-label">${d.l}</span><span class="fe-detail-value">${escHtml(d.v)}</span></div>`).join("")}</div></div>` : ""}
                <div class="entity-section">
                    <div class="entity-section-head">
                        <span class="entity-section-label">${FI.bind} Binds (${bc})</span>
                        <button class="btn-icon" onclick="openBindModal(${f.id})" title="Add Bind">${SVG.plus}</button>
                    </div>
                    <ul class="entity-list">${binds || '<li class="fe-empty-item"><span class="el-main muted">No binds configured</span></li>'}</ul>
                </div>
                <div class="entity-section">
                    <div class="entity-section-head">
                        <span class="entity-section-label">${FI.opts} Options (${regularOpts.length})</span>
                        <button class="btn-icon" onclick="openOptionModal(${f.id})" title="Add Option">${SVG.plus}</button>
                    </div>
                    ${regularOpts.length > 3 ? `<div class="fe-opt-search preset-search-wrap" style="margin-bottom:.5rem">${icon("search")}<input placeholder="Search options..." oninput="searchFeOpts(${f.id}, this.value)"></div>` : ""}
                    <div class="fe-opt-tabs stabs" style="margin-bottom:.5rem">${catTabs}</div>
                    <ul class="entity-list" id="${feCardId}">${opts || '<li class="fe-empty-item"><span class="el-main muted">No options configured</span></li>'}</ul>
                </div>
                ${ipRules.length ? `<div class="entity-section"><div class="entity-section-head"><span class="entity-section-label">${FI.shield} IP Access Rules (${ipRules.length})</span></div><ul class="entity-list" id="${feIpId}">${ipList}</ul></div>` : ""}
                ${f.comment ? `<div class="entity-section"><span class="entity-section-label">Comment</span><div class="entity-detail">${escHtml(f.comment)}</div></div>` : ""}
            </div>
        </div>`;
        })
        .join("");
}

/** Filters the option list within a specific frontend card by category tab. */
export function filterFeOpts(fid: number, cat: string): void {
    const list = document.getElementById(`fe-opts-${fid}`);
    if (!list) return;
    const section = list.closest(".entity-section");
    const searchInput = section?.querySelector(".fe-opt-search input") as HTMLInputElement | null;
    if (searchInput) searchInput.value = "";
    const tabsWrap = section?.querySelector(".fe-opt-tabs");
    if (tabsWrap)
        tabsWrap.querySelectorAll(".stab").forEach((t) =>
            t.classList.toggle("active", (t.textContent || "").trim().startsWith(cat === "all" ? "All" : FE_OPT_CATS[cat]?.label || "")),
        );
    list.querySelectorAll<HTMLElement>("li[data-fe-cat]").forEach((li) => {
        li.style.display = cat === "all" || li.dataset.feCat === cat ? "" : "none";
    });
}

/** Filters options in a frontend card by free-text search query. */
export function searchFeOpts(fid: number, query: string): void {
    const list = document.getElementById(`fe-opts-${fid}`);
    if (!list) return;
    const q = (query || "").toLowerCase().trim();
    const section = list.closest(".entity-section");
    const tabsWrap = section?.querySelector(".fe-opt-tabs");
    if (tabsWrap) tabsWrap.querySelectorAll(".stab").forEach((t) => t.classList.remove("active"));
    if (!q) {
        filterFeOpts(fid, "all");
        return;
    }
    list.querySelectorAll<HTMLElement>("li[data-fe-cat]").forEach((li) => {
        const text = (li.textContent || "").toLowerCase();
        li.style.display = text.includes(q) ? "" : "none";
    });
}

/** Opens the frontend create/edit modal with mode, backend, timeouts, HTTP options, and compression fields. */
export function openFrontendModal(existing: Partial<Frontend> | null = null): void {
    const f = existing || {};
    const beOpts = state.allBackends.map((b) => `<option value="${escHtml(b.name)}" ${f.default_backend === b.name ? "selected" : ""}>${escHtml(b.name)}</option>`).join("");

    const FMI = {
        core: icon("settings", 15),
        timeout: icon("clock", 15),
        http: icon("code", 15),
        compress: icon("minimize", 15),
    };

    openModal(
        `
        <h3>${f.id ? "Edit" : "New"} Frontend</h3>
        <p class="modal-subtitle">Configure a client-facing entry point with bind addresses, routing, and request processing.</p>

        <div class="form-row"><div><label>Name</label><input id="m-name" value="${escHtml(f.name || "")}" placeholder="my-frontend">
            <div class="form-help">Unique identifier for this frontend</div></div>
        <div><label>Mode</label><select id="m-mode"><option value="http" ${f.mode === "http" || !f.mode ? "selected" : ""}>HTTP</option>
            <option value="tcp" ${f.mode === "tcp" ? "selected" : ""}>TCP</option></select>
            <div class="form-help">Protocol mode (Layer 7 HTTP or Layer 4 TCP)</div></div></div>
        <div class="form-row"><div><label>Default Backend</label><select id="m-default-backend"><option value="">- None -</option>${beOpts}</select>
            <div class="form-help">Fallback backend when no ACL rule matches</div></div>
        <div><label>Max Connections</label><input type="number" id="m-maxconn" value="${f.maxconn || ""}" placeholder="e.g. 10000">
            <div class="form-help">Maximum concurrent connections</div></div></div>

        <hr class="form-divider">
        <div class="form-section-title">${FMI.timeout} Timeouts</div>
        <div class="form-row-3">
            <div><label>Client Timeout</label><input id="m-timeout-client" value="${escHtml(f.timeout_client || "")}" placeholder="30s">
                <div class="form-help">Max inactivity on client side</div></div>
            <div><label>HTTP Request Timeout</label><input id="m-timeout-http-request" value="${escHtml(f.timeout_http_request || "")}" placeholder="10s">
                <div class="form-help">Max time to receive full request</div></div>
            <div><label>HTTP Keep-Alive</label><input id="m-timeout-http-keep-alive" value="${escHtml(f.timeout_http_keep_alive || "")}" placeholder="5s">
                <div class="form-help">Max idle time between requests</div></div>
        </div>

        <hr class="form-divider">
        <div class="form-section-title">${FMI.http} HTTP Options</div>
        <div class="form-row-3">
            <div><label class="toggle-wrap"><input type="checkbox" id="m-forwardfor" ${f.option_forwardfor ? "checked" : ""}> X-Forwarded-For</label>
                <div class="form-help">Add client IP header</div></div>
            <div><label class="toggle-wrap"><input type="checkbox" id="m-httplog" ${f.option_httplog ? "checked" : ""}> HTTP Log</label>
                <div class="form-help">Detailed HTTP logging</div></div>
            <div><label class="toggle-wrap"><input type="checkbox" id="m-tcplog" ${f.option_tcplog ? "checked" : ""}> TCP Log</label>
                <div class="form-help">TCP connection logging</div></div>
        </div>

        <hr class="form-divider">
        <div class="form-collapsible-head" onclick="toggleCollapsible(this)">
            ${FMI.compress} Compression & Comment ${SVG.chevron}
        </div>
        <div class="form-collapsible-body">
            <div class="form-row"><div><label>Compression Algorithms</label><input id="m-comp-algo" value="${escHtml(f.compression_algo || "")}" placeholder="gzip deflate">
                <div class="form-help">Space-separated: gzip, deflate, raw-deflate, identity</div></div>
            <div><label>Compression Types</label><input id="m-comp-type" value="${escHtml(f.compression_type || "")}" placeholder="text/html text/css application/javascript">
                <div class="form-help">Content types to compress</div></div></div>
            <label>Comment</label><input id="m-comment" value="${escHtml(f.comment || "")}" placeholder="Optional description...">
                <div class="form-help">Internal note for documentation</div>
        </div>

        <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="saveFrontend(${f.id || "null"})">Save</button></div>
    `,
        { wide: true },
    );
}

/** Saves a new or updated frontend via the API. */
export async function saveFrontend(id: number | null): Promise<void> {
    const body = {
        name: (document.getElementById("m-name") as HTMLInputElement).value,
        mode: (document.getElementById("m-mode") as HTMLSelectElement).value,
        default_backend: (document.getElementById("m-default-backend") as HTMLSelectElement).value || null,
        comment: (document.getElementById("m-comment") as HTMLInputElement).value || null,
        maxconn: parseInt((document.getElementById("m-maxconn") as HTMLInputElement).value) || null,
        timeout_client: (document.getElementById("m-timeout-client") as HTMLInputElement).value || null,
        timeout_http_request: (document.getElementById("m-timeout-http-request") as HTMLInputElement).value || null,
        timeout_http_keep_alive: (document.getElementById("m-timeout-http-keep-alive") as HTMLInputElement).value || null,
        option_forwardfor: (document.getElementById("m-forwardfor") as HTMLInputElement).checked,
        option_httplog: (document.getElementById("m-httplog") as HTMLInputElement).checked,
        option_tcplog: (document.getElementById("m-tcplog") as HTMLInputElement).checked,
        compression_algo: (document.getElementById("m-comp-algo") as HTMLInputElement).value || null,
        compression_type: (document.getElementById("m-comp-type") as HTMLInputElement).value || null,
    };
    try {
        if (id) await api(`/api/frontends/${id}`, { method: "PUT", body: JSON.stringify(body) });
        else await api("/api/frontends", { method: "POST", body: JSON.stringify(body) });
        closeModal();
        toast(id ? "Updated" : "Created");
        loadFrontends();
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Deletes a frontend after user confirmation. */
export async function deleteFrontend(id: number): Promise<void> {
    await crudDelete(`/api/frontends/${id}`, "Delete this frontend?", loadFrontends);
}

/** Preset bind line templates organised by protocol category. */
export const BIND_PRESETS: BindPreset[] = [
    { cat: "HTTP", line: "*:80", h: "HTTP on all interfaces, port 80" },
    { cat: "HTTP", line: "ipv4@*:80", h: "HTTP on all IPv4 interfaces" },
    { cat: "HTTP", line: "ipv6@:::80", h: "HTTP on all IPv6 interfaces" },
    { cat: "HTTP", line: "127.0.0.1:8080", h: "Localhost only, port 8080" },
    { cat: "HTTP", line: "*:8080", h: "Alternative HTTP port 8080" },
    { cat: "HTTPS", line: "*:443 ssl crt /etc/ssl/cert.pem", h: "HTTPS with SSL certificate" },
    { cat: "HTTPS", line: "*:443 ssl crt /etc/ssl/cert.pem alpn h2,http/1.1", h: "HTTPS with HTTP/2 and ALPN" },
    { cat: "HTTPS", line: "*:443 strict-sni ssl crt /etc/ssl/certs alpn h2,http/1.1", h: "HTTPS with strict SNI + HTTP/2" },
    { cat: "HTTPS", line: "ipv4@*:443 strict-sni ssl crt /etc/nethostssl alpn h2,http/1.1", h: "HTTPS IPv4 strict SNI + ALPN" },
    { cat: "HTTPS", line: "ipv6@:::443 ssl crt /etc/ssl/cert.pem", h: "HTTPS on IPv6 with SSL" },
    { cat: "HTTPS", line: "*:8443 ssl crt /etc/ssl/cert.pem alpn h2,http/1.1", h: "Alt HTTPS port 8443 with HTTP/2" },
    { cat: "Multi", line: "ipv4@*:80,ipv6@:::80", h: "HTTP dual-stack (IPv4 + IPv6)" },
    { cat: "Multi", line: "ipv4@*:443,ipv6@:::443 ssl crt /etc/ssl/cert.pem alpn h2,http/1.1", h: "HTTPS dual-stack with HTTP/2" },
    { cat: "Multi", line: "ipv4@*:80,ipv4@*:8080", h: "HTTP on ports 80 + 8080" },
    { cat: "TCP", line: "*:3306", h: "MySQL default port" },
    { cat: "TCP", line: "*:5432", h: "PostgreSQL default port" },
    { cat: "TCP", line: "*:6379", h: "Redis default port" },
    { cat: "TCP", line: "*:1883", h: "MQTT default port" },
    { cat: "Advanced", line: "unix@/var/run/haproxy.sock", h: "Unix domain socket" },
    { cat: "Advanced", line: "fd@${FD_NUM}", h: "File descriptor (systemd socket activation)" },
    { cat: "Advanced", line: "*:443 ssl crt /etc/ssl/cert.pem ca-file /etc/ssl/ca.pem verify required", h: "mTLS with client certificate verification" },
    { cat: "Advanced", line: "*:443 ssl crt /etc/ssl/cert.pem ssl-min-ver TLSv1.2 ciphers ECDHE+AESGCM:!SHA1", h: "HTTPS with TLS 1.2+ and strong ciphers" },
];

/** Opens the bind create/edit modal with optional preset template grid. */
export function openBindModal(frontendId: number, existing: Partial<FrontendBind> | null = null): void {
    const b = existing || {};
    const cats = [...new Set(BIND_PRESETS.map((p) => p.cat))];

    const BMI = {
        templates: icon("grid", 15),
        bind: icon("monitor", 15),
        opts: icon("settings", 15),
    };

    const presetsHtml = !b.id
        ? `
        <div class="form-section-title">${BMI.templates} Templates <span class="stab-count">${BIND_PRESETS.length}</span></div>
        <div class="stabs" style="margin-bottom:.5rem">
            <button class="stab active" onclick="filterBindPresets('all')">All</button>
            ${cats.map((c) => `<button class="stab" onclick="filterBindPresets('${c}')">${c}</button>`).join("")}
        </div>
        <div class="preset-search-wrap">
            ${icon("search")}
            <input id="bind-preset-filter" placeholder="Search templates..." oninput="filterBindPresetSearch()">
        </div>
        <div class="dir-grid" id="bind-presets-grid">
            ${BIND_PRESETS.map(
            (p) => `
                <div class="dir-card" data-bcat="${escHtml(p.cat)}" data-search-text="${escHtml((p.line + " " + p.h).toLowerCase())}"
                     onclick="document.getElementById('m-bind-line').value='${escHtml(p.line).replace(/'/g, "\\'")}'">
                    <div class="dir-card-name">${escHtml(p.line)}</div>
                    <div class="dir-card-desc">${escHtml(p.h)}</div>
                </div>`,
        ).join("")}
        </div>
        <hr class="form-divider">`
        : "";

    openModal(
        `
        <h3>${b.id ? "Edit" : "New"} Bind</h3>
        <p class="modal-subtitle">Define a listen address and port for incoming connections, with optional SSL and protocol settings.</p>
        ${presetsHtml}
        <div class="form-section-title">${BMI.bind} Bind Configuration</div>
        <label>Bind Line</label>
        <input id="m-bind-line" value="${escHtml(b.bind_line || "")}" placeholder="*:80 or *:443 ssl crt /etc/ssl/cert.pem">
        <div class="form-help">Full HAProxy bind directive. Use commas to bind multiple addresses: <code>ipv4@*:80,ipv6@:::80</code></div>

        <hr class="form-divider">
        <div class="form-collapsible-head" onclick="toggleCollapsible(this)">
            ${BMI.opts} Options ${SVG.chevron}
        </div>
        <div class="form-collapsible-body">
            <label>Sort Order</label>
            <input type="number" id="m-sort" value="${b.sort_order || 0}">
            <div class="form-help">Lower numbers appear first in the config</div>
        </div>

        <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="saveBind(${frontendId},${b.id || "null"})">Save</button></div>
    `,
        { wide: !b.id },
    );
}

/** Filters the bind preset template grid by protocol category. */
export function filterBindPresets(cat: string): void {
    filterPresetGrid("bind-presets-grid", "bind-preset-filter", "bcat", cat);
}

/** Filters bind preset templates by free-text search. */
export function filterBindPresetSearch(): void {
    searchPresetGrid("bind-presets-grid", "bind-preset-filter", "bcat");
}

/** Saves a new or updated bind to a frontend. */
export async function saveBind(frontendId: number, bindId: number | null): Promise<void> {
    const body = {
        bind_line: (document.getElementById("m-bind-line") as HTMLInputElement).value,
        sort_order: parseInt((document.getElementById("m-sort") as HTMLInputElement).value) || 0,
    };
    try {
        if (bindId) await api(`/api/frontends/${frontendId}/binds/${bindId}`, { method: "PUT", body: JSON.stringify(body) });
        else await api(`/api/frontends/${frontendId}/binds`, { method: "POST", body: JSON.stringify(body) });
        closeModal();
        toast("Saved");
        loadFrontends();
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Deletes a bind from a frontend after confirmation. */
export async function deleteBind(frontendId: number, bindId: number): Promise<void> {
    await crudDelete(`/api/frontends/${frontendId}/binds/${bindId}`, "Delete this bind?", loadFrontends);
}

/** Preset frontend option/directive templates organised by functional category. */
export const FRONTEND_OPTIONS: FrontendOptionPreset[] = [
    { c: "Logging", d: "option httplog", v: "", h: "Enable detailed HTTP request logging" },
    { c: "Logging", d: "option dontlognull", v: "", h: "Don't log connections with no data" },
    { c: "Logging", d: "option logasap", v: "", h: "Log as soon as possible (before response)" },
    { c: "Logging", d: "option tcplog", v: "", h: "Enable TCP connection logging" },
    { c: "Logging", d: "log global", v: "", h: "Use global log configuration" },
    { c: "Logging", d: "log", v: "127.0.0.1:514 local0", h: "Custom syslog target" },
    { c: "HTTP", d: "option forwardfor", v: "except 127.0.0.0/8", h: "Add X-Forwarded-For header" },
    { c: "HTTP", d: "option http-server-close", v: "", h: "Close server connection after response" },
    { c: "HTTP", d: "option http-keep-alive", v: "", h: "Enable HTTP keep-alive" },
    { c: "HTTP", d: "option httpclose", v: "", h: "Force close HTTP connections" },
    { c: "HTTP", d: "http-request set-header", v: "X-Forwarded-Proto https if { ssl_fc }", h: "Pass SSL protocol info to backend" },
    { c: "HTTP", d: "http-request set-header", v: "X-Real-IP %[src]", h: "Forward client's real IP to backend" },
    { c: "HTTP", d: "http-request set-header", v: "X-Forwarded-For %[src]", h: "Add client IP to forwarded header" },
    { c: "HTTP", d: "http-response set-header", v: "Strict-Transport-Security max-age=31536000", h: "HSTS - force HTTPS for 1 year" },
    { c: "HTTP", d: "http-response set-header", v: "X-Content-Type-Options nosniff", h: "Prevent MIME-type sniffing" },
    { c: "HTTP", d: "http-response set-header", v: "X-Frame-Options DENY", h: "Block clickjacking via iframes" },
    { c: "HTTP", d: "http-response set-header", v: "Content-Security-Policy default-src 'self'", h: "Restrict resource loading to same origin" },
    { c: "HTTP", d: "http-response set-header", v: "Referrer-Policy strict-origin-when-cross-origin", h: "Control Referer header in requests" },
    { c: "HTTP", d: "http-response del-header", v: "Server", h: "Remove backend server header" },
    { c: "HTTP", d: "http-response del-header", v: "X-Powered-By", h: "Remove technology disclosure header" },
    { c: "HTTP", d: "compression algo", v: "gzip", h: "Enable gzip compression" },
    { c: "HTTP", d: "compression type", v: "text/html text/plain text/css application/json application/javascript", h: "Content types to compress" },
    { c: "Security", d: "http-request redirect", v: "scheme https unless { ssl_fc }", h: "Force HTTPS redirect" },
    { c: "Security", d: "http-request deny", v: "if { src -f /etc/haproxy/blocked.acl }", h: "Block IPs from blacklist file" },
    { c: "Security", d: "http-request deny", v: "unless { src -f /etc/haproxy/allowed.acl }", h: "Allow only whitelisted IPs" },
    { c: "Security", d: "http-request deny", v: "if { path_beg /admin } !{ src 10.0.0.0/8 }", h: "Restrict admin path to internal IPs" },
    { c: "Security", d: "http-request tarpit", v: "if { src_http_req_rate gt 100 }", h: "Slow down high-rate sources" },
    { c: "Security", d: "rate-limit sessions", v: "100", h: "Limit new sessions per second" },
    { c: "Security", d: "stick-table", v: "type ip size 200k expire 30s store http_req_rate(10s)", h: "Track request rates per source IP" },
    { c: "Security", d: "http-request track-sc0", v: "src", h: "Track source IP in stick table" },
    { c: "Security", d: "tcp-request connection reject", v: "if { src -f /etc/haproxy/blocked.acl }", h: "TCP-level IP blacklist" },
    { c: "Security", d: "tcp-request connection accept", v: "if { src -f /etc/haproxy/allowed.acl }", h: "TCP-level IP whitelist" },
    { c: "Security", d: "http-request set-header", v: "X-Request-ID %[unique-id]", h: "Add unique request ID for tracing" },
    { c: "Security", d: "unique-id-format", v: "%{+X}o_%ci:%cp_%fi:%fp_%Ts_%rt:%pid", h: "Format for unique request IDs" },
    { c: "Routing", d: "use_backend", v: "%[req.hdr(host),lower,map_dom(/etc/haproxy/domain2backend.map)]", h: "Domain-to-backend mapping file" },
    { c: "Routing", d: "use_backend", v: "api-servers if { path_beg /api/ }", h: "Route /api/ paths to specific backend" },
    { c: "Routing", d: "use_backend", v: "ws-servers if { hdr(Upgrade) -i WebSocket }", h: "Route WebSocket connections" },
    { c: "Routing", d: "default_backend", v: "default-servers", h: "Fallback backend for unmatched requests" },
    { c: "Routing", d: "redirect prefix", v: "https://www.example.com code 301", h: "Permanent redirect to new URL" },
    { c: "Routing", d: "redirect location", v: "/ code 302 if { path /old-page }", h: "Temporary redirect for specific path" },
    { c: "Timeouts", d: "timeout client", v: "30s", h: "Max inactivity time on client side" },
    { c: "Timeouts", d: "timeout http-request", v: "10s", h: "Max time to receive complete request" },
    { c: "Timeouts", d: "timeout http-keep-alive", v: "5s", h: "Max idle time between HTTP requests" },
    { c: "Timeouts", d: "timeout tarpit", v: "60s", h: "Duration to hold tarpitted connections" },
    { c: "Timeouts", d: "timeout client-fin", v: "5s", h: "Timeout for half-closed client connections" },
    { c: "ACL", d: "acl", v: "is_ssl dst_port 443", h: "Match HTTPS connections (port 443)" },
    { c: "ACL", d: "acl", v: "host_match hdr(host) -i example.com", h: "Match specific hostname" },
    { c: "ACL", d: "acl", v: "path_api path_beg /api/", h: "Match API path prefix" },
    { c: "ACL", d: "acl", v: "is_websocket hdr(Upgrade) -i WebSocket", h: "Match WebSocket upgrade requests" },
    { c: "ACL", d: "acl", v: "src_local src 127.0.0.0/8 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16", h: "Match private/local source IPs" },
    { c: "ACL", d: "acl", v: "is_options method OPTIONS", h: "Match CORS preflight requests" },
    { c: "Performance", d: "maxconn", v: "5000", h: "Moderate connection limit" },
    { c: "Performance", d: "maxconn", v: "50000", h: "High connection limit" },
    { c: "Performance", d: "backlog", v: "10000", h: "TCP backlog queue size" },
    { c: "Performance", d: "option splice-auto", v: "", h: "Zero-copy data forwarding (Linux)" },
    { c: "Performance", d: "option nolinger", v: "", h: "Reset connections immediately on close" },
    { c: "IP Access", d: "tcp-request connection reject", v: "if { src -f /etc/haproxy/blacklist.acl }", h: "Reject connections from blacklisted IPs" },
    { c: "IP Access", d: "tcp-request connection accept", v: "if { src -f /etc/haproxy/whitelist.acl }", h: "Accept only whitelisted IPs" },
    { c: "IP Access", d: "http-request deny", v: "if { src -f /etc/haproxy/blacklist.acl }", h: "HTTP deny from blacklisted IPs" },
    { c: "IP Access", d: "http-request deny", v: "unless { src 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16 }", h: "Allow only private IP ranges" },
    { c: "IP Access", d: "acl", v: "blocked_ips src -f /etc/haproxy/blacklist.acl", h: "Define blacklist ACL from file" },
    { c: "IP Access", d: "acl", v: "allowed_ips src -f /etc/haproxy/whitelist.acl", h: "Define whitelist ACL from file" },
];

/** Opens the option create/edit modal with preset template grid for new options. */
export function openOptionModal(frontendId: number, existing: Partial<FrontendOption> | null = null): void {
    const o = existing || {};
    const optCats = [...new Set(FRONTEND_OPTIONS.map((p) => p.c))];

    const OMI = {
        templates: icon("grid", 15),
        directive: icon("code", 15),
        opts: icon("settings", 15),
    };

    const presetsHtml = !o.id
        ? `
        <div class="form-section-title">${OMI.templates} Templates <span class="stab-count">${FRONTEND_OPTIONS.length}</span></div>
        <div class="stabs" style="margin-bottom:.6rem">
            <button class="stab active" onclick="filterOptPresets('all')">All</button>
            ${optCats.map((c) => `<button class="stab" onclick="filterOptPresets('${c}')">${c}</button>`).join("")}
        </div>
        <div class="preset-search-wrap" style="margin-bottom:.75rem">
            ${icon("search")}
            <input id="opt-preset-filter" placeholder="Search templates..." oninput="filterOptPresetSearch()">
        </div>
        <div class="dir-grid" id="opt-presets-grid">
            ${FRONTEND_OPTIONS.map(
            (p, i) => `
                <div class="dir-card" data-ocat="${escHtml(p.c)}" data-search-text="${escHtml((p.d + " " + p.v + " " + p.h).toLowerCase())}"
                     onclick="applyOptPreset(${i})">
                    <div class="dir-card-name">${escHtml(p.d)}</div>
                    ${p.v ? `<div class="dir-card-val">${escHtml(p.v)}</div>` : ""}
                    <div class="dir-card-desc">${escHtml(p.h)}</div>
                </div>`,
        ).join("")}
        </div>
        <hr class="form-divider">`
        : "";

    openModal(
        `
        <h3>${o.id ? "Edit" : "New"} Frontend Option</h3>
        <p class="modal-subtitle">Add an HAProxy directive for request processing, security, routing, or performance tuning.</p>
        ${presetsHtml}
        <div class="form-section-title">${OMI.directive} Directive Details</div>
        <div class="form-row"><div><label>Directive</label>
            <input id="m-directive" value="${escHtml(o.directive || "")}" placeholder="e.g. option, http-request, timeout">
            <div class="form-help">HAProxy directive keyword (e.g. "option", "http-request set-header")</div></div>
        <div><label>Value</label>
            <input id="m-value" value="${escHtml(o.value || "")}" placeholder="e.g. httplog, set-header X-Forwarded-Proto https">
            <div class="form-help">Directive parameter or value</div></div></div>

        <hr class="form-divider">
        <div class="form-collapsible-head" onclick="toggleCollapsible(this)">
            ${OMI.opts} Options ${SVG.chevron}
        </div>
        <div class="form-collapsible-body">
            <div class="form-row"><div><label>Comment</label>
                <input id="m-comment" value="${escHtml(o.comment || "")}" placeholder="Optional description">
                <div class="form-help">Internal note for documentation</div></div>
            <div><label>Sort Order</label>
                <input type="number" id="m-sort" value="${o.sort_order || 0}">
                <div class="form-help">Lower numbers appear first in the config</div></div></div>
        </div>

        <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="saveOption(${frontendId},${o.id || "null"})">Save</button></div>
    `,
        { wide: !o.id },
    );
}

/** Fills the option form with values from a selected preset template. */
export function applyOptPreset(idx: number): void {
    const p = FRONTEND_OPTIONS[idx];
    if (!p) return;
    const d = document.getElementById("m-directive") as HTMLInputElement;
    if (d) d.value = p.d;
    const v = document.getElementById("m-value") as HTMLInputElement;
    if (v) v.value = p.v;
    const c = document.getElementById("m-comment") as HTMLInputElement;
    if (c) c.value = p.h;
    if (d) d.scrollIntoView({ behavior: "smooth", block: "center" });
}

/** Filters the option preset grid by category tab. */
export function filterOptPresets(cat: string): void {
    filterPresetGrid("opt-presets-grid", "opt-preset-filter", "ocat", cat);
}

/** Filters option preset templates by free-text search. */
export function filterOptPresetSearch(): void {
    searchPresetGrid("opt-presets-grid", "opt-preset-filter", "ocat");
}

/** Saves a new or updated option to a frontend. */
export async function saveOption(frontendId: number, optionId: number | null): Promise<void> {
    const body = {
        directive: (document.getElementById("m-directive") as HTMLInputElement).value,
        value: (document.getElementById("m-value") as HTMLInputElement).value,
        comment: (document.getElementById("m-comment") as HTMLInputElement).value || null,
        sort_order: parseInt((document.getElementById("m-sort") as HTMLInputElement).value) || 0,
    };
    try {
        if (optionId) await api(`/api/frontends/${frontendId}/options/${optionId}`, { method: "PUT", body: JSON.stringify(body) });
        else await api(`/api/frontends/${frontendId}/options`, { method: "POST", body: JSON.stringify(body) });
        closeModal();
        toast("Saved");
        loadFrontends();
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Deletes a frontend option after confirmation. */
export async function deleteOption(frontendId: number, optionId: number): Promise<void> {
    await crudDelete(`/api/frontends/${frontendId}/options/${optionId}`, "Delete this option?", loadFrontends);
}
