/**
 * First-time Setup
 * ================
 *
 * Handles the initial setup flow when the application has no
 * committed configuration version. Presents two options:
 * start with an empty config or import an existing one.
 */

import { api, toast } from "../core/api";
import { showApp } from "../core/auth";

/** Show the setup overlay. */
export function showSetup(): void {
    document.getElementById("setup-overlay")!.style.display = "flex";
    document.getElementById("app-layout")!.style.display = "none";
    document.getElementById("app-footer")!.style.display = "none";
}

/** Hide the setup overlay and proceed to main app. */
function hideSetup(): void {
    document.getElementById("setup-overlay")!.style.display = "none";
    showApp();
}

/** Initialize with an empty configuration. */
export async function initEmpty(): Promise<void> {
    try {
        await api("/api/versions/init/empty", { method: "POST" });
        toast("Configuration initialized");
        hideSetup();
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Open file picker and initialize by importing a config. */
export async function initImport(): Promise<void> {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".cfg,.conf,.txt";
    input.onchange = async (e: Event) => {
        const files = (e.target as HTMLInputElement).files;
        const file = files?.[0];
        if (!file) return;
        const text = await file.text();
        try {
            await api("/api/versions/init/import", {
                method: "POST",
                body: JSON.stringify({ config_text: text }),
            });
            toast("Configuration imported and initialized!");
            hideSetup();
        } catch (err: any) {
            toast(err.message, "error");
        }
    };
    input.click();
}
