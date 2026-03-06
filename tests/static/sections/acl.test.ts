/**
 * Tests ACL section
 * =================
 *
 * Covers renderAclTable, filterAclTable.
 */

import { describe, it, expect, beforeEach } from "vitest";
import { state } from "@/state";
import type { AclRule } from "@/types";
import { renderAclTable, filterAclTable } from "@/sections/acl";

const makeAcl = (overrides: Partial<AclRule> = {}): AclRule => ({
    id: 1,
    domain: "example.com",
    acl_match_type: "hdr",
    frontend_id: 1,
    backend_name: "web-backend",
    sort_order: 0,
    ...overrides,
});

describe("renderAclTable", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML(
            "beforeend",
            `
      <div id="acl-table-wrap">
        <table id="acl-table"><tbody></tbody></table>
      </div>
      <div id="acl-empty" style="display:none"></div>
    `,
        );
        state.allBackends = [{ id: 1, name: "web-backend", mode: "http" }] as any[];
    });

    it("shows empty state when no ACL rules", () => {
        renderAclTable([]);
        expect(document.querySelector("#acl-table tbody")!.innerHTML).toBe("");
        expect(document.getElementById("acl-empty")!.style.display).toBe("block");
    });

    it("renders ACL rows", () => {
        renderAclTable([makeAcl()]);
        const body = document.querySelector("#acl-table tbody") as HTMLElement;
        expect(body.innerHTML).toContain("example.com");
    });

    it("renders multiple rows", () => {
        renderAclTable([makeAcl({ id: 1, domain: "a.com" }), makeAcl({ id: 2, domain: "b.com" })]);
        expect(document.querySelector("#acl-table tbody")!.innerHTML).toContain("a.com");
        expect(document.querySelector("#acl-table tbody")!.innerHTML).toContain("b.com");
    });
});

describe("filterAclTable", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML(
            "beforeend",
            `
      <input id="acl-search" value="">
      <div id="acl-table-wrap">
        <table id="acl-table"><tbody></tbody></table>
      </div>
      <div id="acl-empty" style="display:none"></div>
    `,
        );
        state.allAclRules = [makeAcl({ id: 1, domain: "example.com" }), makeAcl({ id: 2, domain: "other.org" })];
        state.allBackends = [{ id: 1, name: "app", mode: "http" }] as any[];
    });

    it("filters by domain query", () => {
        (document.getElementById("acl-search") as HTMLInputElement).value = "other";
        filterAclTable();
        const body = document.querySelector("#acl-table tbody") as HTMLElement;
        expect(body.innerHTML).not.toContain("example.com");
        expect(body.innerHTML).toContain("other.org");
    });

    it("shows all when search is empty", () => {
        (document.getElementById("acl-search") as HTMLInputElement).value = "";
        filterAclTable();
        const body = document.querySelector("#acl-table tbody") as HTMLElement;
        expect(body.innerHTML).toContain("example.com");
        expect(body.innerHTML).toContain("other.org");
    });
});
