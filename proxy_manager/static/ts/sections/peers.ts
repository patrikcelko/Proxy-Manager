/**
 * Peers section
 * =============
 *
 * Manages HAProxy peer sections for stick-table replication
 * and state synchronization between HAProxy instances.
 */

import { api, toast } from "../core/api";
import { icon, SVG } from "../core/icons";
import { openModal, closeModal } from "../core/ui";
import { escHtml, escJsonAttr, crudDelete } from "../core/utils";
import { state } from "../state";
import type { Peer, PeerEntry } from "../types";

/** Renders peer section cards with peer entries and feature badges. */
function renderPeersGrid(items: Peer[]): void {
    const grid = document.getElementById("peers-grid") as HTMLElement;
    const empty = document.getElementById("peers-empty") as HTMLElement;
    if (!items.length) {
        grid.innerHTML = "";
        grid.style.display = "none";
        empty.style.display = "block";
        return;
    }
    grid.style.display = "grid";
    grid.style.gridTemplateColumns = "repeat(auto-fill,minmax(380px,1fr))";
    empty.style.display = "none";

    const PIC = {
        cluster: icon("cluster", 11, 2.5),
        peer: icon("server", 11, 2.5),
        network: icon("arrow-right", 11, 2.5),
    };

    grid.innerHTML = items
        .map((p) => {
            const entries = p.entries || [];
            const features: string[] = [];
            features.push(`<span class="pe-feat pe-feat-cluster">${PIC.cluster} Peer Section</span>`);
            features.push(`<span class="pe-feat pe-feat-count">${PIC.peer} ${entries.length} Peer${entries.length !== 1 ? "s" : ""}</span>`);
            if (p.default_bind) features.push(`<span class="pe-feat pe-feat-extra">${PIC.network} Bind</span>`);
            if (p.default_server_options) features.push(`<span class="pe-feat pe-feat-extra">${PIC.network} Default Server</span>`);
            if (p.extra_options) features.push(`<span class="pe-feat pe-feat-extra">${PIC.network} Extra Opts</span>`);

            const entryCards = entries
                .map(
                    (e) =>
                        `<div class="pe-entry-card">
                    <div class="pe-entry-dot"></div>
                    <div class="pe-entry-body">
                        <div class="pe-entry-name">${escHtml(e.name)}</div>
                        <div class="pe-entry-addr">${escHtml(e.address)}:${e.port}</div>
                    </div>
                    <div class="pe-entry-actions">
                        <button class="btn-icon" onclick='openPeerEntryModal(${p.id},${escJsonAttr(e)})'>${SVG.editSm}</button>
                        <button class="btn-icon danger" onclick="deletePeerEntry(${p.id},${e.id})">${SVG.delSm}</button>
                    </div>
                </div>`,
                )
                .join("");

            return `<div class="item-card pe-card">
                <div class="item-header"><h3>${escHtml(p.name)}</h3>
                    <div><button class="btn-icon" onclick='openPeerModal(${escJsonAttr(p)})'>${SVG.edit}</button>
                    <button class="btn-icon danger" onclick="deletePeer(${p.id})">${SVG.del}</button></div>
                </div>
                <div class="pe-features">${features.join("")}</div>
                ${p.comment ? `<div class="pe-custom-opts"><span class="pe-custom-label">Comment</span><span>${escHtml(p.comment)}</span></div>` : ""}
                ${p.default_bind ? `<div class="pe-custom-opts"><span class="pe-custom-label">Bind</span><span class="mono">${escHtml(p.default_bind)}</span></div>` : ""}
                ${p.default_server_options ? `<div class="pe-custom-opts"><span class="pe-custom-label">Default Server</span><span class="mono">${escHtml(p.default_server_options)}</span></div>` : ""}
                <div class="pe-entries-section">
                    <div class="pe-entries-head"><span>${PIC.peer} Peer Entries <span class="pe-entry-count">${entries.length}</span></span>
                        <button class="btn-icon" onclick="openPeerEntryModal(${p.id})">${SVG.plus}</button></div>
                    <div class="pe-entries-grid">${entryCards || `<div class="pe-entry-empty">${PIC.peer} No peer entries configured</div>`}</div>
                </div>
                ${p.extra_options ? `<div class="pe-custom-opts"><span class="pe-custom-label">Extra Options</span><span class="mono">${escHtml(p.extra_options).substring(0, 300)}</span></div>` : ""}
            </div>`;
        })
        .join("");
}

