/**
 * Version Control
 * ===============
 *
 * Handles pending-change badge updates, save/discard flows,
 * inline change indicators on entity cards/rows, section-level
 * revert, and the save-version modal with commit message input.
 */

import { api, toast } from "../core/api";
import { openModal, closeModal, switchSection } from "../core/ui";
import { state } from "../state";
import { escHtml, SECTION_LABELS } from "../core/utils";
import { renderDiffContent } from "./history";
import { switchDiffTab } from "./history";
import type { PendingChanges, SectionDiff, VersionStatus } from "../types";

/** Section key -> sidebar data-section attribute. */
const SECTION_MAP: Record<string, string> = {
    global_settings: "global",
    default_settings: "defaults",
    frontends: "frontends",
    acl_rules: "acl",
    backends: "backends",
    listen_blocks: "listen",
    userlists: "userlists",
    resolvers: "resolvers",
    peers: "peers",
    mailers: "mailers",
    http_errors: "http-errors",
    caches: "caches",
    ssl_certificates: "ssl-certificates",
};

/** Reverse map: sidebar section -> snapshot section key. */
const SIDEBAR_TO_KEY: Record<string, string> = Object.fromEntries(
    Object.entries(SECTION_MAP).map(([k, v]) => [v, k]),
);

/** Debounce timer for badge refresh. */
let _refreshTimer: ReturnType<typeof setTimeout> | null = null;

/** Check initialization status. Returns true if initialized. */
export async function checkVersionStatus(): Promise<boolean> {
    try {
        const status: VersionStatus = await api("/api/versions/status");
        state.versionStatus = status;
        _updateBadges(status.pending_counts);
        _updateSidebarActions(status.has_pending);
        return status.initialized;
    } catch {
        console.warn("Failed to check version status");
        return false; // Assume not initialized on error
    }
}

/**
 * Refresh pending change badges from the API (debounced).
 *
 * Fetches the full pending diff so that inline change markers
 * can be updated for the currently visible section.
 */
export function refreshPendingBadges(): Promise<void> {
    return new Promise((resolve) => {
        if (_refreshTimer) clearTimeout(_refreshTimer);
        _refreshTimer = setTimeout(async () => {
            _refreshTimer = null;
            try {
                const pending: PendingChanges = await api("/api/versions/pending");
                state.versionStatus = {
                    initialized: true,
                    has_pending: pending.has_pending,
                    pending_counts: pending.pending_counts,
                    current_hash: state.versionStatus?.current_hash ?? null,
                    current_message: state.versionStatus?.current_message ?? null,
                    current_user_name: state.versionStatus?.current_user_name ?? null,
                    current_created_at: state.versionStatus?.current_created_at ?? null,
                };
                state.pendingDiff = pending;
                _updateBadges(pending.pending_counts);
                _updateSidebarActions(pending.has_pending);
                applySectionChangeMarkers();
            } catch {
                /* silently fail */
            }
            resolve();
        }, 80);
    });
}

/** Open the save-version modal with commit message input. */
export function openSaveVersionModal(): void {
    const vs = state.versionStatus;
    const baseInfo = vs?.current_hash
        ? `<div class="sv-base-version">
            <svg width="14" height="14" stroke-width="2"><use href="#i-hash"/></svg>
            <span class="sv-base-label">Based on:</span>
            <span class="sv-base-hash">${escHtml(vs.current_hash.substring(0, 8))}</span>
            <span class="sv-base-msg">${escHtml(vs.current_message || "")}</span>
          </div>`
        : "";

    const html = `
    <h3>Save Version</h3>
    <p class="modal-subtitle">Commit all pending changes as a new configuration version.</p>
    ${baseInfo}
    <form onsubmit="saveVersion(event)">
      <label>Commit Message <span class="required">*</span></label>
      <input id="sv-message" placeholder="Describe the changes made…" required maxlength="500" autofocus>
      <div class="modal-actions">
        <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn">
          <svg width="14" height="14" stroke-width="2"><use href="#i-check"/></svg>
          Save Version
        </button>
      </div>
    </form>`;
    openModal(html);
    setTimeout(() => (document.getElementById("sv-message") as HTMLInputElement)?.focus(), 100);
}

