/**
 * Resolvers section
 * =================
 *
 * Manages HAProxy DNS resolver sections for dynamic server
 * name resolution and service discovery with nameserver entries.
 */

import { api, toast } from "../core/api";
import { icon, SVG } from "../core/icons";
import { openModal, closeModal } from "../core/ui";
import { escHtml, escJsonAttr, crudDelete, filterPresetGrid, searchPresetGrid } from "../core/utils";
import { state } from "../state";
import type { Resolver, Nameserver } from "../types";

/** Resolver quick-add preset definition. */
interface ResolverPreset {
    name: string;
    comment: string;
    nameservers: { name: string; address: string; port: number }[];
    resolve_retries?: number;
    timeout_resolve?: string;
    timeout_retry?: string;
    hold_valid?: string;
    cat: string;
}

/** Quick-add presets for common DNS resolver configurations. */
const RESOLVER_PRESETS: ResolverPreset[] = [
    { name: "google-dns", comment: "Google Public DNS", nameservers: [{ name: "google1", address: "8.8.8.8", port: 53 }, { name: "google2", address: "8.8.4.4", port: 53 }], resolve_retries: 3, timeout_resolve: "1s", timeout_retry: "1s", hold_valid: "10s", cat: "public" },
    { name: "google-dns-v6", comment: "Google Public DNS (IPv6)", nameservers: [{ name: "google1-v6", address: "2001:4860:4860::8888", port: 53 }, { name: "google2-v6", address: "2001:4860:4860::8844", port: 53 }], resolve_retries: 3, timeout_resolve: "1s", timeout_retry: "1s", hold_valid: "10s", cat: "public" },
    { name: "cloudflare-dns", comment: "Cloudflare 1.1.1.1 DNS", nameservers: [{ name: "cf-primary", address: "1.1.1.1", port: 53 }, { name: "cf-secondary", address: "1.0.0.1", port: 53 }], resolve_retries: 3, timeout_resolve: "1s", timeout_retry: "1s", hold_valid: "10s", cat: "public" },
    { name: "cloudflare-dns-v6", comment: "Cloudflare DNS (IPv6)", nameservers: [{ name: "cf-primary-v6", address: "2606:4700:4700::1111", port: 53 }, { name: "cf-secondary-v6", address: "2606:4700:4700::1001", port: 53 }], resolve_retries: 3, timeout_resolve: "1s", timeout_retry: "1s", hold_valid: "10s", cat: "public" },
    { name: "quad9-dns", comment: "Quad9 DNS with security filtering", nameservers: [{ name: "quad9-primary", address: "9.9.9.9", port: 53 }, { name: "quad9-secondary", address: "149.112.112.112", port: 53 }], resolve_retries: 3, timeout_resolve: "1s", timeout_retry: "1s", hold_valid: "10s", cat: "public" },
    { name: "opendns", comment: "Cisco OpenDNS", nameservers: [{ name: "opendns1", address: "208.67.222.222", port: 53 }, { name: "opendns2", address: "208.67.220.220", port: 53 }], resolve_retries: 3, timeout_resolve: "1s", timeout_retry: "1s", hold_valid: "10s", cat: "public" },
    { name: "docker-dns", comment: "Docker embedded DNS for container discovery", nameservers: [{ name: "docker-embedded", address: "127.0.0.11", port: 53 }], resolve_retries: 3, timeout_resolve: "1s", timeout_retry: "1s", hold_valid: "10s", cat: "internal" },
    { name: "k8s-coredns", comment: "Kubernetes CoreDNS for service discovery", nameservers: [{ name: "kube-dns", address: "10.96.0.10", port: 53 }], resolve_retries: 3, timeout_resolve: "1s", timeout_retry: "1s", hold_valid: "10s", cat: "internal" },
    { name: "consul-dns", comment: "HashiCorp Consul DNS interface", nameservers: [{ name: "consul", address: "127.0.0.1", port: 8600 }], resolve_retries: 3, timeout_resolve: "2s", timeout_retry: "1s", hold_valid: "5s", cat: "internal" },
    { name: "local-dns", comment: "Local network DNS server", nameservers: [{ name: "local-ns", address: "192.168.1.1", port: 53 }], resolve_retries: 3, timeout_resolve: "1s", timeout_retry: "1s", hold_valid: "30s", cat: "internal" },
    { name: "aggressive-resolver", comment: "Aggressive resolution with short hold times", nameservers: [{ name: "cf1", address: "1.1.1.1", port: 53 }, { name: "goog1", address: "8.8.8.8", port: 53 }], resolve_retries: 5, timeout_resolve: "500ms", timeout_retry: "500ms", hold_valid: "5s", cat: "advanced" },
    { name: "failover-resolver", comment: "Multi-provider DNS failover", nameservers: [{ name: "primary-cf", address: "1.1.1.1", port: 53 }, { name: "secondary-google", address: "8.8.8.8", port: 53 }, { name: "tertiary-quad9", address: "9.9.9.9", port: 53 }], resolve_retries: 3, timeout_resolve: "1s", timeout_retry: "1s", hold_valid: "10s", cat: "advanced" },
];

