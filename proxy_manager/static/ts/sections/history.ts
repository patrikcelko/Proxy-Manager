/**
 * Version History
 * ===============
 */

import { api, toast } from "../core/api";
import { icon } from "../core/icons";
import { escHtml, SECTION_LABELS } from "../core/utils";
import { refreshPendingBadges } from "./versions";
import type { VersionListResponse, VersionSummary, VersionDetail, SectionDiff, FieldChange, EntityUpdate } from "../types";

/** Load and render the version history list. */
export async function loadHistory(): Promise<void> {
    const container = document.getElementById("history-list");
    if (!container) return;

    container.innerHTML = `<div class="loading-placeholder">Loading history…</div>`;

    try {
        const data = await api<VersionListResponse>("/api/versions?limit=100");
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
            diffEl.innerHTML = _renderDiffTabs(detail.diff, `ht-${hash}`);
        } catch (err: any) {
            diffEl.innerHTML = `<div class="diff-error">${escHtml(err.message)}</div>`;
        }
    }
}

/** Switch between Changes / Diff tabs inside a diff panel. */
export function switchDiffTab(tabId: string, tab: string): void {
    const wrap = document.getElementById(tabId);
    if (!wrap) return;
    wrap.querySelectorAll<HTMLElement>(".dtab-btn").forEach((b) => b.classList.toggle("active", b.dataset.tab === tab));
    wrap.querySelectorAll<HTMLElement>(".dtab-pane").forEach((p) => (p.style.display = p.dataset.tab === tab ? "block" : "none"));
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

/**
 * Render a diff-content block (with tabs) for a given diff payload.
 * Reused by the "View Changes" modal in versions.ts.
 */
export function renderDiffContent(diff: Record<string, SectionDiff>, idPrefix: string): string {
    return _renderDiffTabs(diff, idPrefix);
}

/* Card / Tabs rendering */

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

/** Render the tabbed container (Changes + Diff). */
function _renderDiffTabs(diff: Record<string, SectionDiff>, id: string): string {
    const sections = Object.keys(diff);
    if (sections.length === 0) return `<div class="diff-empty">No changes in this version</div>`;

    // Summary counts
    let totalAdded = 0, totalModified = 0, totalDeleted = 0;
    for (const s of Object.values(diff)) {
        totalAdded += s.created.length;
        totalModified += s.updated.length;
        totalDeleted += s.deleted.length;
    }

    const summaryParts: string[] = [];
    if (totalAdded > 0) summaryParts.push(`<span class="dtab-stat dtab-s-add">+${totalAdded}</span>`);
    if (totalModified > 0) summaryParts.push(`<span class="dtab-stat dtab-s-mod">~${totalModified}</span>`);
    if (totalDeleted > 0) summaryParts.push(`<span class="dtab-stat dtab-s-del">-${totalDeleted}</span>`);
    const summary = summaryParts.length ? `<span class="dtab-summary">${summaryParts.join("")}</span>` : "";

    return `
    <div class="dtab-wrap" id="${escHtml(id)}">
        <div class="dtab-bar">
            <button class="dtab-btn active" data-tab="changes" onclick="switchDiffTab('${escHtml(id)}','changes')">
                ${icon("layers", 13)} Changes
            </button>
            <button class="dtab-btn" data-tab="diff" onclick="switchDiffTab('${escHtml(id)}','diff')">
                ${icon("code", 13)} Diff
            </button>
            ${summary}
        </div>
        <div class="dtab-pane" data-tab="changes" style="display:block">
            ${_renderStructuredDiff(diff)}
        </div>
        <div class="dtab-pane" data-tab="diff" style="display:none">
            ${_renderUnifiedDiff(diff)}
        </div>
    </div>`;
}

/*  Structured Changes view   */

function _renderStructuredDiff(diff: Record<string, SectionDiff>): string {
    return Object.entries(diff)
        .map(([key, s]) => {
            const label = SECTION_LABELS[key] || key;
            const parts: string[] = [];

            if (s.created.length > 0) {
                parts.push(
                    `<div class="diff-group diff-created">
                        <div class="diff-group-header">${icon("plus", 12)} Added (${s.created.length})</div>
                        ${s.created.map((item) => `<div class="diff-item"><span class="diff-entity-name">${escHtml(_entityName(item))}</span>${_renderEntityFields(item)}</div>`).join("")}
                    </div>`
                );
            }

            if (s.deleted.length > 0) {
                parts.push(
                    `<div class="diff-group diff-deleted">
                        <div class="diff-group-header">${icon("trash", 12)} Removed (${s.deleted.length})</div>
                        ${s.deleted.map((item) => `<div class="diff-item"><span class="diff-entity-name">${escHtml(_entityName(item))}</span></div>`).join("")}
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

/** Render a newly-created entity with all its key fields. */
function _renderEntityFields(item: Record<string, unknown>): string {
    const skip = new Set(["id", "binds", "options", "servers", "entries", "nameservers"]);
    const fields = Object.entries(item).filter(([k, v]) => !skip.has(k) && v !== null && v !== undefined && v !== "");
    if (fields.length <= 1) return "";
    return `<div class="diff-fields">${fields
        .map(([k, v]) => `<div class="diff-field"><span class="diff-field-name">${escHtml(k)}</span><span class="diff-new">${escHtml(_fmtVal(v))}</span></div>`)
        .join("")}</div>`;
}

function _renderUpdate(u: EntityUpdate): string {
    const changes = (u.changes || [])
        .filter((c) => !_isNestedField(c.field))
        .map((c) => {
            const oldVal = _fmtVal(c.old);
            const newVal = _fmtVal(c.new);
            return `<div class="diff-field">
                <span class="diff-field-name">${escHtml(c.field)}</span>
                <span class="diff-old">${escHtml(oldVal)}</span>
                <span class="diff-arrow">${icon("arrow-right-narrow", 12, 2)}</span>
                <span class="diff-new">${escHtml(newVal)}</span>
            </div>`;
        })
        .join("");

    // Nested sub-entity changes (binds, options, servers, etc.)
    const nested = (u.changes || []).filter((c) => _isNestedField(c.field));
    const nestedHtml = nested.length > 0 ? _renderNestedChanges(nested) : "";

    return `<div class="diff-item diff-update-item">
        <span class="diff-entity-name">${escHtml(u.entity)}</span>
        ${changes ? `<div class="diff-fields">${changes}</div>` : ""}
        ${nestedHtml}
    </div>`;
}

/** Check if a field represents a nested sub-entity list. */
function _isNestedField(field: string): boolean {
    return ["binds", "options", "servers", "entries", "nameservers"].includes(field);
}

/** Render nested sub-entity changes (e.g. frontend options). */
function _renderNestedChanges(changes: FieldChange[]): string {
    return changes.map((c) => {
        const oldArr = Array.isArray(c.old) ? c.old : [];
        const newArr = Array.isArray(c.new) ? c.new : [];
        const added = newArr.length - oldArr.length;
        const label = c.field;
        const badge = added > 0 ? `<span class="dtab-stat dtab-s-add">+${added}</span>` : added < 0 ? `<span class="dtab-stat dtab-s-del">${added}</span>` : `<span class="dtab-stat dtab-s-mod">~</span>`;
        return `<div class="diff-nested-note">${icon("layers", 11)} <span>${escHtml(label)}</span> ${badge} <span class="diff-nested-count">(${newArr.length} total)</span></div>`;
    }).join("");
}

/*  Unified Diff view   */

function _renderUnifiedDiff(diff: Record<string, SectionDiff>): string {
    const blocks: string[] = [];

    for (const [key, s] of Object.entries(diff)) {
        const label = SECTION_LABELS[key] || key;
        const lines: string[] = [];

        // Created entities
        for (const item of s.created) {
            const name = _entityName(item);
            lines.push(_udLine("+", `+ ${name}`, "add"));
            _entityToLines(item).forEach((l) => lines.push(_udLine("+", `+   ${l}`, "add")));
            lines.push(_udSpacer());
        }

        // Deleted entities
        for (const item of s.deleted) {
            const name = _entityName(item);
            lines.push(_udLine("-", `- ${name}`, "del"));
            _entityToLines(item).forEach((l) => lines.push(_udLine("-", `-   ${l}`, "del")));
            lines.push(_udSpacer());
        }

        // Updated entities
        for (const u of s.updated) {
            lines.push(_udLine("~", `  ${u.entity}`, "ctx"));
            for (const c of u.changes) {
                if (_isNestedField(c.field)) {
                    const oldLen = Array.isArray(c.old) ? c.old.length : 0;
                    const newLen = Array.isArray(c.new) ? c.new.length : 0;
                    lines.push(_udLine("~", `    ${c.field}: ${oldLen} \u2192 ${newLen} items`, "mod"));
                    continue;
                }
                lines.push(_udLine("-", `-   ${c.field}: ${_fmtVal(c.old)}`, "del"));
                lines.push(_udLine("+", `+   ${c.field}: ${_fmtVal(c.new)}`, "add"));
            }
            lines.push(_udSpacer());
        }

        if (lines.length > 0) {
            // Remove trailing spacer
            if (lines[lines.length - 1].includes("ud-spacer")) lines.pop();
            blocks.push(`
            <div class="ud-section">
                <div class="ud-file-header">${icon("file-text", 13)} ${escHtml(label)}
                    <span class="ud-file-stats">
                        <span class="ud-fs-add">+${s.created.length + s.updated.length}</span>
                        <span class="ud-fs-del">-${s.deleted.length}</span>
                    </span>
                </div>
                <div class="ud-block">${lines.join("")}</div>
            </div>`);
        }
    }

    return blocks.length > 0 ? blocks.join("") : `<div class="diff-empty">No field-level changes</div>`;
}

function _udLine(gutter: string, text: string, type: string): string {
    return `<div class="ud-line ud-${type}"><span class="ud-gutter">${escHtml(gutter)}</span><span class="ud-text">${escHtml(text)}</span></div>`;
}

function _udSpacer(): string {
    return `<div class="ud-line ud-spacer"><span class="ud-gutter"> </span><span class="ud-text"> </span></div>`;
}

/** Convert an entity dict to key: value lines for the diff view. */
function _entityToLines(item: Record<string, unknown>): string[] {
    const skip = new Set(["id", "binds", "options", "servers", "entries", "nameservers"]);
    return Object.entries(item)
        .filter(([k, v]) => !skip.has(k) && v !== null && v !== undefined)
        .map(([k, v]) => `${k}: ${_fmtVal(v)}`);
}

/* Utilities */

function _entityName(item: Record<string, unknown>): string {
    return String(item.name || item.directive || item.domain || item.frontend_name || "");
}

function _fmtVal(val: unknown): string {
    if (val === null || val === undefined) return "–";
    if (typeof val === "boolean") return val ? "yes" : "no";
    if (typeof val === "object") return JSON.stringify(val);
    return String(val);
}

function _formatDate(iso: string): string {
    return new Date(iso).toLocaleString();
}

function _relativeDate(iso: string): string {
    const d = new Date(iso);
    const secs = Math.floor((Date.now() - d.getTime()) / 1000);
    if (secs < 60) return "just now";
    const mins = Math.floor(secs / 60);
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 30) return `${days}d ago`;
    return d.toLocaleDateString();
}
