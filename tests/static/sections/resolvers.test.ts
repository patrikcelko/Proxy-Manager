/**
 * Tests resolvers section
 * =======================
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { state } from "@/state";
import type { Resolver, Nameserver } from "@/types";

import {
    loadResolvers,
    filterResolvers,
    openResolverModal,
    saveResolver,
    deleteResolver,
    openNameserverModal,
    saveNameserver,
    deleteNameserver,
} from "@/sections/resolvers";

const makeNs = (overrides: Partial<Nameserver> = {}): Nameserver => ({
    id: 1,
    name: "dns1",
    address: "8.8.8.8",
    port: 53,
    sort_order: 0,
    ...overrides,
});

const makeResolver = (overrides: Partial<Resolver> = {}): Resolver => ({
    id: 1,
    name: "mydns",
    comment: null,
    resolve_retries: null,
    timeout_resolve: null,
    timeout_retry: null,
    hold_valid: null,
    hold_nx: null,
    hold_other: null,
    hold_obsolete: null,
    hold_timeout: null,
    hold_refused: null,
    hold_aa: null,
    accepted_payload_size: null,
    parse_resolv_conf: null,
    extra_options: null,
    nameservers: [],
    ...overrides,
});

const DOM = `
  <input id="resolver-search" value="">
  <div id="resolvers-grid"></div>
  <div id="resolvers-empty" style="display:none"></div>
`;

describe("loadResolvers", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allResolvers = [];
    });

    it("fetches and renders resolvers", async () => {
        const items = [makeResolver({ name: "loaded-dns" })];
        vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items }),
        } as Response);

        await loadResolvers();
        expect(state.allResolvers).toEqual(items);
        expect(document.getElementById("resolvers-grid")!.innerHTML).toContain("loaded-dns");
    });

    it("shows toast on error", async () => {
        vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new Error("DNS error"));
        await loadResolvers();
        expect(document.getElementById("toast-container")!.innerHTML).toContain("DNS error");
    });
});

describe("filterResolvers (render empty / populated)", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allResolvers = [
            makeResolver({ id: 1, name: "primary-dns", comment: "main resolver" }),
            makeResolver({ id: 2, name: "backup-dns", nameservers: [makeNs({ name: "cf-dns", address: "1.1.1.1" })] }),
        ];
    });

    it("shows empty grid when no resolvers", () => {
        state.allResolvers = [];
        (document.getElementById("resolver-search") as HTMLInputElement).value = "";
        filterResolvers();
        expect(document.getElementById("resolvers-grid")!.innerHTML).toBe("");
        expect(document.getElementById("resolvers-empty")!.style.display).toBe("block");
    });

    it("renders resolver cards", () => {
        (document.getElementById("resolver-search") as HTMLInputElement).value = "";
        filterResolvers();
        const grid = document.getElementById("resolvers-grid")!;
        expect(grid.innerHTML).toContain("primary-dns");
        expect(grid.innerHTML).toContain("backup-dns");
        expect(grid.style.display).toBe("grid");
    });

    it("filters by name", () => {
        (document.getElementById("resolver-search") as HTMLInputElement).value = "primary";
        filterResolvers();
        const grid = document.getElementById("resolvers-grid")!;
        expect(grid.innerHTML).toContain("primary-dns");
        expect(grid.innerHTML).not.toContain("backup-dns");
    });

    it("filters by comment", () => {
        (document.getElementById("resolver-search") as HTMLInputElement).value = "main resolver";
        filterResolvers();
        const grid = document.getElementById("resolvers-grid")!;
        expect(grid.innerHTML).toContain("primary-dns");
    });

    it("filters by nameserver name", () => {
        (document.getElementById("resolver-search") as HTMLInputElement).value = "cf-dns";
        filterResolvers();
        const grid = document.getElementById("resolvers-grid")!;
        expect(grid.innerHTML).toContain("backup-dns");
        expect(grid.innerHTML).not.toContain("primary-dns");
    });

    it("renders nameserver entries", () => {
        (document.getElementById("resolver-search") as HTMLInputElement).value = "";
        filterResolvers();
        const grid = document.getElementById("resolvers-grid")!;
        expect(grid.innerHTML).toContain("cf-dns");
        expect(grid.innerHTML).toContain("1.1.1.1");
    });

    it("renders feature badges for timeouts and hold timers", () => {
        state.allResolvers = [
            makeResolver({
                timeout_resolve: "1s",
                timeout_retry: "500ms",
                hold_valid: "10s",
                hold_nx: "30s",
                accepted_payload_size: 8192,
                parse_resolv_conf: 1,
            }),
        ];
        (document.getElementById("resolver-search") as HTMLInputElement).value = "";
        filterResolvers();
        const grid = document.getElementById("resolvers-grid")!;
        expect(grid.innerHTML).toContain("resolve: 1s");
        expect(grid.innerHTML).toContain("payload: 8192");
        expect(grid.innerHTML).toContain("resolv.conf");
        expect(grid.innerHTML).toContain("hold timer");
    });
});

describe("openResolverModal", () => {
    it("opens create modal", () => {
        openResolverModal();
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("New DNS Resolver");
    });

    it("opens edit modal with existing data", () => {
        openResolverModal(makeResolver({ name: "edit-dns", timeout_resolve: "2s" }));
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("Edit DNS Resolver");
        expect(content.innerHTML).toContain("edit-dns");
    });
});

describe("saveResolver", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        openResolverModal();
    });

    it("creates via POST", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "new-dns";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 201,
            json: () => Promise.resolve({ id: 1 }),
        } as Response);
        await saveResolver(null);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/resolvers");
    });

    it("updates via PUT", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "upd-dns";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ id: 5 }),
        } as Response);
        await saveResolver(5);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/resolvers/5");
        expect((fetchSpy.mock.calls[0][1] as any).method).toBe("PUT");
    });
});

describe("deleteResolver", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allResolvers = [];
    });

    it("deletes after confirmation", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [] }),
        } as Response);
        await deleteResolver(3);
        expect(fetchSpy).toHaveBeenCalledWith("/api/resolvers/3", expect.objectContaining({ method: "DELETE" }));
    });
});

describe("openNameserverModal", () => {
    it("opens create modal", () => {
        openNameserverModal(1);
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("New Nameserver");
    });

    it("opens edit modal", () => {
        openNameserverModal(1, makeNs({ name: "edit-ns", address: "1.0.0.1" }));
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("Edit Nameserver");
        expect(content.innerHTML).toContain("edit-ns");
    });
});

describe("saveNameserver", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        openNameserverModal(1);
    });

    it("creates via POST", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "new-ns";
        (document.getElementById("m-address") as HTMLInputElement).value = "8.8.4.4";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 201,
            json: () => Promise.resolve({ id: 1 }),
        } as Response);
        await saveNameserver(1, null);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/resolvers/1/nameservers");
    });

    it("updates via PUT", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "upd-ns";
        (document.getElementById("m-address") as HTMLInputElement).value = "1.1.1.1";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ id: 7 }),
        } as Response);
        await saveNameserver(1, 7);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/resolvers/1/nameservers/7");
    });
});

describe("deleteNameserver", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allResolvers = [];
    });

    it("deletes after confirmation", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [] }),
        } as Response);
        await deleteNameserver(2, 5);
        expect(fetchSpy).toHaveBeenCalledWith("/api/resolvers/2/nameservers/5", expect.objectContaining({ method: "DELETE" }));
    });
});
