/**
 * Config Export section
 * =====================
 *
 * Handles exporting the current configuration with copy support.
 */

import { api, toast } from "../core/api";

/** Fetches the current HAProxy configuration text from the API and displays it in the export textarea. */
export async function exportConfig(): Promise<void> {
    try {
        const d = await api("/api/config/export");
        (document.getElementById("config-export-text") as HTMLTextAreaElement).value = d.config_text || d;
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Copies the exported configuration text to the clipboard. */
export function copyExport(): void {
    const ta = document.getElementById("config-export-text") as HTMLTextAreaElement;
    navigator.clipboard.writeText(ta.value).then(() => toast("Copied to clipboard"));
}
