/**
 * Tests version history section
 * =============================
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { loadHistory, toggleHistoryDiff, rollbackVersion } from "@/sections/history";

describe("loadHistory", () => {
    let container: HTMLDivElement;

    beforeEach(() => {
        container = document.createElement("div");
        container.innerHTML = `<div id="history-list"></div><div id="toast-container"></div>`;
        document.body.appendChild(container);
    });

    afterEach(() => container.remove());

    it("renders version cards", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () =>
                Promise.resolve({
                    items: [
                        {
                            hash: "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
                            message: "Initial config",
                            user_name: "Admin",
                            created_at: new Date().toISOString(),
                            parent_hash: null,
                        },
                    ],
                    total: 1,
                }),
        } as Response);

        await loadHistory();

        const list = document.getElementById("history-list")!;
        expect(list.querySelectorAll(".history-card")).toHaveLength(1);
        expect(list.innerHTML).toContain("abcdef12");
        expect(list.innerHTML).toContain("Initial config");
        expect(list.innerHTML).toContain("Admin");
    });

    it("shows empty state when no versions", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [], total: 0 }),
        } as Response);

        await loadHistory();

        const list = document.getElementById("history-list")!;
        expect(list.innerHTML).toContain("No versions yet");
    });

    it("shows loading state initially", async () => {
        let resolvePromise: (val: any) => void;
        const pending = new Promise((res) => { resolvePromise = res; });

        vi.spyOn(globalThis, "fetch").mockReturnValue(
            pending as Promise<Response>
        );

        const loadPromise = loadHistory();
        expect(document.getElementById("history-list")!.innerHTML).toContain("Loading history");

        resolvePromise!({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [], total: 0 }),
        });
        await loadPromise;
    });

    it("shows error on API failure", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: false,
            status: 500,
            json: () => Promise.resolve({ detail: "Internal error" }),
        } as Response);

        await loadHistory();

        const list = document.getElementById("history-list")!;
        expect(list.innerHTML).toContain("error");
    });

    it("marks first version as Latest", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () =>
                Promise.resolve({
                    items: [
                        { hash: "a".repeat(64), message: "v2", user_name: "A", created_at: new Date().toISOString(), parent_hash: "b".repeat(64) },
                        { hash: "b".repeat(64), message: "v1", user_name: "A", created_at: new Date().toISOString(), parent_hash: null },
                    ],
                    total: 2,
                }),
        } as Response);

        await loadHistory();

        const cards = document.querySelectorAll(".history-card");
        expect(cards).toHaveLength(2);
        // First card should have Latest badge
        expect(cards[0].innerHTML).toContain("Latest");
        // Second card should have rollback button
        expect(cards[1].innerHTML).toContain("Rollback");
    });
});

describe("toggleHistoryDiff", () => {
    let container: HTMLDivElement;
    const hash = "a".repeat(64);

    beforeEach(() => {
        container = document.createElement("div");
        container.innerHTML = `
            <div class="history-card" data-hash="${hash}">
                <div class="history-header"></div>
                <div class="history-diff" id="diff-${hash}" style="display:none">
                    <div class="diff-loading">Loading diff…</div>
                </div>
            </div>
            <div id="toast-container"></div>
        `;
        document.body.appendChild(container);
    });

    afterEach(() => container.remove());

    it("opens diff panel and fetches detail", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () =>
                Promise.resolve({
                    hash,
                    message: "test",
                    user_name: "Admin",
                    created_at: new Date().toISOString(),
                    diff: {
                        backends: {
                            created: [{ name: "be_new" }],
                            deleted: [],
                            updated: [],
                            total: 1,
                        },
                    },
                }),
        } as Response);

        await toggleHistoryDiff(hash);

        const card = document.querySelector(".history-card");
        expect(card!.classList.contains("open")).toBe(true);

        const diffEl = document.getElementById(`diff-${hash}`)!;
        expect(diffEl.style.display).toBe("block");
        expect(diffEl.innerHTML).toContain("Backends");
        expect(diffEl.innerHTML).toContain("be_new");
    });

    it("closes diff panel on second toggle", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () =>
                Promise.resolve({
                    hash,
                    message: "test",
                    user_name: "Admin",
                    created_at: new Date().toISOString(),
                    diff: {},
                }),
        } as Response);

        await toggleHistoryDiff(hash); // Open
        await toggleHistoryDiff(hash); // Close

        const card = document.querySelector(".history-card");
        expect(card!.classList.contains("open")).toBe(false);
    });
});

describe("rollbackVersion", () => {
    let container: HTMLDivElement;
    const hash = "b".repeat(64);

    beforeEach(() => {
        container = document.createElement("div");
        container.innerHTML = `
            <div id="history-list"></div>
            <div id="sidebar-actions" style="display:none"></div>
            <div id="toast-container"></div>
        `;
        document.body.appendChild(container);
        (window.confirm as ReturnType<typeof vi.fn>).mockReturnValue(true);
    });

    afterEach(() => container.remove());

    it("calls rollback API when confirmed", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () =>
                Promise.resolve({
                    hash: "c".repeat(64),
                    message: "Rollback to bbbbbbb",
                    items: [],
                    total: 0,
                }),
        } as Response);

        await rollbackVersion(hash);

        const rollbackCall = fetchSpy.mock.calls.find((c) =>
            String(c[0]).includes(`/api/versions/${hash}/rollback`)
        );
        expect(rollbackCall).toBeDefined();
    });

    it("does nothing when cancelled", async () => {
        (window.confirm as ReturnType<typeof vi.fn>).mockReturnValue(false);
        const fetchSpy = vi.spyOn(globalThis, "fetch");
        await rollbackVersion(hash);
        expect(fetchSpy).not.toHaveBeenCalled();
    });
});