/** Renders resolver cards with nameserver entries, feature badges, and detail grids. */
function renderResolversGrid(items: Resolver[]): void {
    const grid = document.getElementById("resolvers-grid") as HTMLElement;
    const empty = document.getElementById("resolvers-empty") as HTMLElement;
    if (!items.length) {
        grid.innerHTML = "";
        grid.style.display = "none";
        empty.style.display = "block";
        return;
    }
    grid.style.display = "grid";
    grid.style.gridTemplateColumns = "repeat(auto-fill,minmax(380px,1fr))";
    empty.style.display = "none";

    const RIC = {
        dns: icon("globe", 12),
        ns: icon("server", 12),
        clock: icon("clock", 12),
        hold: icon("shield", 12),
        payload: icon("package", 12),
        resolv: icon("file", 12),
        dot: icon("chevron-right", 10),
    };

    grid.innerHTML = items
        .map((r) => {
            const ns = (r.nameservers || []).sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));

            const feats: string[] = [];
            feats.push(`<span class="rs-feat rs-feat-dns">${RIC.dns} DNS Resolver</span>`);
            feats.push(`<span class="rs-feat rs-feat-count">${RIC.ns} ${ns.length} nameserver${ns.length !== 1 ? "s" : ""}</span>`);
            if (r.timeout_resolve || r.timeout_retry) {
                const t = r.timeout_resolve ? `resolve: ${r.timeout_resolve}` : "";
                const t2 = r.timeout_retry ? `retry: ${r.timeout_retry}` : "";
                feats.push(`<span class="rs-feat rs-feat-timeout">${RIC.clock} ${[t, t2].filter(Boolean).join(", ")}</span>`);
            }
            const holdKeys = ["hold_valid", "hold_other", "hold_refused", "hold_timeout", "hold_obsolete", "hold_nx", "hold_aa"] as const;
            const holdCount = holdKeys.filter((h) => r[h]).length;
            if (holdCount) feats.push(`<span class="rs-feat rs-feat-hold">${RIC.hold} ${holdCount} hold timer${holdCount > 1 ? "s" : ""}</span>`);
            if (r.accepted_payload_size) feats.push(`<span class="rs-feat rs-feat-payload">${RIC.payload} payload: ${r.accepted_payload_size}</span>`);
            if (r.parse_resolv_conf) feats.push(`<span class="rs-feat rs-feat-resolv">${RIC.resolv} resolv.conf</span>`);

            const details: { l: string; v: string | number }[] = [];
            if (r.resolve_retries != null) details.push({ l: "Retries", v: r.resolve_retries });
            if (r.timeout_resolve) details.push({ l: "Timeout Resolve", v: r.timeout_resolve });
            if (r.timeout_retry) details.push({ l: "Timeout Retry", v: r.timeout_retry });
            if (r.accepted_payload_size) details.push({ l: "Payload Size", v: `${r.accepted_payload_size} bytes` });
            (["valid", "other", "refused", "timeout", "obsolete", "nx", "aa"] as const).forEach((h) => {
                const key = `hold_${h}` as keyof Resolver;
                if (r[key]) details.push({ l: `Hold ${h}`, v: r[key] as string });
            });
            if (r.parse_resolv_conf) details.push({ l: "resolv.conf", v: "Enabled" });

            const detailHtml = details.length
                ? `<div class="rs-detail-section"><div class="rs-detail-grid">${details
                    .map(
                        (d) =>
                            `<div class="rs-detail-item"><div class="rs-detail-icon">${RIC.dot}</div><span class="rs-detail-label">${d.l}</span><span class="rs-detail-value">${escHtml(String(d.v))}</span></div>`,
                    )
                    .join("")}</div></div>`
                : "";

            const nsHtml = ns.length
                ? ns
                    .map(
                        (n) =>
                            `<div class="rs-entry-card">
                    <div class="rs-entry-dot"></div>
                    <div class="rs-entry-body">
                        <div class="rs-entry-name">${escHtml(n.name)}</div>
                        <div class="rs-entry-addr">${escHtml(n.address)}<span class="rs-entry-port">:${n.port}</span></div>
                    </div>
                    <div class="rs-entry-actions">
                        <button class="btn-icon" onclick='openNameserverModal(${r.id},${escJsonAttr(n)})'>${SVG.editSm}</button>
                        <button class="btn-icon danger" onclick="deleteNameserver(${r.id},${n.id})">${SVG.delSm}</button>
                    </div>
                </div>`,
                    )
                    .join("")
                : `<div class="rs-entry-empty">${RIC.ns} No nameservers configured</div>`;

            const extraHtml = r.extra_options ? `<div class="rs-custom-opts"><span class="rs-custom-label">Extra:</span>${escHtml(r.extra_options).replace(/\n/g, "; ")}</div>` : "";

            return `<div class="item-card rs-card" data-entity-name="${escHtml(r.name)}">
                <div class="item-header"><h3>${escHtml(r.name)}</h3>
                    <div><button class="btn-icon" onclick='openResolverModal(${escJsonAttr(r)})'>${SVG.edit}</button>
                    <button class="btn-icon danger" onclick="deleteResolver(${r.id})">${SVG.del}</button></div>
                </div>
                ${r.comment ? `<p class="item-comment" style="padding:0 .65rem .25rem;margin:0;font-size:.78rem;color:var(--text-muted)">${escHtml(r.comment)}</p>` : ""}
                <div class="rs-features">${feats.join("")}</div>
                ${detailHtml}
                <div class="rs-entries-section">
                    <div class="rs-entries-head"><span>${RIC.ns} Nameservers <span class="rs-entry-count">${ns.length}</span></span>
                        <button class="btn-icon" onclick="openNameserverModal(${r.id})">${SVG.plus}</button></div>
                    <div class="rs-entries-grid">${nsHtml}</div>
                </div>
                ${extraHtml}
            </div>`;
        })
        .join("");
}

