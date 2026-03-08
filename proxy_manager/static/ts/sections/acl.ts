/**
 * ACL Rules section
 * =================
 *
 * Manages HAProxy ACL routing rules that match incoming
 * requests by domain, path, header, or source IP and route
 * them to backends or redirect to URLs.
 */

import { api, toast } from "../core/api";
import { icon, SVG } from "../core/icons";
import { openModal, closeModal } from "../core/ui";
import { escHtml, escJsonAttr, safeInt, crudDelete } from "../core/utils";
import { state } from "../state";
import type { AclRule } from "../types";

/** Current filter query for ACL table search. */
let aclFilter = "";

/** Fetches all ACL rules from the API and renders the table. */
export async function loadAclRules(): Promise<void> {
    try {
        const d: { items: AclRule[] } = await api("/api/acl-rules");
        state.allAclRules = d.items || d;
        renderAclTable(state.allAclRules);
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Filters ACL rules by search query across domain, backend, redirect, match type, comment, and frontend name. */
export function filterAclTable(): void {
    aclFilter = ((document.getElementById("acl-search") as HTMLInputElement).value || "").toLowerCase();
    renderAclTable(
        state.allAclRules.filter(
            (a) =>
                a.domain.toLowerCase().includes(aclFilter) ||
                (a.backend_name || "").toLowerCase().includes(aclFilter) ||
                (a.redirect_target || "").toLowerCase().includes(aclFilter) ||
                (a.acl_match_type || "").toLowerCase().includes(aclFilter) ||
                (a.comment || "").toLowerCase().includes(aclFilter) ||
                (state.allFrontends.find((f) => f.id === a.frontend_id)?.name || "").toLowerCase().includes(aclFilter),
        ),
    );
}

/** Renders the ACL rules as a sortable table with domain links, action pills, match badges, and reorder controls. */
export function renderAclTable(list: AclRule[]): void {
    const tbody = document.querySelector("#acl-table tbody") as HTMLElement;
    const empty = document.getElementById("acl-empty") as HTMLElement;
    const wrap = (document.querySelector("#acl-table") as HTMLElement).parentElement!;
    if (!list.length) {
        wrap.style.display = "none";
        empty.style.display = "block";
        return;
    }
    wrap.style.display = "block";
    empty.style.display = "none";

    list.sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0));

    tbody.innerHTML = list
        .map((a, idx) => {
            const feLabel = state.allFrontends.find((f) => f.id === a.frontend_id)?.name || "-";
            const isFirst = idx === 0;
            const isLast = idx === list.length - 1;

            const domainDisplay = /^[a-zA-Z0-9._-]+\.[a-zA-Z]{2,}$/.test(a.domain)
                ? `<a href="https://${escHtml(a.domain)}" target="_blank" rel="noopener" class="acl-domain-link">${escHtml(a.domain)}</a>`
                : `<span class="mono">${escHtml(a.domain)}</span>`;

            const actionDisplay = a.is_redirect
                ? `<span class="acl-redirect-pill">${icon("chevron-right", 12)}<span class="acl-redir-code">${a.redirect_code || 301}</span><span class="acl-redir-url">${escHtml(a.redirect_target || "")}</span></span>`
                : `<span class="badge badge-muted">${escHtml(a.backend_name || "-")}</span>`;

            const matchIcons: Record<string, string> = {
                hdr: "header",
                hdr_beg: "header",
                hdr_end: "header",
                hdr_reg: "header",
                hdr_dom: "domain",
                path: "path",
                path_beg: "path",
                path_end: "path",
                path_reg: "path",
                src: "ip",
                url_beg: "url",
                url_reg: "url",
            };
            const matchType = a.acl_match_type || "hdr";
            const matchCat = matchIcons[matchType] || "header";
            const matchBadgeClass = matchCat === "domain" ? "badge-info" : matchCat === "path" ? "badge-warn" : "badge-muted";

            return `<tr class="acl-row" data-id="${a.id}" data-entity-name="${escHtml(feLabel)}:${escHtml(a.domain)}:${a.sort_order}">
            <td class="acl-domain-cell">${domainDisplay}</td>
            <td>${actionDisplay}</td>
            <td><span class="badge ${matchBadgeClass}">${escHtml(matchType)}</span></td>
            <td class="muted">${escHtml(feLabel)}</td>
            <td class="sett-order-cell">
                <div class="reorder-group">
                    <button class="reorder-btn${isFirst ? " disabled" : ""}" onclick="reorderAclRule(${a.id},'up')" title="Move up" ${isFirst ? "disabled" : ""}>
                        ${icon("chevron-up", 12, 2.5)}
                    </button>
                    <span class="reorder-num">${a.sort_order}</span>
                    <button class="reorder-btn${isLast ? " disabled" : ""}" onclick="reorderAclRule(${a.id},'down')" title="Move down" ${isLast ? "disabled" : ""}>
                        ${icon("chevron-down", 12, 2.5)}
                    </button>
                </div>
            </td>
            <td class="muted acl-comment-cell">${escHtml(a.comment || "")}</td>
            <td class="actions">
                <button class="btn-icon" onclick='openAclModal(${escJsonAttr(a)})'>${SVG.edit}</button>
                <button class="btn-icon danger" onclick="deleteAclRule(${a.id})">${SVG.del}</button>
            </td>
        </tr>`;
        })
        .join("");
}

