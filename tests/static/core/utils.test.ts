/**
 * Tests utilities
 * ===============
 *
 * Covers escHtml, escJsonAttr, safeInt, filterPresetGrid, searchPresetGrid.
 * crudSave / crudDelete are integration-level (api + modal) and tested separately.
 */

import { describe, it, expect, beforeEach } from "vitest";
import { escHtml, escJsonAttr, safeInt, filterPresetGrid, searchPresetGrid } from "@/core/utils";

/*  escHtml  */
describe("escHtml", () => {
    it("escapes HTML special chars", () => {
        expect(escHtml('<script>"xss" & more</script>')).toBe("&lt;script&gt;&quot;xss&quot; &amp; more&lt;/script&gt;");
    });

    it("returns empty string for null / undefined", () => {
        expect(escHtml(null)).toBe("");
        expect(escHtml(undefined)).toBe("");
    });

    it("coerces numbers to string", () => {
        expect(escHtml(42)).toBe("42");
    });

    it("handles empty string", () => {
        expect(escHtml("")).toBe("");
    });

    it("returns plain text unchanged", () => {
        expect(escHtml("hello world")).toBe("hello world");
    });
});

/*  escJsonAttr  */
describe("escJsonAttr", () => {
    it("escapes JSON for safe use in HTML attributes", () => {
        const obj = { name: '<b>"Hello"</b>', val: "a & b" };
        const result = escJsonAttr(obj);
        // Must not contain raw <, >, ", &, '
        expect(result).not.toContain("<");
        expect(result).not.toContain(">");
        // Must be parseable after un-escaping
        const unescaped = result.replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;/g, "'");
        expect(JSON.parse(unescaped)).toEqual(obj);
    });

    it("handles simple objects", () => {
        const result = escJsonAttr({ id: 1 });
        expect(result).toContain("1");
    });
});

/*  safeInt  */
describe("safeInt", () => {
    it("parses valid integer strings", () => {
        expect(safeInt("42")).toBe(42);
        expect(safeInt("0")).toBe(0);
        expect(safeInt("-5")).toBe(-5);
    });

    it("returns fallback for non-numeric", () => {
        expect(safeInt("abc")).toBeNull();
        expect(safeInt("abc", 10)).toBe(10);
        expect(safeInt("")).toBeNull();
    });

    it("returns fallback for null / undefined", () => {
        expect(safeInt(null)).toBeNull();
        expect(safeInt(undefined)).toBeNull();
    });

    it("handles numeric input directly", () => {
        expect(safeInt(7)).toBe(7);
    });

    it("truncates floats", () => {
        expect(safeInt("3.9")).toBe(3);
    });
});

/*  filterPresetGrid / searchPresetGrid  */
describe("filterPresetGrid", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML(
            "beforeend",
            `
      <div class="modal">
        <div class="stabs">
          <button class="stab active">All</button>
          <button class="stab">Net</button>
        </div>
        <input id="pg-search" value="old">
        <div id="pg-grid">
          <div class="dir-card" data-cat="Net" data-search-text="bind net 443">Bind</div>
          <div class="dir-card" data-cat="SSL" data-search-text="ssl cert path">SSL</div>
        </div>
      </div>
    `,
        );
    });

    it("clears search input and shows all cards for 'all'", () => {
        filterPresetGrid("pg-grid", "pg-search", "cat", "all");
        const search = document.getElementById("pg-search") as HTMLInputElement;
        expect(search.value).toBe("");
        const cards = document.querySelectorAll<HTMLElement>("#pg-grid .dir-card");
        cards.forEach((c) => expect(c.style.display).toBe(""));
    });

    it("filters by category", () => {
        filterPresetGrid("pg-grid", "pg-search", "cat", "Net");
        const cards = document.querySelectorAll<HTMLElement>("#pg-grid .dir-card");
        expect(cards[0].style.display).toBe("");
        expect(cards[1].style.display).toBe("none");
    });
});

describe("searchPresetGrid", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML(
            "beforeend",
            `
      <div class="modal">
        <div class="stabs">
          <button class="stab active">All</button>
        </div>
        <input id="sg-search" value="ssl">
        <div id="sg-grid">
          <div class="dir-card" data-cat="Net" data-search-text="bind net 443">Bind</div>
          <div class="dir-card" data-cat="SSL" data-search-text="ssl cert path">SSL</div>
        </div>
      </div>
    `,
        );
    });

    it("filters cards by search text", () => {
        searchPresetGrid("sg-grid", "sg-search", "cat");
        const cards = document.querySelectorAll<HTMLElement>("#sg-grid .dir-card");
        expect(cards[0].style.display).toBe("none"); // "bind net 443" doesn't match "ssl"
        expect(cards[1].style.display).toBe(""); // "ssl cert path" matches "ssl"
    });

    it("resets to all when query is empty", () => {
        (document.getElementById("sg-search") as HTMLInputElement).value = "";
        searchPresetGrid("sg-grid", "sg-search", "cat");
        const cards = document.querySelectorAll<HTMLElement>("#sg-grid .dir-card");
        cards.forEach((c) => expect(c.style.display).toBe(""));
    });
});
