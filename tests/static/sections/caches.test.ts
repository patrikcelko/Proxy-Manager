/**
 * Tests caches section
 * ====================
 *
 * Covers renderCachesGrid, filterCaches.
 */

import { describe, it, expect, beforeEach } from "vitest";
import { state } from "@/state";
import type { Cache } from "@/types";

import { filterCaches } from "@/sections/caches";

const makeCache = (overrides: Partial<Cache> = {}): Cache => ({
    id: 1,
    name: "test-cache",
    total_max_size: 100,
    max_object_size: 1024,
    max_age: 3600,
    process_vary: 1,
    max_secondary_entries: 10,
    comment: null,
    extra_options: null,
    ...overrides,
});

describe("filterCaches", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML(
            "beforeend",
            `
      <input id="cache-search" value="">
      <div id="caches-grid"></div>
      <div id="caches-empty" style="display:none"></div>
    `,
        );
        state.allCaches = [makeCache({ id: 1, name: "my-cache" }), makeCache({ id: 2, name: "other-cache", comment: "hot data" })];
    });

    it("filters by name", () => {
        (document.getElementById("cache-search") as HTMLInputElement).value = "other";
        filterCaches();
        const grid = document.getElementById("caches-grid")!;
        expect(grid.innerHTML).toContain("other-cache");
        expect(grid.innerHTML).not.toContain("my-cache");
    });

    it("filters by comment content", () => {
        (document.getElementById("cache-search") as HTMLInputElement).value = "hot";
        filterCaches();
        const grid = document.getElementById("caches-grid")!;
        expect(grid.innerHTML).toContain("other-cache");
    });

    it("shows all when search is empty", () => {
        (document.getElementById("cache-search") as HTMLInputElement).value = "";
        filterCaches();
        const grid = document.getElementById("caches-grid")!;
        expect(grid.innerHTML).toContain("my-cache");
        expect(grid.innerHTML).toContain("other-cache");
    });
});
