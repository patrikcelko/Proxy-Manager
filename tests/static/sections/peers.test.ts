/**
 * Tests peers section
 * ===================
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { state } from "@/state";
import type { Peer, PeerEntry } from "@/types";

import {
    loadPeers,
    filterPeers,
    openPeerModal,
    savePeer,
    deletePeer,
    openPeerEntryModal,
    savePeerEntry,
    deletePeerEntry,
} from "@/sections/peers";

const makeEntry = (overrides: Partial<PeerEntry> = {}): PeerEntry => ({
    id: 1,
    name: "haproxy1",
    address: "10.0.0.1",
    port: 10000,
    sort_order: 0,
    ...overrides,
});

const makePeer = (overrides: Partial<Peer> = {}): Peer => ({
    id: 1,
    name: "mypeers",
    comment: null,
    default_bind: null,
    default_server_options: null,
    extra_options: null,
    entries: [],
    ...overrides,
});

const DOM = `
  <input id="peer-search" value="">
  <div id="peers-grid"></div>
  <div id="peers-empty" style="display:none"></div>
`;

describe("loadPeers + render", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allPeers = [];
    });

    it("fetches and renders peers", async () => {
        const items = [makePeer({ name: "loaded-peer" })];
        vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items }),
        } as Response);

        await loadPeers();
        expect(state.allPeers).toEqual(items);
        expect(document.getElementById("peers-grid")!.innerHTML).toContain("loaded-peer");
    });

    it("shows empty state", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [] }),
        } as Response);

        await loadPeers();
        expect(document.getElementById("peers-grid")!.innerHTML).toBe("");
        expect(document.getElementById("peers-empty")!.style.display).toBe("block");
    });

    it("renders peer entries", async () => {
        const items = [makePeer({ entries: [makeEntry({ name: "node1", address: "192.168.1.1", port: 10000 })] })];
        vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items }),
        } as Response);

        await loadPeers();
        const grid = document.getElementById("peers-grid")!;
        expect(grid.innerHTML).toContain("node1");
        expect(grid.innerHTML).toContain("192.168.1.1");
    });

    it("renders feature badges", async () => {
        const items = [makePeer({ default_bind: ":10000 ssl", default_server_options: "ssl verify none", extra_options: "stick-table" })];
        vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items }),
        } as Response);

        await loadPeers();
        const grid = document.getElementById("peers-grid")!;
        expect(grid.innerHTML).toContain("Bind");
        expect(grid.innerHTML).toContain("Default Server");
        expect(grid.innerHTML).toContain("Extra Opts");
    });

    it("shows toast on error", async () => {
        vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new Error("Peer error"));
        await loadPeers();
        expect(document.getElementById("toast-container")!.innerHTML).toContain("Peer error");
    });
});

describe("filterPeers", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allPeers = [
            makePeer({ id: 1, name: "cluster-a", comment: "primary" }),
            makePeer({ id: 2, name: "cluster-b", entries: [makeEntry({ name: "node-x" })] }),
        ];
    });

    it("filters by name", () => {
        (document.getElementById("peer-search") as HTMLInputElement).value = "cluster-a";
        filterPeers();
        const grid = document.getElementById("peers-grid")!;
        expect(grid.innerHTML).toContain("cluster-a");
        expect(grid.innerHTML).not.toContain("cluster-b");
    });

    it("filters by comment", () => {
        (document.getElementById("peer-search") as HTMLInputElement).value = "primary";
        filterPeers();
        const grid = document.getElementById("peers-grid")!;
        expect(grid.innerHTML).toContain("cluster-a");
    });

    it("filters by entry name", () => {
        (document.getElementById("peer-search") as HTMLInputElement).value = "node-x";
        filterPeers();
        const grid = document.getElementById("peers-grid")!;
        expect(grid.innerHTML).toContain("cluster-b");
        expect(grid.innerHTML).not.toContain("cluster-a");
    });

    it("shows all when empty", () => {
        (document.getElementById("peer-search") as HTMLInputElement).value = "";
        filterPeers();
        const grid = document.getElementById("peers-grid")!;
        expect(grid.innerHTML).toContain("cluster-a");
        expect(grid.innerHTML).toContain("cluster-b");
    });
});

describe("openPeerModal", () => {
    it("opens create modal", () => {
        openPeerModal();
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("New Peer Section");
    });

    it("opens edit modal", () => {
        openPeerModal(makePeer({ name: "edit-peer" }));
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("Edit Peer Section");
        expect(content.innerHTML).toContain("edit-peer");
    });
});

describe("savePeer", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        openPeerModal();
    });

    it("creates via POST", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "new-peer";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 201,
            json: () => Promise.resolve({ id: 1 }),
        } as Response);
        await savePeer(null);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/peers");
    });

    it("updates via PUT", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "upd-peer";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ id: 5 }),
        } as Response);
        await savePeer(5);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/peers/5");
        expect((fetchSpy.mock.calls[0][1] as any).method).toBe("PUT");
    });
});

describe("deletePeer", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allPeers = [];
    });

    it("deletes after confirmation", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [] }),
        } as Response);
        await deletePeer(3);
        expect(fetchSpy).toHaveBeenCalledWith("/api/peers/3", expect.objectContaining({ method: "DELETE" }));
    });
});

describe("openPeerEntryModal", () => {
    it("opens create modal", () => {
        openPeerEntryModal(1);
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("New Peer Entry");
    });

    it("opens edit modal", () => {
        openPeerEntryModal(1, makeEntry({ name: "edit-node" }));
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("Edit Peer Entry");
        expect(content.innerHTML).toContain("edit-node");
    });
});

describe("savePeerEntry", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        openPeerEntryModal(1);
    });

    it("creates via POST", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "new-node";
        (document.getElementById("m-address") as HTMLInputElement).value = "10.0.0.5";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 201,
            json: () => Promise.resolve({ id: 1 }),
        } as Response);
        await savePeerEntry(1, null);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/peers/1/entries");
    });

    it("updates via PUT", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "upd-node";
        (document.getElementById("m-address") as HTMLInputElement).value = "10.0.0.6";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ id: 7 }),
        } as Response);
        await savePeerEntry(1, 7);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/peers/1/entries/7");
    });
});

describe("deletePeerEntry", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allPeers = [];
    });

    it("deletes after confirmation", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [] }),
        } as Response);
        await deletePeerEntry(2, 5);
        expect(fetchSpy).toHaveBeenCalledWith("/api/peers/2/entries/5", expect.objectContaining({ method: "DELETE" }));
    });
});
