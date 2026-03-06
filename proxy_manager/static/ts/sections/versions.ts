/**
 * Version Control
 * ===============
 *
 * Handles pending-change badge updates, save/discard flows,
 * and the save-version modal with commit message input.
 */

import { api, toast } from "../core/api";
import { openModal, closeModal, switchSection } from "../core/ui";
import { state } from "../state";
import { escHtml } from "../core/utils";
import type { VersionStatus } from "../types";

/** Section key → sidebar data-section attribute. */
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

/** Check initialization status. Returns true if initialized. */
export async function checkVersionStatus(): Promise<boolean> {
    try {
        const status: VersionStatus = await api("/api/versions/status");
        state.versionStatus = status;
        _updateBadges(status.pending_counts);
        _updateSidebarActions(status.has_pending);
        return status.initialized;
    } catch {
        return true; // Assume initialized on error
    }
}

/** Refresh pending change badges from the API. */
export async function refreshPendingBadges(): Promise<void> {
    try {
        const status: VersionStatus = await api("/api/versions/status");
        state.versionStatus = status;
        _updateBadges(status.pending_counts);
        _updateSidebarActions(status.has_pending);
    } catch {
        /* silently fail */
    }
}

/** Open the save-version modal with commit message input. */
export function openSaveVersionModal(): void {
    const html = `
    <h3>Save Version</h3>
    <p class="modal-subtitle">Commit all pending changes as a new configuration version.</p>
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
    // Focus the input after the modal opens
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
        // Reload current section to reflect restored state
        const activeNav = document.querySelector(".nav-item.active") as HTMLElement | null;
        const section = activeNav?.dataset.section || "overview";
        switchSection(section);
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Update sidebar nav-item badges with pending counts. */
function _updateBadges(counts: Record<string, number>): void {
    // Clear all existing badges
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
}
