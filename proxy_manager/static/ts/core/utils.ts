/**
 * Utilities
 * =========
 *
 * Shared helper functions used across core and section modules.
 */

import { api, toast } from "./api";
import { closeModal, confirmPopup } from "./ui";

/** Escapes HTML special characters to prevent XSS in rendered templates. */
export function escHtml(s: unknown): string {
    if (s == null) return "";
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

/** Encodes a JS object as an HTML-safe JSON string for use in onclick attributes. */
export function escJsonAttr(obj: unknown): string {
    return JSON.stringify(obj).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

/** Parses a string to integer, returning fallback if not a number. */
export function safeInt(val: string | number | null | undefined, fallback: number | null = null): number | null {
    const n = parseInt(String(val), 10);
    return isNaN(n) ? fallback : n;
}

/** Human-readable section labels shared across version control and history modules. */
export const SECTION_LABELS: Record<string, string> = {
    global_settings: "Global Settings",
    default_settings: "Defaults",
    frontends: "Frontends",
    acl_rules: "ACL Routing",
    backends: "Backends",
    listen_blocks: "Listen Blocks",
    userlists: "Auth Lists",
    resolvers: "DNS Resolvers",
    peers: "Peers",
    mailers: "Mailers",
    http_errors: "HTTP Errors",
    caches: "Cache",
    ssl_certificates: "SSL Certificates",
};

/** Generic CRUD save: creates or updates an entity and reloads on success. */
export async function crudSave(baseUrl: string, body: unknown, entityId: number | null, reloadFn: () => void): Promise<void> {
    try {
        if (entityId != null) await api(`${baseUrl}/${entityId}`, { method: "PUT", body: JSON.stringify(body) });
        else await api(baseUrl, { method: "POST", body: JSON.stringify(body) });
        toast("Saved");
        closeModal();
        reloadFn();
    } catch (err) {
        toast((err as Error).message, "error");
    }
}

/** Generic CRUD delete: confirms with user then deletes and reloads. */
export async function crudDelete(url: string, confirmMsg: string, reloadFn: () => void): Promise<void> {
    if (!(await confirmPopup(confirmMsg, "Delete"))) return;
    try {
        await api(url, { method: "DELETE" });
        toast("Deleted");
        reloadFn();
    } catch (err) {
        toast((err as Error).message, "error");
    }
}

/** Generic preset grid filter: shows/hides cards by category tab. */
export function filterPresetGrid(gridId: string, searchId: string, catAttr: string, cat: string): void {
    const grid = document.getElementById(gridId);
    if (!grid) return;
    const searchInput = document.getElementById(searchId) as HTMLInputElement | null;
    if (searchInput) searchInput.value = "";
    const label = cat === "all" ? "All" : cat;
    grid.closest(".modal")?.querySelectorAll(".stabs .stab").forEach((t) => t.classList.toggle("active", t.textContent?.trim() === label));
    grid.querySelectorAll<HTMLElement>(".dir-card").forEach((c) => (c.style.display = cat === "all" || c.dataset[catAttr] === cat ? "" : "none"));
}

/** Generic preset grid search: filters cards by free-text query. */
export function searchPresetGrid(gridId: string, searchId: string, catAttr: string, resetCat: string = "all"): void {
    const q = ((document.getElementById(searchId) as HTMLInputElement | null)?.value || "").toLowerCase().trim();
    const grid = document.getElementById(gridId);
    if (!grid) return;
    if (!q) {
        filterPresetGrid(gridId, searchId, catAttr, resetCat);
        return;
    }
    grid.closest(".modal")?.querySelectorAll(".stabs .stab").forEach((t) => t.classList.remove("active"));
    grid.querySelectorAll<HTMLElement>(".dir-card").forEach((c) => (c.style.display = (c.dataset.searchText || "").includes(q) ? "" : "none"));
}
