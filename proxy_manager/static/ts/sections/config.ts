/**
 * Config Import / Export section
 * ==============================
 *
 * Handles importing HAProxy configuration from a file
 * and exporting the current configuration with copy support.
 */

import { api, toast } from "../core/api";
import { switchSection } from "../core/ui";

/** Opens a file picker dialog and imports the selected HAProxy config via the API. */
export async function importConfig(): Promise<void> {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".cfg,.conf,.txt";
    input.onchange = async (e: Event) => {
        const files = (e.target as HTMLInputElement).files;
        const file = files?.[0];
        if (!file) return;
        const text = await file.text();
        try {
            await api("/api/config/import", { method: "POST", body: JSON.stringify({ config_text: text }) });
            toast("Configuration imported!");
            switchSection("overview");
        } catch (err: any) {
            toast(err.message, "error");
        }
    };
    input.click();
}

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
