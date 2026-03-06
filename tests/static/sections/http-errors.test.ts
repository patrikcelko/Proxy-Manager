/**
 * Tests http-errors section
 * =========================
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { state } from "@/state";
import type { HttpErrorGroup, HttpErrorEntry } from "@/types";

import {
    loadHttpErrors,
    filterHttpErrors,
    openHttpErrorsModal,
    saveHttpErrors,
    deleteHttpErrors,
    openHttpErrorEntryModal,
    saveHttpErrorEntry,
    deleteHttpErrorEntry,
} from "@/sections/http-errors";

const makeEntry = (overrides: Partial<HttpErrorEntry> = {}): HttpErrorEntry => ({
    id: 1,
    status_code: 503,
    type: "content",
    value: "<h1>Service Unavailable</h1>",
    sort_order: 0,
    ...overrides,
});

const makeGroup = (overrides: Partial<HttpErrorGroup> = {}): HttpErrorGroup => ({
    id: 1,
    name: "http-errors",
    comment: null,
    extra_options: null,
    entries: [],
    ...overrides,
});

const DOM = `
  <input id="http-error-search" value="">
  <div id="http-errors-grid"></div>
  <div id="http-errors-empty" style="display:none"></div>
`;

describe("loadHttpErrors + render", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allHttpErrors = [];
    });

    it("fetches and renders http error groups", async () => {
        const items = [makeGroup({ name: "my-errors" })];
        vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items }),
        } as Response);

        await loadHttpErrors();
        expect(state.allHttpErrors).toEqual(items);
        expect(document.getElementById("http-errors-grid")!.innerHTML).toContain("my-errors");
    });

    it("shows empty state", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [] }),
        } as Response);

        await loadHttpErrors();
        expect(document.getElementById("http-errors-grid")!.innerHTML).toBe("");
        expect(document.getElementById("http-errors-empty")!.style.display).toBe("block");
    });

    it("renders entries with status codes", async () => {
        const items = [
            makeGroup({
                entries: [
                    makeEntry({ status_code: 404, type: "content", value: "<h1>Not Found</h1>" }),
                    makeEntry({ id: 2, status_code: 503, type: "file", value: "/errors/503.html" }),
                ],
            }),
        ];
        vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items }),
        } as Response);

        await loadHttpErrors();
        const grid = document.getElementById("http-errors-grid")!;
        expect(grid.innerHTML).toContain("404");
        expect(grid.innerHTML).toContain("503");
    });

    it("shows error toast on failure", async () => {
        vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new Error("http-err fail"));
        await loadHttpErrors();
        expect(document.getElementById("toast-container")!.innerHTML).toContain("http-err fail");
    });

    it("renders extra_options badge", async () => {
        const items = [makeGroup({ extra_options: "option httplog" })];
        vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items }),
        } as Response);

        await loadHttpErrors();
        const grid = document.getElementById("http-errors-grid")!;
        expect(grid.innerHTML).toContain("Extra");
    });
});

describe("filterHttpErrors", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allHttpErrors = [
            makeGroup({ id: 1, name: "web-errors", comment: "web server errors" }),
            makeGroup({
                id: 2,
                name: "api-errors",
                entries: [makeEntry({ status_code: 502 })],
            }),
        ];
    });

    it("filters by group name", () => {
        (document.getElementById("http-error-search") as HTMLInputElement).value = "api";
        filterHttpErrors();
        const grid = document.getElementById("http-errors-grid")!;
        expect(grid.innerHTML).toContain("api-errors");
        expect(grid.innerHTML).not.toContain("web-errors");
    });

    it("filters by comment", () => {
        (document.getElementById("http-error-search") as HTMLInputElement).value = "web server";
        filterHttpErrors();
        const grid = document.getElementById("http-errors-grid")!;
        expect(grid.innerHTML).toContain("web-errors");
    });

    it("filters by status code", () => {
        (document.getElementById("http-error-search") as HTMLInputElement).value = "502";
        filterHttpErrors();
        const grid = document.getElementById("http-errors-grid")!;
        expect(grid.innerHTML).toContain("api-errors");
        expect(grid.innerHTML).not.toContain("web-errors");
    });

    it("shows all when empty", () => {
        (document.getElementById("http-error-search") as HTMLInputElement).value = "";
        filterHttpErrors();
        const grid = document.getElementById("http-errors-grid")!;
        expect(grid.innerHTML).toContain("api-errors");
        expect(grid.innerHTML).toContain("web-errors");
    });
});

describe("openHttpErrorsModal", () => {
    it("opens create modal", () => {
        openHttpErrorsModal();
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("New HTTP Error");
    });

    it("opens edit modal", () => {
        openHttpErrorsModal(makeGroup({ name: "edit-errors", comment: "test comment" }));
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("Edit HTTP Error");
        expect(content.innerHTML).toContain("edit-errors");
    });
});

describe("saveHttpErrors", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        openHttpErrorsModal();
    });

    it("creates via POST", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "new-errors";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 201,
            json: () => Promise.resolve({ id: 1 }),
        } as Response);
        await saveHttpErrors(null);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/http-errors");
    });

    it("updates via PUT", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "upd-errors";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ id: 3 }),
        } as Response);
        await saveHttpErrors(3);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/http-errors/3");
        expect((fetchSpy.mock.calls[0][1] as any).method).toBe("PUT");
    });
});

describe("deleteHttpErrors", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allHttpErrors = [];
    });

    it("deletes after confirmation", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [] }),
        } as Response);
        await deleteHttpErrors(4);
        expect(fetchSpy).toHaveBeenCalledWith("/api/http-errors/4", expect.objectContaining({ method: "DELETE" }));
    });
});

describe("openHttpErrorEntryModal", () => {
    it("opens create modal", () => {
        openHttpErrorEntryModal(1);
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("New Error Entry");
    });

    it("opens edit modal with status code", () => {
        openHttpErrorEntryModal(1, makeEntry({ status_code: 404, type: "content", value: "<h1>404</h1>" }));
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("Edit Error Entry");
        expect(content.innerHTML).toContain("404");
    });
});

describe("saveHttpErrorEntry", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        openHttpErrorEntryModal(1);
    });

    it("creates via POST", async () => {
        (document.getElementById("m-status-code") as HTMLInputElement).value = "500";
        (document.getElementById("m-type") as HTMLSelectElement).value = "content";
        (document.getElementById("m-value") as HTMLTextAreaElement).value = "<h1>Error</h1>";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 201,
            json: () => Promise.resolve({ id: 1 }),
        } as Response);
        await saveHttpErrorEntry(1, null);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/http-errors/1/entries");
        const body = JSON.parse((fetchSpy.mock.calls[0][1] as any).body);
        expect(body.status_code).toBe(500);
    });

    it("updates via PUT", async () => {
        (document.getElementById("m-status-code") as HTMLInputElement).value = "503";
        (document.getElementById("m-type") as HTMLSelectElement).value = "file";
        (document.getElementById("m-value") as HTMLTextAreaElement).value = "/err/503.html";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ id: 9 }),
        } as Response);
        await saveHttpErrorEntry(1, 9);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/http-errors/1/entries/9");
    });
});

describe("deleteHttpErrorEntry", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allHttpErrors = [];
    });

    it("deletes after confirmation", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [] }),
        } as Response);
        await deleteHttpErrorEntry(3, 6);
        expect(fetchSpy).toHaveBeenCalledWith("/api/http-errors/3/entries/6", expect.objectContaining({ method: "DELETE" }));
    });
});
