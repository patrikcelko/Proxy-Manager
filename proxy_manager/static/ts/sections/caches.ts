/**
 * Caches section
 * ==============
 *
 * Manages HAProxy cache sections for storing and serving
 * frequently requested HTTP responses from memory.
 */

import { api, toast } from "../core/api";
import { icon, SVG } from "../core/icons";
import { openModal, closeModal } from "../core/ui";
import { escHtml, escJsonAttr, crudDelete } from "../core/utils";
import { state } from "../state";
import type { Cache } from "../types";

/** Renders cache section cards with detail grids showing size, TTL, and vary settings. */
function renderCachesGrid(items: Cache[]): void {
    const grid = document.getElementById("caches-grid") as HTMLElement;
    const empty = document.getElementById("caches-empty") as HTMLElement;
    if (!items.length) {
        grid.innerHTML = "";
        grid.style.display = "none";
        empty.style.display = "block";
        return;
    }
    grid.style.display = "grid";
    grid.style.gridTemplateColumns = "repeat(auto-fill,minmax(380px,1fr))";
    empty.style.display = "none";

    const CIC = {
        db: icon("database", 11, 2.5),
        box: icon("box", 11, 2.5),
        clock: icon("clock", 11, 2.5),
        layers: icon("layers", 11, 2.5),
        toggle: icon("toggle", 11, 2.5),
    };

    grid.innerHTML = items
        .map((c) => {
            const features: string[] = [];
            if (c.total_max_size) features.push(`<span class="ca-feat ca-feat-size">${CIC.db} ${c.total_max_size} MB</span>`);
            if (c.max_age) features.push(`<span class="ca-feat ca-feat-age">${CIC.clock} ${c.max_age}s TTL</span>`);
            if (c.max_object_size) features.push(`<span class="ca-feat ca-feat-obj">${CIC.box} ${c.max_object_size} bytes</span>`);
            if (c.process_vary !== null && c.process_vary !== undefined) features.push(`<span class="ca-feat ca-feat-vary">${CIC.toggle} vary ${c.process_vary ? "on" : "off"}</span>`);
            if (c.max_secondary_entries) features.push(`<span class="ca-feat ca-feat-secondary">${CIC.layers} 2nd: ${c.max_secondary_entries}</span>`);

            const details = [
                { icon: CIC.db, label: "Total Max Size", value: c.total_max_size ? `${c.total_max_size} MB` : "-" },
                { icon: CIC.box, label: "Max Object Size", value: c.max_object_size ? `${c.max_object_size} bytes` : "-" },
                { icon: CIC.clock, label: "Max Age", value: c.max_age ? `${c.max_age}s` : "-" },
                { icon: CIC.layers, label: "Secondary Entries", value: c.max_secondary_entries != null ? `${c.max_secondary_entries}` : "-" },
                { icon: CIC.toggle, label: "Process Vary", value: c.process_vary != null ? (c.process_vary ? "Enabled" : "Disabled") : "-" },
            ];

            const detailGrid = details
                .map((d) => `<div class="ca-detail-item"><span class="ca-detail-icon">${d.icon}</span><span class="ca-detail-label">${d.label}</span><span class="ca-detail-value">${d.value}</span></div>`)
                .join("");

            return `<div class="item-card ca-card">
                <div class="item-header"><h3>${escHtml(c.name)}</h3>
                    <div><button class="btn-icon" onclick='openCacheModal(${escJsonAttr(c)})'>${SVG.edit}</button>
                    <button class="btn-icon danger" onclick="deleteCache(${c.id})">${SVG.del}</button></div>
                </div>
                <div class="ca-features">${features.join("")}</div>
                ${c.comment ? `<div class="ca-custom-opts"><span class="ca-custom-label">Comment</span><span>${escHtml(c.comment)}</span></div>` : ""}
                <div class="ca-detail-section">
                    <div class="ca-detail-grid">${detailGrid}</div>
                </div>
                ${c.extra_options ? `<div class="ca-custom-opts"><span class="ca-custom-label">Extra Options</span><span class="mono">${escHtml(c.extra_options).substring(0, 300)}</span></div>` : ""}
            </div>`;
        })
        .join("");
}

