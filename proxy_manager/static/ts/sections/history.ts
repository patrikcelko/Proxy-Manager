/**
 * Version History
 * ===============
 *
 * Displays the configuration version history with diffs,
 * and provides rollback functionality.
 */

import { api, toast } from "../core/api";
import { openModal, closeModal } from "../core/ui";
import { icon } from "../core/icons";
import { escHtml } from "../core/utils";
import { refreshPendingBadges } from "./versions";
import type { VersionSummary, VersionDetail, SectionDiff, FieldChange } from "../types";

/** Human-readable section labels. */
const SECTION_LABELS: Record<string, string> = {
    global_settings: "Global Settings",
    default_settings: "Defaults",
    frontends: "Frontends",
    acl_rules: "ACL Routing",
    backends: "Backends",
    listen_blocks: "Listen Blocks",
    userlists: "User Lists",
    resolvers: "DNS Resolvers",
    peers: "Peers",
    mailers: "Mailers",
    http_errors: "HTTP Errors",
    caches: "Cache",
    ssl_certificates: "SSL Certificates",
};

/** Load and render the version history list. */
export async function loadHistory(): Promise<void> {
    const container = document.getElementById("history-list");
    if (!container) return;

    container.innerHTML = `<div class="loading-placeholder">Loading history…</div>`;

    try {
        const data = await api("/api/versions?limit=100");
        const versions: VersionSummary[] = data.items || [];

        if (versions.length === 0) {
            container.innerHTML = `<div class="empty-state">${icon("clock", 32, 1.5)} <p>No versions yet</p></div>`;
            return;
        }

        container.innerHTML = versions.map((v, idx) => _renderVersionCard(v, idx === 0)).join("");
    } catch (err: any) {
        container.innerHTML = `<div class="empty-state error">${icon("alert-triangle", 32, 1.5)} <p>${escHtml(err.message)}</p></div>`;
    }
}

function _renderVersionCard(v: VersionSummary, isLatest: boolean): string {
    const shortHash = v.hash.substring(0, 8);
    const date = _formatDate(v.created_at);
    const relDate = _relativeDate(v.created_at);
    const latestBadge = isLatest ? `<span class="badge badge-ok">Latest</span>` : "";
    const rollbackBtn = !isLatest
        ? `<button class="btn btn-ghost btn-sm" onclick="rollbackVersion('${escHtml(v.hash)}')">${icon("repeat", 12)} Rollback</button>`
        : "";

    return `
    <div class="history-card" data-hash="${escHtml(v.hash)}">
        <div class="history-header" onclick="toggleHistoryDiff('${escHtml(v.hash)}')">
            <div class="history-meta">
                <span class="history-hash">${icon("hash", 14)} ${escHtml(shortHash)}</span>
                ${latestBadge}
                <span class="history-message">${escHtml(v.message)}</span>
            </div>
            <div class="history-info">
                <span class="history-author">${icon("user", 12)} ${escHtml(v.user_name)}</span>
                <span class="history-date" title="${escHtml(date)}">${icon("clock", 12)} ${escHtml(relDate)}</span>
                ${rollbackBtn}
                <span class="history-chevron">${icon("chevron-down", 14, 2, "chevron")}</span>
            </div>
        </div>
        <div class="history-diff" id="diff-${escHtml(v.hash)}" style="display:none">
            <div class="diff-loading">Loading diff…</div>
        </div>
    </div>`;
}

/** Toggle diff panel for a version card. */
export async function toggleHistoryDiff(hash: string): Promise<void> {
    const diffEl = document.getElementById(`diff-${hash}`);
    const card = diffEl?.closest(".history-card");
    if (!diffEl || !card) return;

    const isOpen = card.classList.toggle("open");
    diffEl.style.display = isOpen ? "block" : "none";

    if (isOpen && diffEl.querySelector(".diff-loading")) {
        try {
            const detail: VersionDetail = await api(`/api/versions/${hash}`);
            diffEl.innerHTML = _renderDiff(detail.diff);
        } catch (err: any) {
            diffEl.innerHTML = `<div class="diff-error">${escHtml(err.message)}</div>`;
        }
    }
}