/** Opens the ACL rule create/edit modal with domain/match, action (backend or redirect), and scope options. */
export function openAclModal(existing: Partial<AclRule> | null = null): void {
    const a = existing || {};
    const feOpts = state.allFrontends.map((f) => `<option value="${f.id}" ${a.frontend_id === f.id ? "selected" : ""}>${escHtml(f.name)}</option>`).join("");
    const beOpts = state.allBackends.map((b) => `<option value="${escHtml(b.name)}" ${a.backend_name === b.name ? "selected" : ""}>${escHtml(b.name)}</option>`).join("");
    const isRedir = a.is_redirect || false;

    const AI = {
        route: icon("route-arrow", 15),
        match: icon("search", 15),
        scope: icon("monitor", 15),
        action: icon("chevron-right", 15),
        opts: icon("settings", 15),
    };

    openModal(`
        <h3>${a.id ? "Edit" : "New"} ACL Rule</h3>
        <p class="modal-subtitle">Define a routing rule to match incoming requests and direct them to a backend or redirect URL.</p>

        <div class="form-section-title">${AI.route} Domain & Match</div>
        <div class="form-row"><div><label>Domain / Pattern</label><input id="m-domain" value="${escHtml(a.domain || "")}" placeholder="example.com">
            <div class="form-help">Hostname, path, or pattern to match against</div></div>
        <div><label>Match Type</label><select id="m-match">
            ${["hdr", "hdr_beg", "hdr_end", "hdr_reg", "hdr_dom", "path", "path_beg", "path_end", "path_reg", "src", "url_beg", "url_reg"].map((m) => `<option ${a.acl_match_type === m ? "selected" : ""}>${m}</option>`).join("")}
            </select>
            <div class="form-help">HAProxy ACL matching function</div></div></div>

        <hr class="form-divider">
        <div class="form-section-title">${AI.action} Action</div>
        <div class="form-row"><div><label>Action Type</label><select id="m-is-redirect" onchange="toggleAclRedirect(this.value==='true')">
            <option value="false" ${!isRedir ? "selected" : ""}>Route to Backend</option>
            <option value="true" ${isRedir ? "selected" : ""}>HTTP Redirect</option></select>
            <div class="form-help">Route traffic to a backend pool or send a redirect response</div></div>
        <div id="acl-backend-row" ${isRedir ? 'style="display:none"' : ""}>
            <label>Target Backend</label><select id="m-backend"><option value="">- Select backend -</option>${beOpts}</select>
            <div class="form-help">Backend server pool to forward matching requests to</div>
        </div></div>
        <div id="acl-redirect-row" ${!isRedir ? 'style="display:none"' : ""}>
            <div class="form-row"><div><label>Redirect URL</label><input id="m-redirect" value="${escHtml(a.redirect_target || "")}" placeholder="https://new-domain.com">
                <div class="form-help">Full URL to redirect matching requests to</div></div>
            <div><label>HTTP Code</label><select id="m-redir-code">
                ${[301, 302, 303, 307, 308].map((c) => `<option ${a.redirect_code === c ? "selected" : ""}>${c}</option>`).join("")}</select>
                <div class="form-help">301/308 permanent, 302/303/307 temporary</div></div></div>
        </div>

        <hr class="form-divider">
        <div class="form-collapsible-head" onclick="toggleCollapsible(this)">
            ${AI.opts} Scope & Options ${SVG.chevron}
        </div>
        <div class="form-collapsible-body">
            <div class="form-row"><div><label>Frontend Scope</label><select id="m-frontend"><option value="">Any (all frontends)</option>${feOpts}</select>
                <div class="form-help">Limit this rule to a specific frontend, or apply globally</div></div>
            <div><label>Status</label><select id="m-enabled"><option value="true" ${a.enabled !== false ? "selected" : ""}>Enabled</option>
                <option value="false" ${a.enabled === false ? "selected" : ""}>Disabled</option></select>
                <div class="form-help">Disabled rules are kept but not applied</div></div></div>
            <div class="form-row"><div><label>Sort Order</label><input type="number" id="m-sort" value="${a.sort_order || 0}">
                <div class="form-help">Evaluation priority (lower = first)</div></div>
            <div><label>Comment</label><input id="m-comment" value="${escHtml(a.comment || "")}" placeholder="Optional description...">
                <div class="form-help">Internal note for documentation</div></div></div>
        </div>

        <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="saveAclRule(${a.id || "null"})">Save</button></div>
    `);
}