/** Save a new version with the commit message. */
export async function saveVersion(e: Event): Promise<void> {
    e.preventDefault();
    const msg = (document.getElementById("sv-message") as HTMLInputElement).value.trim();
    if (!msg) {
        toast("Commit message is required", "error");
        return;
    }

    try {
        await api("/api/versions/save", {
            method: "POST",
            body: JSON.stringify({ message: msg }),
        });
        toast("Version saved successfully");
        closeModal();
        // Refresh full version status first (updates current_hash,
        // current_message, etc.), then refresh badges & markers.
        await checkVersionStatus();
        await refreshPendingBadges();
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Discard all pending changes. */
export async function discardChanges(): Promise<void> {
    if (!confirm("Discard all pending changes? This will restore the configuration to the last saved version.")) return;

    try {
        await api("/api/versions/discard", { method: "POST" });
        toast("All changes discarded");
        await refreshPendingBadges();
        const activeNav = document.querySelector(".nav-item.active") as HTMLElement | null;
        const section = activeNav?.dataset.section || "overview";
        switchSection(section);
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Revert a specific section to its last committed state. */
export async function revertSection(sectionKey: string): Promise<void> {
    const label = _sectionLabel(sectionKey);
    if (!confirm(`Revert all changes in "${label}"? This will restore this section to the last saved version.`)) return;

    try {
        await api("/api/versions/revert-section", {
            method: "POST",
            body: JSON.stringify({ section: sectionKey }),
        });
        toast(`${label} reverted`);
        await refreshPendingBadges();
        const sidebarSection = SECTION_MAP[sectionKey];
        if (sidebarSection) switchSection(sidebarSection);
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Open a modal showing pending changes for a specific section (or all). */
export function viewSectionChanges(sectionKey?: string): void {
    if (!state.pendingDiff?.has_pending) return;

    let diff: Record<string, SectionDiff>;
    let title: string;

    if (sectionKey) {
        const sd = state.pendingDiff.sections?.[sectionKey];
        if (!sd || sd.total === 0) return;
        diff = { [sectionKey]: sd };
        title = `Pending Changes - ${_sectionLabel(sectionKey)}`;
    } else {
        diff = state.pendingDiff.sections || {};
        title = "All Pending Changes";
    }

    const idPrefix = "vc-pending";
    const html = `
    <div class="view-changes-modal">
        <h3>${escHtml(title)}</h3>
        <div class="vc-content">${renderDiffContent(diff, idPrefix)}</div>
        <div class="modal-actions">
            <button type="button" class="btn btn-secondary" onclick="closeModal()">Close</button>
        </div>
    </div>`;
    openModal(html, { wide: true });
    // Auto-switch to the Diff tab (GitHub-style) for consistency with history
    setTimeout(() => switchDiffTab(idPrefix, "diff"), 0);
}

/* Inline Change Markers  */

/**
 * Apply change markers (banner + per-entity indicators) to the
 * currently visible section. Called automatically after every
 * badge refresh.
 */
export function applySectionChangeMarkers(): void {
    // Remove all existing markers
    document.querySelectorAll<HTMLElement>(".change-banner").forEach((el) => el.remove());
    document.querySelectorAll<HTMLElement>(".entity-change-badge").forEach((el) => el.remove());
    document.querySelectorAll<HTMLElement>(".entity-created, .entity-modified").forEach((el) => {
        el.classList.remove("entity-created", "entity-modified");
    });

    if (!state.pendingDiff?.has_pending) return;

    const activeNav = document.querySelector(".nav-item.active") as HTMLElement | null;
    const sidebarSection = activeNav?.dataset.section;
    if (!sidebarSection || sidebarSection === "overview" || sidebarSection === "config" || sidebarSection === "history") return;

    const sectionKey = SIDEBAR_TO_KEY[sidebarSection];
    if (!sectionKey) return;

    const diff = state.pendingDiff.sections?.[sectionKey];
    if (!diff || diff.total === 0) return;

    // Insert change banner at the top of the section
    const sec = document.getElementById(`sec-${sidebarSection}`);
    if (!sec) return;

    _insertChangeBanner(sec, sectionKey, diff);
    _markEntities(sec, sectionKey, diff);
}

/** Insert the change summary banner at the top of a section. */
function _insertChangeBanner(sec: HTMLElement, sectionKey: string, diff: SectionDiff): void {
    const createdCount = diff.created.length;
    const updatedCount = diff.updated.length;
    const deletedCount = diff.deleted.length;

    const parts: string[] = [];
    if (createdCount > 0) parts.push(`<span class="cb-stat cb-created">${createdCount} new</span>`);
    if (updatedCount > 0) parts.push(`<span class="cb-stat cb-modified">${updatedCount} modified</span>`);
    if (deletedCount > 0) parts.push(`<span class="cb-stat cb-deleted">${deletedCount} deleted</span>`);

    const banner = document.createElement("div");
    banner.className = "change-banner";
    banner.innerHTML = `
        <div class="cb-left">
            <svg width="15" height="15" stroke-width="2"><use href="#i-alert-triangle"/></svg>
            <span class="cb-title">${diff.total} unsaved change${diff.total !== 1 ? "s" : ""}</span>
            ${parts.join("")}
        </div>
        <div class="cb-actions">
            <button class="btn btn-sm btn-view-changes" onclick="viewSectionChanges('${escHtml(sectionKey)}')">
                <svg width="13" height="13" stroke-width="2"><use href="#i-eye"/></svg>
                View Changes
            </button>
            <button class="btn btn-sm btn-revert" onclick="revertSection('${escHtml(sectionKey)}')">
                <svg width="13" height="13" stroke-width="2"><use href="#i-x-circle"/></svg>
                Revert Section
            </button>
        </div>`;

    // Insert after the first .section-header or as first child
    const header = sec.querySelector(".section-header, .section-toolbar");
    if (header) header.after(banner);
    else sec.prepend(banner);
}

/** Mark individual entity cards/rows with change status classes & badges. */
function _markEntities(sec: HTMLElement, sectionKey: string, diff: SectionDiff): void {
    const nameKey = _entityNameKey(sectionKey);
    const isSettings = sectionKey === "global_settings" || sectionKey === "default_settings";

    const createdNames = new Set(diff.created.map((e) => _entityId(e, nameKey)));
    // For settings, the diff may carry entity_id on created entries
    // so we can match them to specific table rows by DB id.
    if (isSettings) {
        diff.created.forEach((e) => {
            if (e.entity_id != null) createdNames.add(String(e.entity_id));
            if (e.id != null) createdNames.add(String(e.id));
        });
    }

    // For settings with entity_id, match by DB id.
    // For legacy diffs (no entity_id), match by directive name via
    // data-entity-name on the directive cell.
    const updatedById = new Set<string>();
    const updatedByDirective = new Set<string>();
    diff.updated.forEach((u) => {
        if (u.entity_id) {
            updatedById.add(String(u.entity_id));
        } else if (isSettings) {
            updatedByDirective.add(String(u.entity));
        } else {
            updatedById.add(String(u.entity));
        }
    });

    const containers = sec.querySelectorAll<HTMLElement>("[data-entity-name]");
    containers.forEach((el) => {
        const name = el.dataset.entityName || "";
        if (createdNames.has(name)) {
            el.classList.add("entity-created");
            _appendEntityBadge(el, "New", "created");
        } else if (updatedById.has(name)) {
            el.classList.add("entity-modified");
            _appendEntityBadge(el, "Modified", "modified");
        } else if (isSettings && updatedByDirective.size > 0) {
            // Legacy fallback: match by directive text inside the row
            const dir = el.querySelector(".sett-directive")?.textContent?.trim() || "";
            if (updatedByDirective.has(dir)) {
                el.classList.add("entity-modified");
                _appendEntityBadge(el, "Modified", "modified");
                updatedByDirective.delete(dir); // one match per directive
            }
        }
    });
}

/** Append a small status badge to an entity card/row header. */
function _appendEntityBadge(el: HTMLElement, label: string, type: string): void {
    const badge = document.createElement("span");
    badge.className = `entity-change-badge ecb-${type}`;
    badge.textContent = label;

    // Insert INSIDE the name element so it stays inline with the text
    // and doesn't become a separate flex child in space-between layouts
    const nameEl = el.querySelector("h3, .entity-title, .sett-directive");
    if (nameEl) {
        nameEl.appendChild(badge);
        return;
    }

    // Table rows: insert into first cell
    const cell = el.querySelector("td:first-child");
    if (cell) {
        cell.appendChild(badge);
        return;
    }

    // Fallback
    el.prepend(badge);
}

/** Get the name/key field used for entity identification in a section. */
function _entityNameKey(sectionKey: string): string {
    if (sectionKey === "global_settings" || sectionKey === "default_settings") return "id";
    if (sectionKey === "ssl_certificates") return "domain";
    if (sectionKey === "acl_rules") return "_composite";
    return "name";
}

/** Extract the entity identifier from a diff entity. */
function _entityId(entity: Record<string, unknown>, nameKey: string): string {
    if (nameKey === "_composite") {
        // ACL rules use frontend_name:domain:sort_order composite key
        const fn = String(entity["frontend_name"] ?? "");
        const dom = String(entity["domain"] ?? "");
        const so = String(entity["sort_order"] ?? 0);
        return `${fn}:${dom}:${so}`;
    }
    return String(entity[nameKey] ?? "");
}

/** Get human-readable section label. */
function _sectionLabel(sectionKey: string): string {
    return SECTION_LABELS[sectionKey] || sectionKey;
}

/* Sidebar Internals  */

/** Update sidebar nav-item badges with pending counts. */
function _updateBadges(counts: Record<string, number>): void {
    document.querySelectorAll<HTMLElement>(".nav-badge").forEach((b) => b.remove());

    for (const [sectionKey, count] of Object.entries(counts)) {
        if (count <= 0) continue;
        const sidebarSection = SECTION_MAP[sectionKey];
        if (!sidebarSection) continue;

        const navItem = document.querySelector<HTMLElement>(`.nav-item[data-section="${sidebarSection}"]`);
        if (!navItem) continue;

        const badge = document.createElement("span");
        badge.className = "nav-badge";
        badge.textContent = String(count);
        navItem.appendChild(badge);
    }
}

/** Show/hide the save/discard buttons. */
function _updateSidebarActions(hasPending: boolean): void {
    const actions = document.getElementById("sidebar-actions");
    if (actions) {
        actions.style.display = hasPending ? "flex" : "none";
    }
    _updateVersionInfoBar();
}

/** Populate the version info bar above Save Version with current base version details. */
function _updateVersionInfoBar(): void {
    const infoEl = document.getElementById("sidebar-version-info");
    if (!infoEl) return;

    const vs = state.versionStatus;
    if (!vs?.current_hash) {
        infoEl.style.display = "none";
        return;
    }

    const shortHash = vs.current_hash.substring(0, 8);
    const message = vs.current_message || "No message";
    const author = vs.current_user_name || "Unknown";
    const dateStr = vs.current_created_at ? _relativeDate(vs.current_created_at) : "";

    infoEl.style.display = "flex";
    infoEl.innerHTML = `
        <div class="svi-label">Based on version</div>
        <div class="svi-detail">
            <span class="svi-hash">${escHtml(shortHash)}</span>
            <span class="svi-msg">${escHtml(message)}</span>
        </div>
        <div class="svi-meta">${escHtml(author)}${dateStr ? ` · ${escHtml(dateStr)}` : ""}</div>`;
}

/** Compute a relative date string. */
function _relativeDate(iso: string): string {
    const secs = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
    if (secs < 60) return "just now";
    const mins = Math.floor(secs / 60);
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 30) return `${days}d ago`;
    return new Date(iso).toLocaleDateString();
}