/** Rollback to a specific version. */
export async function rollbackVersion(hash: string): Promise<void> {
    if (!confirm(`Rollback to version ${hash.substring(0, 8)}? This will restore the configuration to that state and create a new version.`)) return;

    try {
        await api(`/api/versions/${hash}/rollback`, { method: "POST" });
        toast("Rollback successful");
        loadHistory();
        refreshPendingBadges();
    } catch (err: any) {
        toast(err.message, "error");
    }
}

function _renderDiff(diff: Record<string, SectionDiff>): string {
    const sections = Object.keys(diff);
    if (sections.length === 0) {
        return `<div class="diff-empty">No changes in this version</div>`;
    }

    return sections
        .map((key) => {
            const s = diff[key];
            const label = SECTION_LABELS[key] || key;
            const parts: string[] = [];

            if (s.created.length > 0) {
                parts.push(
                    `<div class="diff-group diff-created">
                        <div class="diff-group-header">${icon("plus", 12)} Added (${s.created.length})</div>
                        ${s.created.map((item) => `<div class="diff-item">${_renderEntity(item)}</div>`).join("")}
                    </div>`
                );
            }

            if (s.deleted.length > 0) {
                parts.push(
                    `<div class="diff-group diff-deleted">
                        <div class="diff-group-header">${icon("trash", 12)} Removed (${s.deleted.length})</div>
                        ${s.deleted.map((item) => `<div class="diff-item">${_renderEntity(item)}</div>`).join("")}
                    </div>`
                );
            }

            if (s.updated.length > 0) {
                parts.push(
                    `<div class="diff-group diff-updated">
                        <div class="diff-group-header">${icon("edit-pen", 12)} Modified (${s.updated.length})</div>
                        ${s.updated.map((u) => _renderUpdate(u)).join("")}
                    </div>`
                );
            }

            return `
            <div class="diff-section">
                <div class="diff-section-header">
                    <span class="diff-section-label">${escHtml(label)}</span>
                    <span class="diff-section-count">${s.total} change${s.total !== 1 ? "s" : ""}</span>
                </div>
                ${parts.join("")}
            </div>`;
        })
        .join("");
}

function _renderEntity(item: Record<string, unknown>): string {
    const name = (item.name || item.directive || item.domain || item.frontend_name || "") as string;
    return `<span class="diff-entity-name">${escHtml(name)}</span>`;
}

function _renderUpdate(u: { entity: string; changes: FieldChange[] }): string {
    const changes = (u.changes || [])
        .filter((c) => c.field !== "binds" && c.field !== "options" && c.field !== "servers" && c.field !== "entries" && c.field !== "nameservers")
        .map((c) => {
            const oldVal = _formatValue(c.old);
            const newVal = _formatValue(c.new);
            return `<div class="diff-field">
                <span class="diff-field-name">${escHtml(c.field)}</span>
                <span class="diff-old">${escHtml(oldVal)}</span>
                <span class="diff-arrow">→</span>
                <span class="diff-new">${escHtml(newVal)}</span>
            </div>`;
        })
        .join("");

    return `<div class="diff-item diff-update-item">
        <span class="diff-entity-name">${escHtml(u.entity)}</span>
        ${changes ? `<div class="diff-fields">${changes}</div>` : ""}
    </div>`;
}

function _formatValue(val: unknown): string {
    if (val === null || val === undefined) return "–";
    if (typeof val === "boolean") return val ? "yes" : "no";
    if (typeof val === "object") return JSON.stringify(val);
    return String(val);
}

function _formatDate(iso: string): string {
    const d = new Date(iso);
    return d.toLocaleString();
}

function _relativeDate(iso: string): string {
    const d = new Date(iso);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    const secs = Math.floor(diff / 1000);

    if (secs < 60) return "just now";
    const mins = Math.floor(secs / 60);
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 30) return `${days}d ago`;
    return d.toLocaleDateString();
}
