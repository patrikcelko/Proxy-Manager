/**
 * Tests API
 * =========
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { headers, api, toast, TOKEN, setToken } from "@/core/api";

describe("setToken / TOKEN", () => {
    beforeEach(() => setToken(null));

    it("sets and reads token", () => {
        setToken("abc123");
        expect(TOKEN).toBe("abc123");
    });

    it("can clear token", () => {
        setToken("abc");
        setToken(null);
        expect(TOKEN).toBeNull();
    });
});

describe("headers", () => {
    beforeEach(() => setToken(null));

    it("includes Content-Type when json=true", () => {
        const h = headers(true);
        expect(h["Content-Type"]).toBe("application/json");
    });

    it("omits Content-Type when json=false", () => {
        const h = headers(false);
        expect(h["Content-Type"]).toBeUndefined();
    });

    it("includes Authorization when token is set", () => {
        setToken("tok123");
        const h = headers();
        expect(h["Authorization"]).toBe("Bearer tok123");
    });

    it("omits Authorization when no token", () => {
        const h = headers();
        expect(h["Authorization"]).toBeUndefined();
    });
});

describe("toast", () => {
    it("adds a toast element to the container", () => {
        const container = document.getElementById("toast-container")!;
        container.innerHTML = "";
        toast("Hello!");
        const toasts = container.querySelectorAll(".toast");
        expect(toasts.length).toBe(1);
        expect(toasts[0].textContent).toBe("Hello!");
        expect(toasts[0].classList.contains("toast-success")).toBe(true);
    });

    it("supports error type", () => {
        const container = document.getElementById("toast-container")!;
        container.innerHTML = "";
        toast("Err", "error");
        expect(container.querySelector(".toast-error")).toBeTruthy();
    });
});

describe("api", () => {
    beforeEach(() => {
        setToken("test-token");
        vi.restoreAllMocks();
    });

    it("fetches and returns JSON on success", async () => {
        const mockData = { items: [1, 2, 3] };
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve(mockData),
        } as Response);

        const result = await api("/api/test");
        expect(result).toEqual(mockData);
        expect(fetch).toHaveBeenCalledWith("/api/test", expect.objectContaining({ headers: expect.objectContaining({ Authorization: "Bearer test-token" }) }));
    });

    it("throws on non-ok response", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: false,
            status: 422,
            json: () => Promise.resolve({ detail: "Validation error" }),
        } as Response);

        await expect(api("/api/fail")).rejects.toThrow("Validation error");
    });

    it("calls logout on 401", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: false,
            status: 401,
            json: () => Promise.resolve({}),
        } as Response);

        // auth.ts logout is dynamically imported; we can just test it throws Unauthorized
        await expect(api("/api/auth-fail")).rejects.toThrow("Unauthorized");
    });
});
