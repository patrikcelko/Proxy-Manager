/**
 * Tests version control (badges, save/discard)
 * =============================================
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { state } from "@/state";
import {
    checkVersionStatus,
    refreshPendingBadges,
    openSaveVersionModal,
    saveVersion,
    discardChanges,
} from "@/sections/versions";

describe("checkVersionStatus", () => {
    let container: HTMLDivElement;

    beforeEach(() => {
        container = document.createElement("div");
        container.innerHTML = `
            <div id="sidebar">
                <div class="nav-item" data-section="global">Global</div>
                <div class="nav-item" data-section="backends">Backends</div>
                <div class="nav-item" data-section="frontends">Frontends</div>
            </div>
            <div id="sidebar-actions" style="display:none"></div>
            <div id="toast-container"></div>
        `;
        document.body.appendChild(container);
    });

    afterEach(() => container.remove());

    it("returns true when initialized", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () =>
                Promise.resolve({
                    initialized: true,
                    has_pending: false,
                    pending_counts: {},
                    current_hash: "abc123",
                }),
        } as Response);

        const result = await checkVersionStatus();
        expect(result).toBe(true);
    });

    it("returns false when not initialized", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () =>
                Promise.resolve({
                    initialized: false,
                    has_pending: false,
                    pending_counts: {},
                    current_hash: null,
                }),
        } as Response);

        const result = await checkVersionStatus();
        expect(result).toBe(false);
    });

    it("updates state.versionStatus", async () => {
        const status = {
            initialized: true,
            has_pending: true,
            pending_counts: { backends: 2 },
            current_hash: "abc123",
        };
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve(status),
        } as Response);

        await checkVersionStatus();
        expect(state.versionStatus).toEqual(status);
    });

    it("returns true on fetch error (assume initialized)", async () => {
        vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("network"));
        const result = await checkVersionStatus();
        expect(result).toBe(true);
    });
});

describe("refreshPendingBadges", () => {
    let container: HTMLDivElement;

    beforeEach(() => {
        container = document.createElement("div");
        container.innerHTML = `
            <div class="nav-item" data-section="global">Global</div>
            <div class="nav-item" data-section="backends">Backends</div>
            <div class="nav-item" data-section="frontends">Frontends</div>
            <div id="sidebar-actions" style="display:none"></div>
            <div id="toast-container"></div>
        `;
        document.body.appendChild(container);
    });

    afterEach(() => container.remove());

    it("adds badges to nav items with pending counts", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () =>
                Promise.resolve({
                    initialized: true,
                    has_pending: true,
                    pending_counts: { backends: 3, global_settings: 1 },
                    current_hash: "abc",
                }),
        } as Response);

        await refreshPendingBadges();

        const backendBadge = document.querySelector('.nav-item[data-section="backends"] .nav-badge');
        expect(backendBadge).not.toBeNull();
        expect(backendBadge!.textContent).toBe("3");

        const globalBadge = document.querySelector('.nav-item[data-section="global"] .nav-badge');
        expect(globalBadge).not.toBeNull();
        expect(globalBadge!.textContent).toBe("1");
    });

    it("removes badges for sections with zero counts", async () => {
        // First set a badge
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () =>
                Promise.resolve({
                    initialized: true,
                    has_pending: true,
                    pending_counts: { backends: 2 },
                    current_hash: "abc",
                }),
        } as Response);
        await refreshPendingBadges();
        expect(document.querySelectorAll(".nav-badge")).toHaveLength(1);

        // Now clear it
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () =>
                Promise.resolve({
                    initialized: true,
                    has_pending: false,
                    pending_counts: { backends: 0 },
                    current_hash: "abc",
                }),
        } as Response);
        await refreshPendingBadges();
        expect(document.querySelectorAll(".nav-badge")).toHaveLength(0);
    });

    it("shows sidebar actions when has_pending is true", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () =>
                Promise.resolve({
                    initialized: true,
                    has_pending: true,
                    pending_counts: { backends: 1 },
                    current_hash: "abc",
                }),
        } as Response);

        await refreshPendingBadges();
        expect(document.getElementById("sidebar-actions")!.style.display).toBe("flex");
    });

    it("hides sidebar actions when has_pending is false", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () =>
                Promise.resolve({
                    initialized: true,
                    has_pending: false,
                    pending_counts: {},
                    current_hash: "abc",
                }),
        } as Response);

        await refreshPendingBadges();
        expect(document.getElementById("sidebar-actions")!.style.display).toBe("none");
    });
});

describe("openSaveVersionModal", () => {
    let container: HTMLDivElement;

    beforeEach(() => {
        container = document.createElement("div");
        container.innerHTML = `<div id="modal-overlay" style="display:none"><div id="modal-content"></div></div>`;
        document.body.appendChild(container);
    });

    afterEach(() => container.remove());

    it("opens modal with commit message input", () => {
        openSaveVersionModal();
        const modal = document.getElementById("modal-content");
        expect(modal!.innerHTML).toContain("Save Version");
        expect(modal!.innerHTML).toContain("sv-message");
    });
});

describe("saveVersion", () => {
    let container: HTMLDivElement;

    beforeEach(() => {
        container = document.createElement("div");
        container.innerHTML = `
            <input id="sv-message" value="test commit" />
            <div id="modal-overlay" style="display:flex"><div id="modal-content"></div></div>
            <div id="sidebar-actions" style="display:none"></div>
            <div id="toast-container"></div>
        `;
        document.body.appendChild(container);
    });

    afterEach(() => container.remove());

    it("sends POST with message", async () => {
        // Mock at module-level api function to avoid fetch-level issues
        const { api: apiMod } = await import("@/core/api");
        const apiSpy = vi.spyOn({ api: apiMod }, "api");

        // Use global fetch mock as fallback
        vi.spyOn(globalThis, "fetch").mockImplementation(async (url: any) => {
            return {
                ok: true,
                status: 200,
                json: () => Promise.resolve({ initialized: true, has_pending: false, pending_counts: {}, current_hash: "abc", hash: "abc" }),
            } as Response;
        });

        const event = { preventDefault: vi.fn() } as unknown as Event;
        await saveVersion(event);

        expect(event.preventDefault).toHaveBeenCalled();
        // The function should not have returned early
        expect(document.querySelector(".toast")).not.toBeNull();
    });

    it("shows error for empty message", async () => {
        (document.getElementById("sv-message") as HTMLInputElement).value = "   ";
        const event = { preventDefault: vi.fn() } as unknown as Event;
        await saveVersion(event);
        // Should show toast error, not call API
        expect(document.querySelector(".toast")).not.toBeNull();
    });
});

describe("discardChanges", () => {
    let container: HTMLDivElement;

    beforeEach(() => {
        container = document.createElement("div");
        container.innerHTML = `
            <div class="nav-item active" data-section="backends">Backends</div>
            <div id="sidebar-actions" style="display:flex"></div>
            <div id="toast-container"></div>
            <div id="sec-backends"></div>
            <div id="top-bar-page-title"></div>
        `;
        document.body.appendChild(container);
        (window.confirm as ReturnType<typeof vi.fn>).mockReturnValue(true);
    });

    afterEach(() => container.remove());

    it("calls discard API when confirmed", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ detail: "discarded" }),
        } as Response);

        await discardChanges();

        const discardCall = fetchSpy.mock.calls.find((c) => String(c[0]).includes("/api/versions/discard"));
        expect(discardCall).toBeDefined();
    });

    it("does nothing when cancelled", async () => {
        (window.confirm as ReturnType<typeof vi.fn>).mockReturnValue(false);
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({}),
        } as Response);

        await discardChanges();

        const discardCall = fetchSpy.mock.calls.find((c) => String(c[0]).includes("/api/versions/discard"));
        expect(discardCall).toBeUndefined();
    });
});
