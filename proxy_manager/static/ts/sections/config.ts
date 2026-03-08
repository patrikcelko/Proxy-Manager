/**
 * Manual Edit section
 * ===================
 *
 * Provides a raw text editor for the HAProxy configuration.
 * Changes are validated before saving and imported as pending
 * modifications (no new version is created automatically).
 */

import { api, toast } from "../core/api";

/** Tracks whether the editor has been loaded and modified. */
let _loaded = false;
let _originalText = "";

/** Loads the current configuration into the editor textarea. */
export async function loadManualEdit(): Promise<void> {
    const ta = document.getElementById("config-export-text") as HTMLTextAreaElement;
    const bar = document.getElementById("manual-edit-version-bar") as HTMLElement;
    const label = document.getElementById("mev-label") as HTMLElement;

    try {
        const d = await api<{ config_text: string }>("/api/config/export");
        _originalText = d.config_text || "";
        ta.value = _originalText;
        _loaded = true;

        // Show version bar
        bar.style.display = "flex";

        // Get current version info
        try {
            const status = await api<{ current_hash: string | null; current_message: string | null }>("/api/versions/status");
            const hash = status.current_hash;
            const msg = status.current_message;
            if (hash) {
                label.textContent = `Editing from ${hash.substring(0, 8)}${msg ? ` - ${msg}` : ""}`;
            } else {
                label.textContent = "Editing configuration";
            }
        } catch {
            label.textContent = "Editing configuration";
        }
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Exports the current config (alias for loadManualEdit for compatibility). */
export async function exportConfig(): Promise<void> {
    return loadManualEdit();
}

/** Copies the editor content to the clipboard. */
export function copyExport(): void {
    const ta = document.getElementById("config-export-text") as HTMLTextAreaElement;
    if (!ta.value) {
        toast("Nothing to copy", "error");
        return;
    }
    navigator.clipboard.writeText(ta.value).then(() => toast("Copied to clipboard"));
}

/** Validates and saves the manual edit, importing it as pending changes. */
export async function saveManualEdit(): Promise<void> {
    const ta = document.getElementById("config-export-text") as HTMLTextAreaElement;
    const msgEl = document.getElementById("config-validation-msg") as HTMLElement;
    const text = ta.value.trim();

    if (!text) {
        _showValidation(msgEl, "Configuration cannot be empty.", true);
        return;
    }

    if (!_loaded) {
        toast("Load the configuration first", "error");
        return;
    }

    if (text === _originalText.trim()) {
        toast("No changes detected");
        return;
    }

    // Validate first
    try {
        const result = await api<{ valid: boolean; error: string }>("/api/config/validate", {
            method: "POST",
            body: JSON.stringify({ config_text: text }),
        });

        if (!result.valid) {
            _showValidation(msgEl, result.error || "Invalid configuration", true);
            return;
        }
    } catch (err: any) {
        _showValidation(msgEl, err.message || "Validation failed", true);
        return;
    }

    // Import (non-merge = replace all)
    try {
        await api("/api/config/import", {
            method: "POST",
            body: JSON.stringify({ config_text: text, merge: false }),
        });

        _showValidation(msgEl, "Changes saved successfully. Pending changes are now reflected across all sections.", false);
        _originalText = text;
        toast("Configuration saved - changes are pending");

        // Refresh badges
        import("./versions").then((m) => m.refreshPendingBadges()).catch(() => { });
    } catch (err: any) {
        _showValidation(msgEl, err.message || "Import failed", true);
    }
}

/** Discards the editor content and reloads the original configuration. */
export async function discardManualEdit(): Promise<void> {
    const ta = document.getElementById("config-export-text") as HTMLTextAreaElement;
    const msgEl = document.getElementById("config-validation-msg") as HTMLElement;

    if (_loaded && ta.value.trim() !== _originalText.trim()) {
        if (!confirm("Discard your unsaved editor changes and reload the current configuration?")) return;
    }

    ta.value = _originalText;
    msgEl.style.display = "none";
    toast("Editor reset to current configuration");
}

/** Shows a validation / status message below the textarea. */
function _showValidation(el: HTMLElement, msg: string, isError: boolean): void {
    el.textContent = msg;
    el.className = `config-validation-msg ${isError ? "validation-error" : "validation-success"}`;
    el.style.display = "block";
}
