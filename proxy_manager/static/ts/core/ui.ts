/**
 * User Interface
 * ==============
 *
 * Section switching with navigation highlighting, modal dialogs,
 * collapsible panels, and entity card expand/collapse behavior.
 */

import { icon } from "./icons";
import { loadOverview } from "../sections/overview";
import { loadSettings } from "../sections/settings";
import { loadFrontends } from "../sections/frontends";
import { loadBackends } from "../sections/backends";
import { loadAclRules } from "../sections/acl";
import { loadListenBlocks } from "../sections/listen";
import { loadUserlists } from "../sections/userlists";
import { loadResolvers } from "../sections/resolvers";
import { loadPeers } from "../sections/peers";
import { loadMailers } from "../sections/mailers";
import { loadHttpErrors } from "../sections/http-errors";
import { loadCaches } from "../sections/caches";
import { loadSslCertificates } from "../sections/ssl";
import { loadManualEdit } from "../sections/config";
import { loadHistory } from "../sections/history";
import { loadUsers } from "../sections/users";

/** Human-readable titles displayed in the top bar for each section. */
const _sectionTitles: Record<string, string> = {
    overview: "Dashboard",
    global: "Global Settings",
    defaults: "Defaults",
    frontends: "Frontends",
    backends: "Backends",
    acl: "ACL Routing",
    listen: "Listen / Stats",
    userlists: "Auth Lists",
    "ssl-certificates": "SSL / TLS Certificates",
    resolvers: "DNS Resolvers",
    peers: "Peers",
    mailers: "Mailers",
    "http-errors": "HTTP Errors",
    caches: "Cache",
    config: "Manual Edit",
    users: "Users",
    history: "Version History",
};

/** Switches the active SPA section, updates nav highlighting, and triggers data loading. */
export function switchSection(name: string): void {
    document.querySelectorAll(".nav-item").forEach((i) => i.classList.toggle("active", (i as HTMLElement).dataset.section === name));
    document.querySelectorAll(".section").forEach((s) => s.classList.toggle("active", s.id === `sec-${name}`));
    const titleEl = document.getElementById("top-bar-page-title");
    if (titleEl) titleEl.textContent = _sectionTitles[name] || name;

    // Close sidebar on mobile after navigation
    document.getElementById("sidebar")?.classList.remove("open");
    document.getElementById("sidebar-backdrop")?.classList.remove("open");
    const loaders: Record<string, () => void> = {
        overview: loadOverview,
        global: () => loadSettings("global"),
        defaults: () => loadSettings("defaults"),
        frontends: loadFrontends,
        backends: loadBackends,
        acl: loadAclRules,
        listen: loadListenBlocks,
        userlists: loadUserlists,
        resolvers: loadResolvers,
        peers: loadPeers,
        mailers: loadMailers,
        "http-errors": loadHttpErrors,
        caches: loadCaches,
        "ssl-certificates": loadSslCertificates,
        config: loadManualEdit,
        history: loadHistory,
        users: loadUsers,
    };
    if (loaders[name]) loaders[name]();

    // Apply change markers after a brief delay to let the section render
    setTimeout(() => {
        import("../sections/versions").then((m) => m.applySectionChangeMarkers()).catch(() => { });
    }, 120);
}

/** Opens a centered modal dialog with the given HTML content. */
export function openModal(html: string, opts: { wide?: boolean } = {}): void {
    const m = document.getElementById("modal-content")!;
    m.innerHTML = html;
    m.classList.toggle("modal-wide", !!opts.wide);
    document.getElementById("modal-overlay")!.classList.add("show");
}

/** Closes the currently open modal dialog. */
export function closeModal(): void {
    document.getElementById("modal-overlay")?.classList.remove("show");
}

/** Close modal on Escape key. */
export function initModalListeners(): void {
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") closeModal();
    });

    const overlay = document.getElementById("modal-overlay");
    if (overlay) {
        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) closeModal();
        });
    }
}

/** Toggles a collapsible form section open/closed. */
export function toggleCollapsible(el: HTMLElement): void {
    el.classList.toggle("open");
    (el.nextElementSibling as HTMLElement | null)?.classList.toggle("open");
}

/** Toggles an entity card (backend server, bind entry, etc.) expanded/collapsed. */
export function toggleEntityCard(el: HTMLElement): void {
    el.closest(".entity-card")?.classList.toggle("open");
}

/** Shows a custom confirmation dialog and returns a promise that resolves to true/false. */
export function confirmPopup(message: string, title = "Confirm"): Promise<boolean> {
    return new Promise((resolve) => {
        const overlay = document.getElementById("confirm-overlay")!;
        const titleEl = document.getElementById("confirm-title")!;
        const msgEl = document.getElementById("confirm-message")!;
        const okBtn = document.getElementById("confirm-ok")!;
        const cancelBtn = document.getElementById("confirm-cancel")!;

        titleEl.textContent = title;
        msgEl.textContent = message;
        overlay.classList.add("show");

        const cleanup = () => {
            overlay.classList.remove("show");
            okBtn.removeEventListener("click", onOk);
            cancelBtn.removeEventListener("click", onCancel);
            overlay.removeEventListener("click", onBackdrop);
            document.removeEventListener("keydown", onKey);
        };
        const onOk = () => { cleanup(); resolve(true); };
        const onCancel = () => { cleanup(); resolve(false); };
        const onBackdrop = (e: MouseEvent) => { if (e.target === overlay) onCancel(); };
        const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onCancel(); else if (e.key === "Enter") onOk(); };

        okBtn.addEventListener("click", onOk);
        cancelBtn.addEventListener("click", onCancel);
        overlay.addEventListener("click", onBackdrop);
        document.addEventListener("keydown", onKey);

        cancelBtn.focus();
    });
}

/* Re-export icon for convenience in section modules that import from ui */
export { icon };
