/**
 * Tests Auth
 * ==========
 *
 * Covers logout, showApp, switchAuthTab, sidebar and user menu functions.
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { logout, showApp, switchAuthTab, toggleSidebar, closeUserMenu } from "@/core/auth";
import { setToken } from "@/core/api";
import { state } from "@/state";

describe("switchAuthTab", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML(
            "beforeend",
            `
      <button class="auth-tab active">Login</button>
      <button class="auth-tab">Register</button>
      <div id="auth-login" class="active"></div>
      <div id="auth-register"></div>
    `,
        );
    });

    it("switches to register tab", () => {
        switchAuthTab("register");
        expect(document.getElementById("auth-register")!.classList.contains("active")).toBe(true);
        expect(document.getElementById("auth-login")!.classList.contains("active")).toBe(false);
    });

    it("switches back to login tab", () => {
        switchAuthTab("register");
        switchAuthTab("login");
        expect(document.getElementById("auth-login")!.classList.contains("active")).toBe(true);
        expect(document.getElementById("auth-register")!.classList.contains("active")).toBe(false);
    });
});

describe("logout", () => {
    beforeEach(() => {
        setToken("test-token");
        localStorage.setItem("pm_token", "test-token");
    });

    it("clears token and shows auth overlay", () => {
        logout();
        const overlay = document.getElementById("auth-overlay")!;
        const layout = document.getElementById("app-layout")!;
        expect(overlay.style.display).toBe("flex");
        expect(layout.style.display).toBe("none");
    });
});

describe("toggleSidebar", () => {
    it("toggles open class on sidebar and backdrop", () => {
        const sidebar = document.getElementById("sidebar")!;
        const backdrop = document.getElementById("sidebar-backdrop")!;
        sidebar.classList.remove("open");
        backdrop.classList.remove("open");

        toggleSidebar();
        expect(sidebar.classList.contains("open")).toBe(true);
        expect(backdrop.classList.contains("open")).toBe(true);

        toggleSidebar();
        expect(sidebar.classList.contains("open")).toBe(false);
        expect(backdrop.classList.contains("open")).toBe(false);
    });
});

describe("closeUserMenu", () => {
    it("removes open class from dropdown and button", () => {
        document.getElementById("user-dropdown")!.classList.add("open");
        document.getElementById("top-bar-user")!.classList.add("open");
        closeUserMenu();
        expect(document.getElementById("user-dropdown")!.classList.contains("open")).toBe(false);
        expect(document.getElementById("top-bar-user")!.classList.contains("open")).toBe(false);
    });
});

describe("showApp", () => {
    beforeEach(() => {
        setToken("test");
        state.currentUser = null;
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ id: 1, name: "Test", email: "test@test.com" }),
        } as Response);
    });

    it("hides auth overlay and shows app layout", () => {
        showApp();
        expect(document.getElementById("auth-overlay")!.style.display).toBe("none");
        expect(document.getElementById("app-layout")!.style.display).toBe("flex");
        expect(document.getElementById("app-footer")!.style.display).toBe("block");
    });
});
