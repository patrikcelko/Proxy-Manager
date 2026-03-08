/**
 * Backends section
 * ================
 *
 * Manages HAProxy backend definitions with server pools,
 * load balancing, health checks, session persistence,
 * authentication, compression, and advanced options.
 */

import { api, toast } from "../core/api";
import { icon, SVG } from "../core/icons";
import { openModal, closeModal } from "../core/ui";
import { escHtml, escJsonAttr, safeInt, crudDelete } from "../core/utils";
import { state } from "../state";
import type { Backend, BackendServer } from "../types";

/** Current filter query for backends search. */
let backendFilter = "";

/** Fetches all backends from the API and renders the card grid. */
export async function loadBackends(): Promise<void> {
    try {
        const d: { items: Backend[] } = await api("/api/backends");
        state.allBackends = d.items || d;
        renderBackends(state.allBackends);
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Filters the backends grid by search query across name, mode, balance, comment, and auth userlist. */
export function filterBackends(): void {
    backendFilter = ((document.getElementById("backend-search") as HTMLInputElement).value || "").toLowerCase();
    renderBackends(
        state.allBackends.filter((b) => {
            const hay = [b.name, b.mode, b.balance, b.comment, b.auth_userlist].filter(Boolean).join(" ").toLowerCase();
            return hay.includes(backendFilter);
        }),
    );
}

/** Renders backend cards with feature badges, detail grids, and server sub-cards. */
export function renderBackends(list: Backend[]): void {
    const grid = document.getElementById("backends-grid") as HTMLElement;
    const empty = document.getElementById("backends-empty") as HTMLElement;
    if (!list.length) {
        grid.innerHTML = "";
        grid.style.display = "none";
        empty.style.display = "block";
        return;
    }
    grid.style.display = "grid";
    grid.style.gridTemplateColumns = "repeat(auto-fill,minmax(420px,1fr))";
    empty.style.display = "none";

    const IC: Record<string, string> = {
        mode: icon("globe-simple", 11, 2.5),
        balance: icon("balance", 11, 2.5),
        lock: icon("lock", 11, 2.5),
        fwd: icon("arrow-right", 11, 2.5),
        retry: icon("refresh", 11, 2.5),
        heart: icon("activity", 11, 2.5),
        cookie: icon("cookie", 11, 2.5),
        reuse: icon("repeat", 11, 2.5),
        compress: icon("cloud-download", 11, 2.5),
        err: icon("x-circle", 11, 2.5),
        stick: icon("briefcase", 11, 2.5),
        log: icon("file-text", 11, 2.5),
        redispatch: icon("redispatch", 11, 2.5),
        timeout: icon("clock", 11, 2.5),
        server: icon("server", 11, 2.5),
    };

    grid.innerHTML = list
        .map((b) => {
            const sc = (b.servers || []).length;
            const mode = b.mode || "http";
            const servers = (b.servers || [])
                .map((s) => {
                    const statusClass = s.check_enabled ? "srv-status-ok" : "srv-status-default";
                    return `<div class="be-srv-card">
                <div class="be-srv-indicator ${statusClass}"></div>
                <div class="be-srv-body">
                    <div class="be-srv-name">${escHtml(s.name)}</div>
                    <div class="be-srv-addr">${escHtml(s.address)}:${s.port}</div>
                </div>
                <div class="be-srv-badges">
                    ${s.check_enabled ? '<span class="badge badge-ok">check</span>' : ""}
                    ${s.ssl_enabled ? '<span class="badge badge-info">ssl</span>' : ""}
                    ${s.backup ? '<span class="badge badge-warn">backup</span>' : ""}
                    ${s.weight != null ? `<span class="badge badge-muted">w:${s.weight}</span>` : ""}
                    ${s.maxconn ? `<span class="badge badge-muted">mc:${s.maxconn}</span>` : ""}
                    ${s.disabled ? '<span class="badge badge-danger">disabled</span>' : ""}
                </div>
                <div class="be-srv-actions">
                    <button class="btn-icon" onclick='openServerModal(${b.id},${escJsonAttr(s)})'>${SVG.editSm}</button>
                    <button class="btn-icon danger" onclick="deleteServer(${b.id},${s.id})">${SVG.delSm}</button>
                </div>
            </div>`;
                })
                .join("");

            const features: string[] = [];
            features.push(`<span class="be-feat be-feat-mode">${IC.mode} ${escHtml(mode.toUpperCase())}</span>`);
            features.push(`<span class="be-feat be-feat-balance">${IC.balance} ${escHtml(b.balance || "roundrobin")}</span>`);
            if (b.auth_userlist) features.push(`<span class="be-feat be-feat-auth">${IC.lock} ${escHtml(b.auth_userlist)}</span>`);
            if (b.option_forwardfor) features.push(`<span class="be-feat be-feat-fwd">${IC.fwd} X-Fwd-For</span>`);
            if (b.option_redispatch) features.push(`<span class="be-feat be-feat-ha">${IC.redispatch} Redispatch</span>`);
            if (b.option_httplog) features.push(`<span class="be-feat be-feat-fwd">${IC.log} HTTP Log</span>`);
            if (b.option_tcplog) features.push(`<span class="be-feat be-feat-fwd">${IC.log} TCP Log</span>`);
            if (b.retries) features.push(`<span class="be-feat be-feat-retry">${IC.retry} Retries: ${b.retries}</span>`);
            if (b.health_check_enabled) features.push(`<span class="be-feat be-feat-health">${IC.heart} Health${b.health_check_method ? " (" + escHtml(b.health_check_method) + ")" : ""}</span>`);
            if (b.cookie) features.push(`<span class="be-feat be-feat-cookie">${IC.cookie} Cookie</span>`);
            if (b.http_reuse) features.push(`<span class="be-feat be-feat-ha">${IC.reuse} Reuse: ${escHtml(b.http_reuse)}</span>`);
            if (b.compression_algo) features.push(`<span class="be-feat be-feat-fwd">${IC.compress} Compress</span>`);
            if (b.errorfile) features.push(`<span class="be-feat be-feat-err">${IC.err} Error Files</span>`);
            if (b.extra_options) {
                const eo = b.extra_options.toLowerCase();
                if (/stick-table/.test(eo)) features.push(`<span class="be-feat be-feat-stick">${IC.stick} Stick Table</span>`);
            }

            const detailRows: [string, string, string][] = [];
            if (b.timeout_server) detailRows.push(["timeout", "Server Timeout", b.timeout_server]);
            if (b.timeout_connect) detailRows.push(["timeout", "Connect Timeout", b.timeout_connect]);
            if (b.timeout_queue) detailRows.push(["timeout", "Queue Timeout", b.timeout_queue]);
            if (b.health_check_uri) detailRows.push(["heart", "Health URI", b.health_check_uri]);
            if (b.health_check_method) detailRows.push(["heart", "HC Method", b.health_check_method]);
            if (b.http_check_expect) detailRows.push(["heart", "HC Expect", b.http_check_expect]);
            if (b.cookie) detailRows.push(["cookie", "Cookie", b.cookie]);
            if (b.hash_type) detailRows.push(["balance", "Hash Type", b.hash_type]);
            if (b.retry_on) detailRows.push(["retry", "Retry On", b.retry_on]);
            if (b.default_server_options) detailRows.push(["server", "Default Server", b.default_server_options]);
            if (b.compression_algo) detailRows.push(["compress", "Compression", b.compression_algo]);
            if (b.compression_type) detailRows.push(["compress", "Compress Type", b.compression_type]);
            if (b.errorfile) detailRows.push(["err", "Error File", b.errorfile]);

            const detailHtml = detailRows.length
                ? `<div class="be-detail-section">
            <div class="be-detail-grid">${detailRows.map(([ic, l, v]) => `<div class="be-detail-item"><span class="be-detail-icon">${IC[ic] || ""}</span><span class="be-detail-label">${escHtml(l)}</span><span class="be-detail-value">${escHtml(v)}</span></div>`).join("")}</div>
        </div>`
                : "";

            return `<div class="item-card be-card" data-entity-name="${escHtml(b.name)}">
            <div class="item-header"><h3>${escHtml(b.name)}</h3>
                <div><button class="btn-icon" onclick='openBackendModal(${escJsonAttr(b)})'>${SVG.edit}</button>
                <button class="btn-icon danger" onclick="deleteBackend(${b.id})">${SVG.del}</button></div>
            </div>
            <div class="be-features">${features.join("")}</div>
            ${detailHtml}
            <div class="be-servers-section">
                <div class="be-servers-head"><span>${IC.server} Servers <span class="be-srv-count">${sc}</span></span>
                    <button class="btn-icon" onclick="openServerModal(${b.id})">${SVG.plus}</button></div>
                <div class="be-servers-grid">${servers || '<div class="be-srv-empty">' + icon("server", 16, 1.5) + " No servers configured</div>"}</div>
            </div>
            ${b.extra_options ? '<div class="be-custom-opts"><span class="be-custom-label">Extra Options</span><span class="mono">' + escHtml(b.extra_options).substring(0, 300) + "</span></div>" : ""}
            ${b.comment ? `<div class="be-custom-opts"><span class="be-custom-label">Comment</span><span>${escHtml(b.comment)}</span></div>` : ""}
        </div>`;
        })
        .join("");
}

/** Opens the backend create/edit modal with timeouts, health checks, auth, options, persistence, and advanced settings. */
export function openBackendModal(existing: Partial<Backend> | null = null): void {
    const b = existing || {};
    const ulOpts = (state.cachedUserlists || [])
        .map((u) => `<option value="${escHtml(u.name)}" ${b.auth_userlist === u.name ? "selected" : ""}>${escHtml(u.name)}</option>`)
        .join("");
    if (!state.cachedUserlists) {
        api("/api/userlists")
            .then((d: any) => {
                state.cachedUserlists = d.items || d;
                const sel = document.getElementById("m-auth-userlist") as HTMLSelectElement | null;
                if (sel) {
                    const current = sel.value;
                    const opts = state
                        .cachedUserlists!.map(
                            (u) => `<option value="${escHtml(u.name)}" ${current === u.name || b.auth_userlist === u.name ? "selected" : ""}>${escHtml(u.name)}</option>`,
                        )
                        .join("");
                    sel.innerHTML = '<option value="">None (no auth)</option>' + opts;
                }
            })
            .catch(() => { });
    }

    const SEC = {
        core: icon("settings", 15),
        timeout: icon("clock", 15),
        auth: icon("shield", 15),
        health: icon("activity", 15),
        cookie: icon("cookie", 15),
        opts: icon("terminal", 15),
        advanced: icon("edit-pen", 15),
    };

    openModal(
        `
        <h3>${b.id ? "Edit" : "New"} Backend</h3>
        <p class="modal-subtitle">Configure an upstream server pool with load balancing and health checking.</p>

        <div class="form-row"><div><label>Name</label><input id="m-name" value="${escHtml(b.name || "")}" placeholder="my-backend">
            <div class="form-help">Unique identifier for this backend</div></div>
        <div><label>Mode</label><select id="m-mode"><option value="http" ${b.mode === "http" || !b.mode ? "selected" : ""}>HTTP</option>
            <option value="tcp" ${b.mode === "tcp" ? "selected" : ""}>TCP</option></select>
            <div class="form-help">Protocol mode (Layer 7 HTTP or Layer 4 TCP)</div></div></div>
        <div class="form-row"><div><label>Balance Algorithm</label><select id="m-balance">
            ${["roundrobin", "leastconn", "source", "uri", "first", "hdr", "random", "rdp-cookie"].map((v) => `<option ${b.balance === v ? "selected" : ""}>${v}</option>`).join("")}
            </select>
            <div class="form-help">Load balancing strategy across servers</div></div>
        <div><label>Comment</label><input id="m-comment" value="${escHtml(b.comment || "")}" placeholder="Optional description...">
            <div class="form-help">Internal note for documentation</div></div></div>

        <hr class="form-divider">
        <div class="form-section-title">${SEC.timeout} Timeouts</div>
        <div class="form-row-3">
            <div><label>Server Timeout</label><input id="m-timeout-server" value="${escHtml(b.timeout_server || "")}" placeholder="30s">
                <div class="form-help">Max inactivity on server side</div></div>
            <div><label>Connect Timeout</label><input id="m-timeout-connect" value="${escHtml(b.timeout_connect || "")}" placeholder="5s">
                <div class="form-help">Max time to connect to server</div></div>
            <div><label>Queue Timeout</label><input id="m-timeout-queue" value="${escHtml(b.timeout_queue || "")}" placeholder="30s">
                <div class="form-help">Max time in queue waiting for slot</div></div>
        </div>

        <hr class="form-divider">
        <div class="form-section-title">${SEC.health} Health Checks</div>
        <div class="form-row"><div>
            <label class="toggle-wrap" style="margin-top:.5rem">
                <input type="checkbox" id="m-hc-enabled" ${b.health_check_enabled ? "checked" : ""}>
                Enable Health Checks
            </label>
        </div><div><label>Method</label><select id="m-hc-method">
            <option value="" ${!b.health_check_method ? "selected" : ""}>Default</option>
            <option value="GET" ${b.health_check_method === "GET" ? "selected" : ""}>GET</option>
            <option value="HEAD" ${b.health_check_method === "HEAD" ? "selected" : ""}>HEAD</option>
            <option value="OPTIONS" ${b.health_check_method === "OPTIONS" ? "selected" : ""}>OPTIONS</option>
        </select></div></div>
        <div class="form-row"><div><label>Health Check URI</label><input id="m-hc-uri" value="${escHtml(b.health_check_uri || "")}" placeholder="/health or /status">
            <div class="form-help">URI path for HTTP health check requests</div></div>
        <div><label>HTTP Check Expect</label><input id="m-hc-expect" value="${escHtml(b.http_check_expect || "")}" placeholder="status 200">
            <div class="form-help">Expected response (e.g. status 200, string OK)</div></div></div>

        <div class="form-collapsible" style="margin-top:1rem">
            <div class="form-collapsible-head" onclick="toggleCollapsible(this)">${SEC.auth} Authentication &amp; Security ${SVG.chevron}</div>
            <div class="form-collapsible-body">
                <div class="form-row"><div>
                    <label>Auth User List</label>
                    <select id="m-auth-userlist"><option value="">None (no auth)</option>${ulOpts}</select>
                    <div class="form-help">Reference an Auth List for HTTP Basic Auth on this backend</div>
                </div><div>
                    <label>&nbsp;</label>
                    <div class="form-help" style="margin-top:.5rem">Create auth lists in the <em>Auth Lists</em> section, then select here to protect this backend.</div>
                </div></div>
            </div>
        </div>

        <div class="form-collapsible" style="margin-top:.5rem">
            <div class="form-collapsible-head" onclick="toggleCollapsible(this)">${SEC.opts} Options &amp; Behavior ${SVG.chevron}</div>
            <div class="form-collapsible-body">
                <div class="form-row"><div>
                    <label class="toggle-wrap" style="margin-top:.5rem">
                        <input type="checkbox" id="m-forwardfor" ${b.option_forwardfor ? "checked" : ""}>
                        X-Forwarded-For
                    </label>
                    <div class="form-help">Pass client IP to backend via header</div>
                </div><div>
                    <label class="toggle-wrap" style="margin-top:.5rem">
                        <input type="checkbox" id="m-redispatch" ${b.option_redispatch ? "checked" : ""}>
                        Redispatch
                    </label>
                    <div class="form-help">Retry on different server on connection failure</div>
                </div></div>
                <div class="form-row"><div>
                    <label class="toggle-wrap" style="margin-top:.5rem">
                        <input type="checkbox" id="m-httplog" ${b.option_httplog ? "checked" : ""}>
                        HTTP Log
                    </label>
                    <div class="form-help">Enable detailed HTTP request logging</div>
                </div><div>
                    <label class="toggle-wrap" style="margin-top:.5rem">
                        <input type="checkbox" id="m-tcplog" ${b.option_tcplog ? "checked" : ""}>
                        TCP Log
                    </label>
                    <div class="form-help">Enable TCP connection logging</div>
                </div></div>
                <div class="form-row"><div><label>Retries</label><input type="number" id="m-retries" value="${b.retries || ""}" placeholder="3" min="0" max="100">
                    <div class="form-help">Number of retries on connection failures</div></div>
                <div><label>Retry On</label><input id="m-retry-on" value="${escHtml(b.retry_on || "")}" placeholder="all-retryable-errors">
                    <div class="form-help">Conditions triggering retry</div></div></div>
                <div class="form-row"><div><label>HTTP Reuse</label><select id="m-http-reuse">
                    <option value="" ${!b.http_reuse ? "selected" : ""}>Default</option>
                    <option value="safe" ${b.http_reuse === "safe" ? "selected" : ""}>safe</option>
                    <option value="aggressive" ${b.http_reuse === "aggressive" ? "selected" : ""}>aggressive</option>
                    <option value="always" ${b.http_reuse === "always" ? "selected" : ""}>always</option>
                    <option value="never" ${b.http_reuse === "never" ? "selected" : ""}>never</option>
                </select><div class="form-help">HTTP connection reuse strategy</div></div>
                <div><label>Hash Type</label><input id="m-hash-type" value="${escHtml(b.hash_type || "")}" placeholder="consistent sdbm">
                    <div class="form-help">Hash-type for balance (e.g. consistent, map-based)</div></div></div>
            </div>
        </div>

        <div class="form-collapsible" style="margin-top:.5rem">
            <div class="form-collapsible-head" onclick="toggleCollapsible(this)">${SEC.cookie} Session Persistence ${SVG.chevron}</div>
            <div class="form-collapsible-body">
                <div class="form-row"><div>
                    <label>Cookie</label><input id="m-cookie" value="${escHtml(b.cookie || "")}" placeholder="SERVERID insert indirect nocache">
                    <div class="form-help">Cookie persistence (e.g. SRVID insert indirect nocache)</div>
                </div></div>
            </div>
        </div>

        <div class="form-collapsible" style="margin-top:.5rem">
            <div class="form-collapsible-head" onclick="toggleCollapsible(this)">${SEC.advanced} Advanced Options ${SVG.chevron}</div>
            <div class="form-collapsible-body">
                <div class="form-row"><div><label>Compression Algorithms</label><input id="m-comp-algo" value="${escHtml(b.compression_algo || "")}" placeholder="gzip deflate">
                    <div class="form-help">Space-separated: gzip, deflate, raw-deflate</div></div>
                <div><label>Compression Types</label><input id="m-comp-type" value="${escHtml(b.compression_type || "")}" placeholder="text/html text/css application/javascript">
                    <div class="form-help">Content types to compress</div></div></div>
                <label>Default Server Options</label><input id="m-default-server" value="${escHtml(b.default_server_options || "")}" placeholder="inter 3s fall 3 rise 2 maxconn 256">
                <div class="form-help">Shared params for all servers (default-server directive)</div>
                <label>Error File Config</label><input id="m-errorfile" value="${escHtml(b.errorfile || "")}" placeholder="503 /etc/haproxy/errors/503.http">
                <div class="form-help">Custom error file paths</div>
                <label>Extra Options</label><textarea id="m-extra" rows="3" placeholder="stick-table type ip size 200k&#10;http-request set-header X-Custom value">${escHtml(b.extra_options || "")}</textarea>
                <div class="form-help">Additional HAProxy directives, one per line</div>
            </div>
        </div>

        <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="saveBackend(${b.id || "null"})">Save</button></div>
    `,
        { wide: true },
    );
}

/** Saves a new or updated backend with all configuration fields via the API. */
export async function saveBackend(id: number | null): Promise<void> {
    const body = {
        name: (document.getElementById("m-name") as HTMLInputElement).value,
        mode: (document.getElementById("m-mode") as HTMLSelectElement).value,
        balance: (document.getElementById("m-balance") as HTMLSelectElement).value,
        option_forwardfor: (document.getElementById("m-forwardfor") as HTMLInputElement).checked,
        option_redispatch: (document.getElementById("m-redispatch") as HTMLInputElement).checked,
        option_httplog: (document.getElementById("m-httplog") as HTMLInputElement).checked,
        option_tcplog: (document.getElementById("m-tcplog") as HTMLInputElement).checked,
        retries: parseInt((document.getElementById("m-retries") as HTMLInputElement).value) || null,
        retry_on: (document.getElementById("m-retry-on") as HTMLInputElement).value || null,
        auth_userlist: (document.getElementById("m-auth-userlist") as HTMLSelectElement).value || null,
        health_check_enabled: (document.getElementById("m-hc-enabled") as HTMLInputElement).checked,
        health_check_method: (document.getElementById("m-hc-method") as HTMLSelectElement).value || null,
        health_check_uri: (document.getElementById("m-hc-uri") as HTMLInputElement).value || null,
        http_check_expect: (document.getElementById("m-hc-expect") as HTMLInputElement).value || null,
        errorfile: (document.getElementById("m-errorfile") as HTMLInputElement).value || null,
        comment: (document.getElementById("m-comment") as HTMLInputElement).value || null,
        extra_options: (document.getElementById("m-extra") as HTMLTextAreaElement).value || null,
        timeout_server: (document.getElementById("m-timeout-server") as HTMLInputElement).value || null,
        timeout_connect: (document.getElementById("m-timeout-connect") as HTMLInputElement).value || null,
        timeout_queue: (document.getElementById("m-timeout-queue") as HTMLInputElement).value || null,
        cookie: (document.getElementById("m-cookie") as HTMLInputElement).value || null,
        http_reuse: (document.getElementById("m-http-reuse") as HTMLSelectElement).value || null,
        hash_type: (document.getElementById("m-hash-type") as HTMLInputElement).value || null,
        compression_algo: (document.getElementById("m-comp-algo") as HTMLInputElement).value || null,
        compression_type: (document.getElementById("m-comp-type") as HTMLInputElement).value || null,
        default_server_options: (document.getElementById("m-default-server") as HTMLInputElement).value || null,
    };
    try {
        if (id) await api(`/api/backends/${id}`, { method: "PUT", body: JSON.stringify(body) });
        else await api("/api/backends", { method: "POST", body: JSON.stringify(body) });
        closeModal();
        toast(id ? "Updated" : "Created");
        loadBackends();
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Deletes a backend and all its servers after confirmation. */
export async function deleteBackend(id: number): Promise<void> {
    await crudDelete(`/api/backends/${id}`, "Delete this backend and all its servers?", loadBackends);
}

/** Opens the server create/edit modal with connection, health check, SSL, and advanced settings. */
export function openServerModal(backendId: number, existing: Partial<BackendServer> | null = null): void {
    const s = existing || {};
    const SI = {
        server: icon("server", 15),
        conn: icon("bar-chart", 15),
        health: icon("activity", 15),
        ssl: icon("lock", 15),
        advanced: icon("edit-pen", 15),
    };
    openModal(
        `
        <h3>${s.id ? "Edit" : "New"} Server</h3>
        <p class="modal-subtitle">Configure an individual upstream server within this backend pool.</p>

        <div class="form-row"><div><label>Name</label><input id="m-name" value="${escHtml(s.name || "")}" placeholder="web-srv-01">
            <div class="form-help">Unique server identifier within this backend</div></div>
        <div><label>Address</label><input id="m-address" value="${escHtml(s.address || "")}" placeholder="10.0.0.1 or hostname">
            <div class="form-help">IP address or resolvable hostname</div></div></div>
        <div class="form-row-3"><div><label>Port</label><input type="number" id="m-port" value="${s.port || 80}" min="1" max="65535">
            <div class="form-help">Listening port (1-65535)</div></div>
        <div><label>Weight</label><input type="number" id="m-weight" value="${s.weight != null ? s.weight : ""}" placeholder="100" min="0" max="256">
            <div class="form-help">Load balance weight (0-256)</div></div>
        <div><label>Sort Order</label><input type="number" id="m-sort" value="${s.sort_order || 0}">
            <div class="form-help">Display ordering</div></div></div>

        <hr class="form-divider">
        <div class="form-section-title">${SI.conn} Connection</div>
        <div class="form-row-3"><div><label>Max Connections</label><input type="number" id="m-maxconn" value="${s.maxconn || ""}" placeholder="256">
            <div class="form-help">Concurrent connection limit</div></div>
        <div><label>Max Queue</label><input type="number" id="m-maxqueue" value="${s.maxqueue || ""}" placeholder="0">
            <div class="form-help">Max pending connections in queue</div></div>
        <div><label>Slowstart</label><input id="m-slowstart" value="${escHtml(s.slowstart || "")}" placeholder="60s">
            <div class="form-help">Ramp-up time after recovery</div></div></div>

        <hr class="form-divider">
        <div class="form-section-title">${SI.health} Health Check</div>
        <div class="form-row"><div>
            <label class="toggle-wrap" style="margin-top:.5rem">
                <input type="checkbox" id="m-check" ${s.check_enabled ? "checked" : ""}>
                Enable Health Check
            </label>
            <div class="form-help">Periodically verify server availability</div>
        </div><div>
            <label class="toggle-wrap" style="margin-top:.5rem">
                <input type="checkbox" id="m-backup" ${s.backup ? "checked" : ""}>
                Backup Server
            </label>
            <div class="form-help">Only used when all primary servers are down</div>
        </div></div>
        <div class="form-row-3"><div><label>Inter</label><input id="m-inter" value="${escHtml(s.inter || "")}" placeholder="3s">
            <div class="form-help">Check interval</div></div>
        <div><label>Rise</label><input type="number" id="m-rise" value="${s.rise != null ? s.rise : ""}" placeholder="2">
            <div class="form-help">Checks to mark UP</div></div>
        <div><label>Fall</label><input type="number" id="m-fall" value="${s.fall != null ? s.fall : ""}" placeholder="3">
            <div class="form-help">Checks to mark DOWN</div></div></div>

        <div class="form-collapsible" style="margin-top:1rem">
            <div class="form-collapsible-head" onclick="toggleCollapsible(this)">${SI.ssl} SSL &amp; Proxy Protocol ${SVG.chevron}</div>
            <div class="form-collapsible-body">
                <div class="form-row"><div>
                    <label class="toggle-wrap" style="margin-top:.5rem">
                        <input type="checkbox" id="m-ssl" ${s.ssl_enabled ? "checked" : ""}>
                        SSL
                    </label>
                    <div class="form-help">Enable SSL to backend server</div>
                </div><div><label>SSL Verify</label><select id="m-ssl-verify">
                    <option value="" ${!s.ssl_verify ? "selected" : ""}>Default</option>
                    <option value="none" ${s.ssl_verify === "none" ? "selected" : ""}>none</option>
                    <option value="required" ${s.ssl_verify === "required" ? "selected" : ""}>required</option>
                </select></div></div>
                <div class="form-row"><div>
                    <label class="toggle-wrap" style="margin-top:.5rem">
                        <input type="checkbox" id="m-send-proxy" ${s.send_proxy ? "checked" : ""}>
                        Send PROXY v1
                    </label>
                    <div class="form-help">Pass client info via PROXY protocol v1</div>
                </div><div>
                    <label class="toggle-wrap" style="margin-top:.5rem">
                        <input type="checkbox" id="m-send-proxy-v2" ${s.send_proxy_v2 ? "checked" : ""}>
                        Send PROXY v2
                    </label>
                    <div class="form-help">Pass client info via PROXY protocol v2 (binary)</div>
                </div></div>
            </div>
        </div>

        <div class="form-collapsible" style="margin-top:.5rem">
            <div class="form-collapsible-head" onclick="toggleCollapsible(this)">${SI.advanced} Advanced Options ${SVG.chevron}</div>
            <div class="form-collapsible-body">
                <div class="form-row"><div><label>Cookie Value</label><input id="m-cookie-value" value="${escHtml(s.cookie_value || "")}" placeholder="server1">
                    <div class="form-help">Cookie value for session persistence</div></div>
                <div><label>On Marked Down</label><select id="m-on-marked-down">
                    <option value="" ${!s.on_marked_down ? "selected" : ""}>Default</option>
                    <option value="shutdown-sessions" ${s.on_marked_down === "shutdown-sessions" ? "selected" : ""}>shutdown-sessions</option>
                </select>
                <div class="form-help">Action when server marked down</div></div></div>
                <div class="form-row"><div><label>Fastinter</label><input id="m-fastinter" value="${escHtml(s.fastinter || "")}" placeholder="1s">
                    <div class="form-help">Fast check interval on transitions</div></div>
                <div><label>Downinter</label><input id="m-downinter" value="${escHtml(s.downinter || "")}" placeholder="5s">
                    <div class="form-help">Check interval when DOWN</div></div></div>
                <div class="form-row"><div><label>Resolvers</label><input id="m-resolvers" value="${escHtml(s.resolvers_ref || "")}" placeholder="mydns">
                    <div class="form-help">DNS resolver name</div></div>
                <div><label>Resolve Prefer</label><select id="m-resolve-prefer">
                    <option value="" ${!s.resolve_prefer ? "selected" : ""}>Default</option>
                    <option value="ipv4" ${s.resolve_prefer === "ipv4" ? "selected" : ""}>ipv4</option>
                    <option value="ipv6" ${s.resolve_prefer === "ipv6" ? "selected" : ""}>ipv6</option>
                </select>
                <div class="form-help">Preferred IP version for DNS</div></div></div>
                <label class="toggle-wrap" style="margin-top:.5rem">
                    <input type="checkbox" id="m-disabled" ${s.disabled ? "checked" : ""}>
                    Disabled
                </label>
                <div class="form-help">Disable this server (maintenance mode)</div>
                <label>Extra Parameters</label><input id="m-params" value="${escHtml(s.extra_params || "")}" placeholder="Additional params...">
                <div class="form-help">Any extra server-line parameters not covered above</div>
            </div>
        </div>

        <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="saveServer(${backendId},${s.id || "null"})">Save</button></div>
    `,
        { wide: true },
    );
}

/** Saves a new or updated server with all configuration fields. */
export async function saveServer(backendId: number, serverId: number | null): Promise<void> {
    const body = {
        name: (document.getElementById("m-name") as HTMLInputElement).value,
        address: (document.getElementById("m-address") as HTMLInputElement).value,
        port: safeInt((document.getElementById("m-port") as HTMLInputElement).value),
        check_enabled: (document.getElementById("m-check") as HTMLInputElement).checked,
        maxconn: parseInt((document.getElementById("m-maxconn") as HTMLInputElement).value) || null,
        maxqueue: parseInt((document.getElementById("m-maxqueue") as HTMLInputElement).value) || null,
        extra_params: (document.getElementById("m-params") as HTMLInputElement).value || null,
        sort_order: parseInt((document.getElementById("m-sort") as HTMLInputElement).value) || 0,
        weight: parseInt((document.getElementById("m-weight") as HTMLInputElement).value) || null,
        ssl_enabled: (document.getElementById("m-ssl") as HTMLInputElement).checked,
        ssl_verify: (document.getElementById("m-ssl-verify") as HTMLSelectElement).value || null,
        backup: (document.getElementById("m-backup") as HTMLInputElement).checked,
        inter: (document.getElementById("m-inter") as HTMLInputElement).value || null,
        fastinter: (document.getElementById("m-fastinter") as HTMLInputElement).value || null,
        downinter: (document.getElementById("m-downinter") as HTMLInputElement).value || null,
        rise: parseInt((document.getElementById("m-rise") as HTMLInputElement).value) || null,
        fall: parseInt((document.getElementById("m-fall") as HTMLInputElement).value) || null,
        cookie_value: (document.getElementById("m-cookie-value") as HTMLInputElement).value || null,
        send_proxy: (document.getElementById("m-send-proxy") as HTMLInputElement).checked,
        send_proxy_v2: (document.getElementById("m-send-proxy-v2") as HTMLInputElement).checked,
        slowstart: (document.getElementById("m-slowstart") as HTMLInputElement).value || null,
        resolve_prefer: (document.getElementById("m-resolve-prefer") as HTMLSelectElement).value || null,
        resolvers_ref: (document.getElementById("m-resolvers") as HTMLInputElement).value || null,
        on_marked_down: (document.getElementById("m-on-marked-down") as HTMLSelectElement).value || null,
        disabled: (document.getElementById("m-disabled") as HTMLInputElement).checked,
    };
    try {
        if (serverId) await api(`/api/backends/${backendId}/servers/${serverId}`, { method: "PUT", body: JSON.stringify(body) });
        else await api(`/api/backends/${backendId}/servers`, { method: "POST", body: JSON.stringify(body) });
        closeModal();
        toast("Saved");
        loadBackends();
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Deletes a server from a backend after confirmation. */
export async function deleteServer(backendId: number, serverId: number): Promise<void> {
    await crudDelete(`/api/backends/${backendId}/servers/${serverId}`, "Delete this server?", loadBackends);
}
