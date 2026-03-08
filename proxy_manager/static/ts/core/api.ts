/**
 * API
 * ===
 *
 * Handles all HTTP requests, authentication headers, and toast
 * notifications for user feedback throughout the application.
 */

/** Base API path prefix (empty = same origin). */
export const API = "";

/** JWT token persisted in localStorage. */
export let TOKEN: string | null = localStorage.getItem("pm_token") || null;

/** Update the in-memory JWT token. */
export function setToken(value: string | null): void {
    TOKEN = value;
}

/** Builds the standard request headers with optional JSON content-type. */
export function headers(json: boolean = true): Record<string, string> {
    const h: Record<string, string> = {};
    if (TOKEN) h["Authorization"] = `Bearer ${TOKEN}`;
    if (json) h["Content-Type"] = "application/json";
    return h;
}

/** Performs an authenticated API request and handles 401 auto-logout. */
export async function api<T = unknown>(path: string, opts: RequestInit & { json?: boolean } = {}): Promise<T> {
    const { json: jsonFlag, ...fetchOpts } = opts;
    const res = await fetch(API + path, { headers: headers(jsonFlag !== false), ...fetchOpts });
    if (res.status === 401) {
        // Dynamically import to avoid circular dependency
        const { logout } = await import("./auth");
        logout();
        throw new Error("Unauthorized");
    }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error((data as Record<string, unknown>).detail as string || `Error ${res.status}`);

    // Auto-refresh version badges after any data mutation
    const method = (fetchOpts.method || "GET").toUpperCase();
    if (method !== "GET" && !path.startsWith("/api/versions/") && !path.startsWith("/auth")) {
        import("../sections/versions").then((m) => m.refreshPendingBadges()).catch(() => { });
    }

    return data as T;
}

/** Shows a temporary toast notification at the bottom of the screen. */
export function toast(msg: string, type: string = "success"): void {
    const c = document.getElementById("toast-container");
    if (!c) return;
    const t = document.createElement("div");
    t.className = `toast toast-${type}`;
    t.textContent = msg;
    c.appendChild(t);
    setTimeout(() => {
        t.classList.add("fade-out");
        setTimeout(() => t.remove(), 350);
    }, 3500);
}