/** Fetches all peer sections from the API and renders cards. */
export async function loadPeers(): Promise<void> {
    try {
        const d = await api("/api/peers");
        state.allPeers = d.items || d;
        renderPeersGrid(state.allPeers);
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Filters peer sections by name, comment, or entry name/address. */
export function filterPeers(): void {
    const q = ((document.getElementById("peer-search") as HTMLInputElement).value || "").toLowerCase();
    if (!q) {
        renderPeersGrid(state.allPeers);
        return;
    }
    renderPeersGrid(
        state.allPeers.filter(
            (p) =>
                p.name.toLowerCase().includes(q) ||
                (p.comment || "").toLowerCase().includes(q) ||
                (p.entries || []).some((e) => (e.name || "").toLowerCase().includes(q) || (e.address || "").toLowerCase().includes(q)),
        ),
    );
}

/** Opens peer section create/edit modal with identification, connection defaults, and advanced options. */
export function openPeerModal(existing: Partial<Peer> | null = null): void {
    const p = existing || {};
    const SEC = {
        core: icon("cluster", 15),
        network: icon("arrow-right", 15),
        opts: icon("terminal", 15),
    };
    openModal(
        `
        <h3>${p.id ? "Edit" : "New"} Peer Section</h3>
        <p class="modal-subtitle">Configure a peers section for stick-table replication and state synchronization between HAProxy instances.</p>

        <div class="form-section-title">${SEC.core} Identification</div>
        <div class="form-row"><div>
            <label>Section Name</label><input id="m-name" value="${escHtml(p.name || "")}" placeholder="mypeers">
            <div class="form-help">Unique name referenced by stick-table peers directives</div>
        </div><div>
            <label>Comment</label><input id="m-comment" value="${escHtml(p.comment || "")}" placeholder="Optional description...">
            <div class="form-help">Internal note for documentation purposes</div>
        </div></div>

        <hr class="form-divider">
        <div class="form-section-title">${SEC.network} Connection Defaults</div>
        <div class="form-row"><div>
            <label>Default Bind</label><input id="m-default-bind" value="${escHtml(p.default_bind || "")}" placeholder=":10000 ssl crt /etc/ssl/cert.pem">
            <div class="form-help">Bind address for incoming peer connections (HAProxy 2.6+)</div>
        </div><div>
            <label>Default Server Options</label><input id="m-default-server" value="${escHtml(p.default_server_options || "")}" placeholder="ssl verify none">
            <div class="form-help">Default-server parameters applied to all peer entries</div>
        </div></div>

        <div class="form-collapsible" style="margin-top:1rem">
            <div class="form-collapsible-head" onclick="toggleCollapsible(this)">${SEC.opts} Advanced Options ${SVG.chevron}</div>
            <div class="form-collapsible-body">
                <label>Extra Options</label>
                <textarea id="m-extra" rows="4" placeholder="stick-table type ip size 200k expire 30m&#10;log global">${escHtml(p.extra_options || "")}</textarea>
                <div class="form-help">Additional HAProxy directives for this peers section, one per line (e.g. stick-table, log)</div>
            </div>
        </div>

        <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="savePeer(${p.id || "null"})">${p.id ? "Update" : "Create"} Peer Section</button></div>
    `,
        { wide: true },
    );
}

/** Opens peer entry create/edit modal with name, address, port, and sort order. */
export function openPeerEntryModal(peerId: number, existing: Partial<PeerEntry> | null = null): void {
    const e = existing || {};
    const SEC = {
        server: icon("server", 15),
        network: icon("arrow-right", 15),
    };
    openModal(
        `
        <h3>${e.id ? "Edit" : "New"} Peer Entry</h3>
        <p class="modal-subtitle">Define a remote HAProxy peer node for stick-table synchronization.</p>

        <div class="form-section-title">${SEC.server} Peer Node</div>
        <div class="form-row"><div>
            <label>Peer Name</label><input id="m-name" value="${escHtml(e.name || "")}" placeholder="haproxy1">
            <div class="form-help">Hostname or identifier for this peer node</div>
        </div><div>
            <label>Sort Order</label><input type="number" id="m-sort" value="${e.sort_order || 0}" min="0">
            <div class="form-help">Display/config order (lower = first)</div>
        </div></div>

        <hr class="form-divider">
        <div class="form-section-title">${SEC.network} Network</div>
        <div class="form-row"><div>
            <label>IP Address / Hostname</label><input id="m-address" value="${escHtml(e.address || "")}" placeholder="10.0.0.1 or peer1.example.com">
            <div class="form-help">IPv4, IPv6, or DNS hostname of the peer</div>
        </div><div>
            <label>Port</label><input type="number" id="m-port" value="${e.port || 10000}" min="1" max="65535">
            <div class="form-help">TCP port for peer protocol (default: 10000)</div>
        </div></div>

        <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="savePeerEntry(${peerId},${e.id || "null"})">${e.id ? "Update" : "Add"} Peer Entry</button></div>
    `,
        { wide: true },
    );
}

/** Saves a new or updated peer section with name, comment, bind, and server options. */
export async function savePeer(id: number | null): Promise<void> {
    const body = {
        name: (document.getElementById("m-name") as HTMLInputElement).value,
        comment: (document.getElementById("m-comment") as HTMLInputElement).value || null,
        default_bind: (document.getElementById("m-default-bind") as HTMLInputElement).value || null,
        default_server_options: (document.getElementById("m-default-server") as HTMLInputElement).value || null,
        extra_options: (document.getElementById("m-extra") as HTMLTextAreaElement).value || null,
    };
    try {
        if (id) await api(`/api/peers/${id}`, { method: "PUT", body: JSON.stringify(body) });
        else await api("/api/peers", { method: "POST", body: JSON.stringify(body) });
        closeModal();
        toast(id ? "Updated" : "Created");
        loadPeers();
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Deletes a peer section after confirmation. */
export async function deletePeer(id: number): Promise<void> {
    await crudDelete(`/api/peers/${id}`, "Delete this peer section?", loadPeers);
}

/** Saves a new or updated peer entry with name, address, port, and sort order. */
export async function savePeerEntry(peerId: number, entryId: number | null): Promise<void> {
    const body = {
        name: (document.getElementById("m-name") as HTMLInputElement).value,
        address: (document.getElementById("m-address") as HTMLInputElement).value,
        port: parseInt((document.getElementById("m-port") as HTMLInputElement).value) || 10000,
        sort_order: parseInt((document.getElementById("m-sort") as HTMLInputElement).value) || 0,
    };
    try {
        if (entryId) await api(`/api/peers/${peerId}/entries/${entryId}`, { method: "PUT", body: JSON.stringify(body) });
        else await api(`/api/peers/${peerId}/entries`, { method: "POST", body: JSON.stringify(body) });
        closeModal();
        toast("Saved");
        loadPeers();
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Deletes a peer entry after confirmation. */
export async function deletePeerEntry(peerId: number, entryId: number): Promise<void> {
    await crudDelete(`/api/peers/${peerId}/entries/${entryId}`, "Delete this peer entry?", loadPeers);
}