/** Toggles visibility of backend vs redirect fields in the ACL modal. */
export function toggleAclRedirect(isRedir: boolean): void {
    (document.getElementById("acl-backend-row") as HTMLElement).style.display = isRedir ? "none" : "";
    (document.getElementById("acl-redirect-row") as HTMLElement).style.display = isRedir ? "" : "none";
}

/** Saves a new or updated ACL rule with domain, match type, action, and scope. */
export async function saveAclRule(id: number | null): Promise<void> {
    const isRedir = (document.getElementById("m-is-redirect") as HTMLSelectElement).value === "true";
    const body = {
        domain: (document.getElementById("m-domain") as HTMLInputElement).value,
        acl_match_type: (document.getElementById("m-match") as HTMLSelectElement).value,
        frontend_id: parseInt((document.getElementById("m-frontend") as HTMLSelectElement).value) || null,
        is_redirect: isRedir,
        backend_name: isRedir ? null : (document.getElementById("m-backend") as HTMLSelectElement).value,
        redirect_target: isRedir ? (document.getElementById("m-redirect") as HTMLInputElement).value : null,
        redirect_code: isRedir ? safeInt((document.getElementById("m-redir-code") as HTMLSelectElement).value) : null,
        enabled: (document.getElementById("m-enabled") as HTMLSelectElement).value === "true",
        sort_order: parseInt((document.getElementById("m-sort") as HTMLInputElement).value) || 0,
        comment: (document.getElementById("m-comment") as HTMLInputElement).value || null,
    };
    try {
        if (id) await api(`/api/acl-rules/${id}`, { method: "PUT", body: JSON.stringify(body) });
        else await api("/api/acl-rules", { method: "POST", body: JSON.stringify(body) });
        closeModal();
        toast(id ? "Updated" : "Created");
        loadAclRules();
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Deletes an ACL rule after confirmation. */
export async function deleteAclRule(id: number): Promise<void> {
    await crudDelete(`/api/acl-rules/${id}`, "Delete this ACL rule?", loadAclRules);
}

/** Swaps sort order of two adjacent ACL rules to reorder them up or down. */
export async function reorderAclRule(id: number, direction: "up" | "down"): Promise<void> {
    const sorted = [...state.allAclRules].sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0));
    const idx = sorted.findIndex((r) => r.id === id);
    if (idx < 0) return;

    const swapIdx = direction === "up" ? idx - 1 : idx + 1;
    if (swapIdx < 0 || swapIdx >= sorted.length) return;

    const current = sorted[idx];
    const swap = sorted[swapIdx];
    const curOrder = current.sort_order ?? 0;
    const swpOrder = swap.sort_order ?? 0;

    const newCurOrder = swpOrder;
    const newSwpOrder = curOrder === swpOrder ? curOrder + (direction === "up" ? 1 : -1) : curOrder;

    try {
        await Promise.all([
            api(`/api/acl-rules/${current.id}`, {
                method: "PUT",
                body: JSON.stringify({ sort_order: newCurOrder }),
            }),
            api(`/api/acl-rules/${swap.id}`, {
                method: "PUT",
                body: JSON.stringify({ sort_order: newSwpOrder }),
            }),
        ]);
        await loadAclRules();
        toast("Order updated", "info");
    } catch (err: any) {
        toast(err.message, "error");
    }
}