/** Fetches all resolvers from the API and renders cards. */
export async function loadResolvers(): Promise<void> {
    try {
        const d: { items: Resolver[] } = await api("/api/resolvers");
        state.allResolvers = d.items || d;
        renderResolversGrid(state.allResolvers);
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Filters resolvers by name, comment, or nameserver name/address. */
export function filterResolvers(): void {
    const q = ((document.getElementById("resolver-search") as HTMLInputElement).value || "").toLowerCase();
    if (!q) {
        renderResolversGrid(state.allResolvers);
        return;
    }
    renderResolversGrid(
        state.allResolvers.filter(
            (r) =>
                r.name.toLowerCase().includes(q) ||
                (r.comment || "").toLowerCase().includes(q) ||
                (r.nameservers || []).some((n) => (n.name || "").toLowerCase().includes(q) || (n.address || "").toLowerCase().includes(q)),
        ),
    );
}

/** Opens the resolver quick-add modal with preset resolver templates.
 * @deprecated Use openResolverModal() which now includes templates for new resolvers.
 */
export function openResolverQuickAdd(): void {
    openResolverModal();
}

/** Filters the resolver preset grid by category. */
export function filterResolverPresets(cat: string): void {
    filterPresetGrid("resolverAddGrid", "resolver-preset-filter", "pcat", cat);
}

/** Filters the resolver preset grid by free-text search. */
export function searchResolverPresets(): void {
    searchPresetGrid("resolverAddGrid", "resolver-preset-filter", "pcat");
}

/** Adds a new empty nameserver row to the inline nameserver list in the create modal. */
export function addNsRow(name = "", address = "", port = 53): void {
    const list = document.getElementById("m-ns-list");
    if (!list) return;
    const idx = list.querySelectorAll(".ns-inline-row").length;
    const row = document.createElement("div");
    row.className = "ns-inline-row";
    row.innerHTML = `<input class="ns-field-name" placeholder="dns${idx + 1}" value="${escHtml(name)}">
        <input class="ns-field-addr" placeholder="8.8.8.8" value="${escHtml(address)}">
        <input class="ns-field-port" type="number" placeholder="53" value="${port}" min="1" max="65535">
        <button type="button" class="btn-icon danger" onclick="this.closest('.ns-inline-row').remove()">${SVG.delSm}</button>`;
    list.appendChild(row);
}

/** Applies a resolver preset: fills the form fields with the preset values. */
export async function applyResolverPreset(idx: number): Promise<void> {
    const p = RESOLVER_PRESETS[idx];
    if (!p) return;

    const setVal = (id: string, val: string | number | null | undefined) => {
        const el = document.getElementById(id) as HTMLInputElement | null;
        if (el && val != null) el.value = String(val);
    };

    setVal("m-name", p.name);
    setVal("m-comment", p.comment);
    setVal("m-resolve-retries", p.resolve_retries);
    setVal("m-timeout-resolve", p.timeout_resolve);
    setVal("m-timeout-retry", p.timeout_retry);
    setVal("m-hold-valid", p.hold_valid);

    // Populate inline nameserver rows from preset
    const list = document.getElementById("m-ns-list");
    if (list) {
        list.innerHTML = "";
        for (const ns of p.nameservers) addNsRow(ns.name, ns.address, ns.port);
    }

    // Focus on the name field so the user sees the filled form
    const nameEl = document.getElementById("m-name") as HTMLInputElement | null;
    nameEl?.focus();
    nameEl?.scrollIntoView({ behavior: "smooth", block: "center" });
    toast(`Template "${p.name}" applied - review and save`, "info");
}

/** Opens the resolver create/edit modal with identification, resolution settings, hold timers, and advanced options.
 * When creating new, includes a preset template picker at the top for quick setup. */
export function openResolverModal(existing: Partial<Resolver> | null = null): void {
    const r = existing || {};
    const isNew = !r.id;
    const SEC = {
        core: icon("globe", 15),
        timeout: icon("clock", 15),
        hold: icon("shield", 15),
        advanced: icon("edit-pen", 15),
        templates: icon("grid", 15),
        ns: icon("server", 15),
    };

    // Build template picker for new resolvers
    let templateSection = "";
    if (isNew) {
        const cats = [...new Set(RESOLVER_PRESETS.map((p) => p.cat))];
        const gridId = "resolverAddGrid";
        templateSection = `
            <div class="form-section-title">${SEC.templates} Templates <span class="stab-count">${RESOLVER_PRESETS.length}</span></div>
            <div class="form-help" style="margin-bottom:.5rem">Choose a preset to auto-fill the form, or configure manually below.</div>
            <div class="stabs" style="margin-bottom:.5rem">
                <button class="stab active" onclick="filterResolverPresets('all')">All</button>
                ${cats.map((c) => `<button class="stab" onclick="filterResolverPresets('${c}')">${c.charAt(0).toUpperCase() + c.slice(1)}</button>`).join("")}
            </div>
            <div class="preset-search-wrap" style="margin-bottom:.75rem">
                ${icon("search")}
                <input id="resolver-preset-filter" placeholder="Search presets..." oninput="searchResolverPresets()">
            </div>
            <div class="dir-grid" id="${gridId}">${RESOLVER_PRESETS.map(
            (p, i) =>
                `<div class="dir-card" data-pcat="${escHtml(p.cat)}" data-search-text="${escHtml((p.name + " " + p.comment + " " + p.nameservers.map((n) => n.address).join(" ")).toLowerCase())}"
                     onclick="applyResolverPreset(${i})">
                    <div class="dir-card-name">${escHtml(p.name)}</div>
                    <div class="dir-card-val">${p.nameservers.map((n) => n.address + ":" + n.port).join(", ")}</div>
                    <div class="dir-card-desc">${escHtml(p.comment)}</div>
                </div>`,
        ).join("")}
            </div>
            <hr class="form-divider" style="margin:1rem 0">
            <p class="form-help" style="margin-bottom:.75rem;font-weight:500;color:var(--text-muted)">Or configure manually:</p>
        `;
    }

    openModal(
        `
        <h3>${r.id ? "Edit" : "New"} DNS Resolver</h3>
        <p class="modal-subtitle">Configure a DNS resolver section for dynamic server name resolution and service discovery.</p>

        ${templateSection}

        <div class="form-section-title">${SEC.core} Identification</div>
        <div class="form-row"><div>
            <label>Resolver Name</label><input id="m-name" value="${escHtml(r.name || "")}" placeholder="mydns">
            <div class="form-help">Unique name referenced by backend server resolvers directive</div>
        </div><div>
            <label>Comment</label><input id="m-comment" value="${escHtml(r.comment || "")}" placeholder="Optional description...">
            <div class="form-help">Internal note for documentation purposes</div>
        </div></div>

        <hr class="form-divider">
        <div class="form-section-title">${SEC.timeout} Resolution Settings</div>
        <div class="form-row-3"><div>
            <label>Resolve Retries</label><input type="number" id="m-resolve-retries" value="${r.resolve_retries != null ? r.resolve_retries : ""}" placeholder="3" min="0">
            <div class="form-help">Number of DNS query retries before giving up</div>
        </div><div>
            <label>Timeout Resolve</label><input id="m-timeout-resolve" value="${escHtml(r.timeout_resolve || "")}" placeholder="1s">
            <div class="form-help">Time to wait for DNS answer</div>
        </div><div>
            <label>Timeout Retry</label><input id="m-timeout-retry" value="${escHtml(r.timeout_retry || "")}" placeholder="1s">
            <div class="form-help">Delay between retries on failure</div>
        </div></div>

        <div class="form-row"><div>
            <label>Accepted Payload Size</label><input type="number" id="m-payload" value="${r.accepted_payload_size != null ? r.accepted_payload_size : ""}" placeholder="8192" min="512" max="65535">
            <div class="form-help">Max DNS response size in bytes (512-65535)</div>
        </div><div>
            <label class="toggle-wrap" style="margin-top:1.5rem">
                <input type="checkbox" id="m-parse-resolv-conf" ${r.parse_resolv_conf ? "checked" : ""}>
                Parse /etc/resolv.conf
            </label>
            <div class="form-help">Auto-import nameservers from system resolv.conf</div>
        </div></div>

        ${isNew ? `<hr class="form-divider">
        <div class="form-section-title">${SEC.ns} Nameservers</div>
        <p class="form-help" style="margin-bottom:.5rem">Add DNS nameserver entries for this resolver. You can also add more after creation.</p>
        <div id="m-ns-list"></div>
        <button type="button" class="btn btn-secondary" style="margin-top:.5rem;font-size:.8rem" onclick="addNsRow()">+ Add Nameserver</button>` : ""}

        <div class="form-collapsible" style="margin-top:1rem">
            <div class="form-collapsible-head" onclick="toggleCollapsible(this)">${SEC.hold} Hold Timers ${SVG.chevron}</div>
            <div class="form-collapsible-body">
                <p class="form-help" style="margin-bottom:.75rem">Duration to hold DNS resolution results in cache before re-querying. Use time suffixes (s, m, h).</p>
                <div class="form-row-3"><div>
                    <label>Hold Valid</label><input id="m-hold-valid" value="${escHtml(r.hold_valid || "")}" placeholder="10s">
                    <div class="form-help">Valid responses (NOERROR)</div>
                </div><div>
                    <label>Hold Obsolete</label><input id="m-hold-obsolete" value="${escHtml(r.hold_obsolete || "")}" placeholder="10s">
                    <div class="form-help">Expired results still usable</div>
                </div><div>
                    <label>Hold NX</label><input id="m-hold-nx" value="${escHtml(r.hold_nx || "")}" placeholder="30s">
                    <div class="form-help">NXDOMAIN results</div>
                </div></div>
                <div class="form-row-3"><div>
                    <label>Hold Timeout</label><input id="m-hold-timeout" value="${escHtml(r.hold_timeout || "")}" placeholder="30s">
                    <div class="form-help">Timeout (no answer)</div>
                </div><div>
                    <label>Hold Refused</label><input id="m-hold-refused" value="${escHtml(r.hold_refused || "")}" placeholder="30s">
                    <div class="form-help">REFUSED responses</div>
                </div><div>
                    <label>Hold Other</label><input id="m-hold-other" value="${escHtml(r.hold_other || "")}" placeholder="30s">
                    <div class="form-help">Other error types</div>
                </div></div>
                <div class="form-row"><div>
                    <label>Hold AA</label><input id="m-hold-aa" value="${escHtml(r.hold_aa || "")}" placeholder="10s">
                    <div class="form-help">Authoritative answer results</div>
                </div><div></div></div>
            </div>
        </div>

        <div class="form-collapsible" style="margin-top:.5rem">
            <div class="form-collapsible-head" onclick="toggleCollapsible(this)">${SEC.advanced} Advanced Options ${SVG.chevron}</div>
            <div class="form-collapsible-body">
                <label>Extra Options</label>
                <textarea id="m-extra" rows="4" placeholder="One directive per line">${escHtml(r.extra_options || "")}</textarea>
                <div class="form-help">Additional HAProxy directives for this resolver section (one per line)</div>
            </div>
        </div>

        <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="saveResolver(${r.id || "null"})">${r.id ? "Update" : "Create"} DNS Resolver</button></div>
    `,
        { wide: true },
    );
}

/** Opens the nameserver create/edit modal with identity and connection fields. */
export function openNameserverModal(resolverId: number, existing: Partial<Nameserver> | null = null): void {
    const n = existing || {};
    const SEC = {
        server: icon("server", 15),
        network: icon("arrow-right", 15),
    };
    openModal(
        `
        <h3>${n.id ? "Edit" : "New"} Nameserver</h3>
        <p class="modal-subtitle">Define a DNS nameserver for this resolver to query for name resolution.</p>

        <div class="form-section-title">${SEC.server} Nameserver Identity</div>
        <div class="form-row"><div>
            <label>Nameserver Name</label><input id="m-name" value="${escHtml(n.name || "")}" placeholder="dns1">
            <div class="form-help">Unique identifier for this nameserver (e.g. google-dns, cloudflare)</div>
        </div><div>
            <label>Sort Order</label><input type="number" id="m-sort" value="${n.sort_order || 0}" min="0">
            <div class="form-help">Display/config order (lower = first)</div>
        </div></div>

        <hr class="form-divider">
        <div class="form-section-title">${SEC.network} Connection</div>
        <div class="form-row"><div>
            <label>IP Address / Hostname</label><input id="m-address" value="${escHtml(n.address || "")}" placeholder="8.8.8.8 or 2001:4860:4860::8888">
            <div class="form-help">IPv4 or IPv6 address of the DNS server</div>
        </div><div>
            <label>Port</label><input type="number" id="m-port" value="${n.port || 53}" min="1" max="65535">
            <div class="form-help">DNS port (default: 53, DoT: 853)</div>
        </div></div>

        <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="saveNameserver(${resolverId},${n.id || "null"})">${n.id ? "Update" : "Add"} Nameserver</button></div>
    `,
        { wide: true },
    );
}

/** Saves a new or updated resolver with all configuration fields including hold timers. */
export async function saveResolver(id: number | null): Promise<void> {
    const prc = document.getElementById("m-parse-resolv-conf") as HTMLInputElement | null;
    const body = {
        name: (document.getElementById("m-name") as HTMLInputElement).value,
        resolve_retries: parseInt((document.getElementById("m-resolve-retries") as HTMLInputElement).value) || null,
        timeout_resolve: (document.getElementById("m-timeout-resolve") as HTMLInputElement).value || null,
        timeout_retry: (document.getElementById("m-timeout-retry") as HTMLInputElement).value || null,
        hold_valid: (document.getElementById("m-hold-valid") as HTMLInputElement).value || null,
        hold_other: (document.getElementById("m-hold-other") as HTMLInputElement).value || null,
        hold_refused: (document.getElementById("m-hold-refused") as HTMLInputElement).value || null,
        hold_timeout: (document.getElementById("m-hold-timeout") as HTMLInputElement).value || null,
        hold_obsolete: (document.getElementById("m-hold-obsolete") as HTMLInputElement).value || null,
        hold_nx: (document.getElementById("m-hold-nx") as HTMLInputElement).value || null,
        hold_aa: (document.getElementById("m-hold-aa") as HTMLInputElement).value || null,
        accepted_payload_size: parseInt((document.getElementById("m-payload") as HTMLInputElement).value) || null,
        parse_resolv_conf: prc && prc.checked ? 1 : null,
        comment: (document.getElementById("m-comment") as HTMLInputElement).value || null,
        extra_options: (document.getElementById("m-extra") as HTMLTextAreaElement).value || null,
    };
    try {
        if (id) {
            await api(`/api/resolvers/${id}`, { method: "PUT", body: JSON.stringify(body) });
        } else {
            const created: any = await api("/api/resolvers", { method: "POST", body: JSON.stringify(body) });
            // Create inline nameservers if any were added
            const rows = document.querySelectorAll("#m-ns-list .ns-inline-row");
            const resolverId = created.id;
            if (resolverId && rows.length) {
                let order = 0;
                for (const row of rows) {
                    const name = (row.querySelector(".ns-field-name") as HTMLInputElement).value.trim();
                    const address = (row.querySelector(".ns-field-addr") as HTMLInputElement).value.trim();
                    const port = parseInt((row.querySelector(".ns-field-port") as HTMLInputElement).value) || 53;
                    if (!name || !address) continue;
                    await api(`/api/resolvers/${resolverId}/nameservers`, {
                        method: "POST",
                        body: JSON.stringify({ name, address, port, sort_order: order++ }),
                    });
                }
            }
        }
        closeModal();
        toast(id ? "Updated" : "Created");
        loadResolvers();
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Deletes a resolver section after confirmation. */
export async function deleteResolver(id: number): Promise<void> {
    await crudDelete(`/api/resolvers/${id}`, "Delete this resolver?", loadResolvers);
}

/** Saves a new or updated nameserver entry within a resolver. */
export async function saveNameserver(resolverId: number, nsId: number | null): Promise<void> {
    const body = {
        name: (document.getElementById("m-name") as HTMLInputElement).value,
        address: (document.getElementById("m-address") as HTMLInputElement).value,
        port: parseInt((document.getElementById("m-port") as HTMLInputElement).value) || 53,
        sort_order: parseInt((document.getElementById("m-sort") as HTMLInputElement).value) || 0,
    };
    try {
        if (nsId) await api(`/api/resolvers/${resolverId}/nameservers/${nsId}`, { method: "PUT", body: JSON.stringify(body) });
        else await api(`/api/resolvers/${resolverId}/nameservers`, { method: "POST", body: JSON.stringify(body) });
        closeModal();
        toast("Saved");
        loadResolvers();
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Deletes a nameserver entry from a resolver after confirmation. */
export async function deleteNameserver(resolverId: number, nsId: number): Promise<void> {
    await crudDelete(`/api/resolvers/${resolverId}/nameservers/${nsId}`, "Delete this nameserver?", loadResolvers);
}
