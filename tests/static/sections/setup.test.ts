/**
 * Tests first-time setup
 * =======================
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { showSetup, initEmpty } from "@/sections/setup";

describe("showSetup", () => {
    let container: HTMLDivElement;

    beforeEach(() => {
        container = document.createElement("div");
        container.innerHTML = `
            <div id="setup-overlay" style="display:none"></div>
            <div id="app-layout" style="display:flex"></div>
            <div id="app-footer" style="display:flex"></div>
        `;
        document.body.appendChild(container);
    });

    afterEach(() => container.remove());

    it("shows overlay and hides app layout", () => {
        showSetup();

        expect(document.getElementById("setup-overlay")!.style.display).toBe("flex");
        expect(document.getElementById("app-layout")!.style.display).toBe("none");
        expect(document.getElementById("app-footer")!.style.display).toBe("none");
    });
});

describe("initEmpty", () => {
    let container: HTMLDivElement;

    beforeEach(() => {
        container = document.createElement("div");
        container.innerHTML = `
            <div id="setup-overlay" style="display:flex"></div>
            <div id="auth-overlay" style="display:none"></div>
            <div id="app-layout" style="display:none"></div>
            <div id="app-footer" style="display:none"></div>
            <div id="sidebar-actions" style="display:none"></div>
            <div id="toast-container"></div>
            <div id="top-bar-user"></div>
            <div id="user-dropdown"></div>
            <div id="user-name"></div>
            <div id="user-avatar"></div>
            <div id="dropdown-user-name"></div>
            <div id="dropdown-user-email"></div>
        `;
        document.body.appendChild(container);
    });

    afterEach(() => container.remove());

    it("calls init/empty API", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ detail: "Initialized" }),
        } as Response);

        await initEmpty();

        const initCall = fetchSpy.mock.calls.find((c) =>
            String(c[0]).includes("/api/versions/init/empty")
        );
        expect(initCall).toBeDefined();
    });

    it("shows toast on error", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: false,
            status: 500,
            json: () => Promise.resolve({ detail: "Server error" }),
        } as Response);

        await initEmpty();

        expect(document.querySelector(".toast")).not.toBeNull();
    });
});
