/**
 * Tests version history section
 * =============================
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { loadHistory, toggleHistoryDiff, rollbackVersion, switchDiffTab, renderDiffContent } from "@/sections/history";

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

describe("renderDiffContent", () => {
    it("renders tabbed diff with Changes and Diff tabs", () => {
        const diff = {
            backends: {
                created: [{ name: "new_be" }],
                deleted: [{ name: "old_be" }],
                updated: [
                    { entity: "web", old: { mode: "http" }, new: { mode: "tcp" }, changes: [{ field: "mode", old: "http", new: "tcp" }] },
                ],
                total: 3,
            },
        };

        const html = renderDiffContent(diff, "test-diff");
        const wrap = document.createElement("div");
        wrap.innerHTML = html;

        // Has tab bar with two buttons
        const tabs = wrap.querySelectorAll(".dtab-btn");
        expect(tabs).toHaveLength(2);
        expect(tabs[0].textContent).toContain("Changes");
        expect(tabs[1].textContent).toContain("Diff");

        // Has two panes
        const panes = wrap.querySelectorAll(".dtab-pane");
        expect(panes).toHaveLength(2);

        // Changes pane is visible by default
        expect((panes[0] as HTMLElement).style.display).toBe("block");
        expect((panes[1] as HTMLElement).style.display).toBe("none");

        // Summary stats present
        expect(wrap.querySelector(".dtab-s-add")).not.toBeNull();
        expect(wrap.querySelector(".dtab-s-del")).not.toBeNull();
    });

    it("uses SVG arrow icon instead of text arrow in field changes", () => {
        const diff = {
            backends: {
                created: [],
                deleted: [],
                updated: [
                    { entity: "web", old: { mode: "http" }, new: { mode: "tcp" }, changes: [{ field: "mode", old: "http", new: "tcp" }] },
                ],
                total: 1,
            },
        };

        const html = renderDiffContent(diff, "arrow-test");
        const wrap = document.createElement("div");
        wrap.innerHTML = html;

        const changesPane = wrap.querySelector(".dtab-pane[data-tab='changes']") as HTMLElement;
        const arrow = changesPane.querySelector(".diff-arrow");
        expect(arrow).not.toBeNull();
        // Should contain an SVG element, not a text arrow
        expect(arrow!.querySelector("svg")).not.toBeNull();
        expect(arrow!.innerHTML).toContain("arrow-right-narrow");
    });

    it("shows empty state for empty diff", () => {
        const html = renderDiffContent({}, "empty-test");
        expect(html).toContain("No changes");
    });

    it("renders unified diff with +/- lines", () => {
        const diff = {
            frontends: {
                created: [],
                deleted: [],
                updated: [
                    { entity: "http", old: { mode: "http" }, new: { mode: "tcp" }, changes: [{ field: "mode", old: "http", new: "tcp" }] },
                ],
                total: 1,
            },
        };

        const html = renderDiffContent(diff, "ud-test");
        const wrap = document.createElement("div");
        wrap.innerHTML = html;

        // Unified diff pane has ud-section elements
        const udPane = wrap.querySelectorAll(".dtab-pane")[1] as HTMLElement;
        expect(udPane.querySelector(".ud-section")).not.toBeNull();
        expect(udPane.querySelector(".ud-file-header")!.textContent).toContain("Frontends");

        // Has add and del lines
        expect(udPane.querySelector(".ud-del")).not.toBeNull();
        expect(udPane.querySelector(".ud-add")).not.toBeNull();
    });
});

describe("switchDiffTab", () => {
    let container: HTMLDivElement;

    beforeEach(() => {
        container = document.createElement("div");
        container.innerHTML = `
            <div class="dtab-wrap" id="test-tabs">
                <div class="dtab-bar">
                    <button class="dtab-btn active" data-tab="changes">Changes</button>
                    <button class="dtab-btn" data-tab="diff">Diff</button>
                </div>
                <div class="dtab-pane" data-tab="changes" style="display:block">Changes content</div>
                <div class="dtab-pane" data-tab="diff" style="display:none">Diff content</div>
            </div>`;
        document.body.appendChild(container);
    });

    afterEach(() => container.remove());

    it("switches to diff tab", () => {
        switchDiffTab("test-tabs", "diff");

        const btns = container.querySelectorAll(".dtab-btn");
        expect(btns[0].classList.contains("active")).toBe(false);
        expect(btns[1].classList.contains("active")).toBe(true);

        const panes = container.querySelectorAll<HTMLElement>(".dtab-pane");
        expect(panes[0].style.display).toBe("none");
        expect(panes[1].style.display).toBe("block");
    });

    it("switches back to changes tab", () => {
        switchDiffTab("test-tabs", "diff");
        switchDiffTab("test-tabs", "changes");

        const panes = container.querySelectorAll<HTMLElement>(".dtab-pane");
        expect(panes[0].style.display).toBe("block");
        expect(panes[1].style.display).toBe("none");
    });
});