/** Fetches all cache sections from the API and renders cards. */
export async function loadCaches(): Promise<void> {
    try {
        const d = await api("/api/caches");
        state.allCaches = d.items || d;
        renderCachesGrid(state.allCaches);
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Filters cache sections by name, comment, or extra options. */
export function filterCaches(): void {
    const q = ((document.getElementById("cache-search") as HTMLInputElement).value || "").toLowerCase();
    if (!q) {
        renderCachesGrid(state.allCaches);
        return;
    }
    renderCachesGrid(state.allCaches.filter((c) => c.name.toLowerCase().includes(q) || (c.comment || "").toLowerCase().includes(q) || (c.extra_options || "").toLowerCase().includes(q)));
}

/** Opens cache create/edit modal with storage limits, expiration, process_vary, and advanced options. */
export function openCacheModal(existing: Partial<Cache> | null = null): void {
    const c = existing || {};
    const SEC = {
        db: icon("database", 15),
        box: icon("box", 15),
        clock: icon("clock", 15),
        opts: icon("terminal", 15),
    };
    openModal(
        `
        <h3>${c.id ? "Edit" : "New"} Cache</h3>
        <p class="modal-subtitle">Configure an HTTP response cache to store and serve frequently requested content directly from memory.</p>

        <div class="form-section-title">${SEC.db} Identification</div>
        <div class="form-row"><div>
            <label>Cache Name</label><input id="m-name" value="${escHtml(c.name || "")}" placeholder="static-cache">
            <div class="form-help">Unique identifier for this cache section</div>
        </div><div>
            <label>Comment</label><input id="m-comment" value="${escHtml(c.comment || "")}" placeholder="Optional description...">
            <div class="form-help">Internal note for documentation purposes</div>
        </div></div>

        <hr class="form-divider">
        <div class="form-section-title">${SEC.box} Storage Limits</div>
        <div class="form-row"><div>
            <label>Total Max Size (MB)</label><input type="number" id="m-total-max-size" value="${c.total_max_size || ""}" placeholder="4" min="1">
            <div class="form-help">Maximum RAM allocated for this cache (shared across all entries)</div>
        </div><div>
            <label>Max Object Size (bytes)</label><input type="number" id="m-max-object-size" value="${c.max_object_size || ""}" placeholder="524288" min="1">
            <div class="form-help">Largest single object size to cache (default: ~256 bytes block)</div>
        </div></div>

        <hr class="form-divider">
        <div class="form-section-title">${SEC.clock} Expiration &amp; Behavior</div>
        <div class="form-row-3"><div>
            <label>Max Age (seconds)</label><input type="number" id="m-max-age" value="${c.max_age || ""}" placeholder="60" min="0">
            <div class="form-help">Max TTL for cached objects in seconds</div>
        </div><div>
            <label>Process Vary</label>
            <select id="m-process-vary">
                <option value="" ${c.process_vary == null ? "selected" : ""}>Default (off)</option>
                <option value="1" ${c.process_vary === 1 ? "selected" : ""}>Enabled - vary-aware caching</option>
                <option value="0" ${c.process_vary === 0 ? "selected" : ""}>Disabled - ignore Vary header</option>
            </select>
            <div class="form-help">Process Vary header for content negotiation</div>
        </div><div>
            <label>Max Secondary Entries</label><input type="number" id="m-max-secondary" value="${c.max_secondary_entries || ""}" placeholder="10" min="0">
            <div class="form-help">Max variants per URL when process-vary is on</div>
        </div></div>

        <div class="form-collapsible" style="margin-top:1rem">
            <div class="form-collapsible-head" onclick="toggleCollapsible(this)">${SEC.opts} Advanced Options ${SVG.chevron}</div>
            <div class="form-collapsible-body">
                <label>Extra Options</label>
                <textarea id="m-extra" rows="4" placeholder="http-request cache-use my-cache&#10;http-response cache-store my-cache">${escHtml(c.extra_options || "")}</textarea>
                <div class="form-help">Additional HAProxy directives for this cache section, one per line</div>
            </div>
        </div>

        <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="saveCache(${c.id || "null"})">${c.id ? "Update" : "Create"} Cache</button></div>
    `,
        { wide: true },
    );
}

/** Saves a new or updated cache with size limits, TTL, process_vary, and extra options. */
export async function saveCache(id: number | null): Promise<void> {
    const pvVal = (document.getElementById("m-process-vary") as HTMLSelectElement).value;
    const body = {
        name: (document.getElementById("m-name") as HTMLInputElement).value,
        total_max_size: parseInt((document.getElementById("m-total-max-size") as HTMLInputElement).value) || null,
        max_object_size: parseInt((document.getElementById("m-max-object-size") as HTMLInputElement).value) || null,
        max_age: parseInt((document.getElementById("m-max-age") as HTMLInputElement).value) || null,
        max_secondary_entries: parseInt((document.getElementById("m-max-secondary") as HTMLInputElement).value) || null,
        process_vary: pvVal !== "" ? parseInt(pvVal) : null,
        comment: (document.getElementById("m-comment") as HTMLInputElement).value || null,
        extra_options: (document.getElementById("m-extra") as HTMLTextAreaElement).value || null,
    };
    try {
        if (id) await api(`/api/caches/${id}`, { method: "PUT", body: JSON.stringify(body) });
        else await api("/api/caches", { method: "POST", body: JSON.stringify(body) });
        closeModal();
        toast(id ? "Updated" : "Created");
        loadCaches();
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Deletes a cache section after confirmation. */
export async function deleteCache(id: number): Promise<void> {
    await crudDelete(`/api/caches/${id}`, "Delete this cache section?", loadCaches);
}
