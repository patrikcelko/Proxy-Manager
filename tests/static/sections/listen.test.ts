/**
 * Tests listen section
 * ====================
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { state } from "@/state";
import type { ListenBlock, ListenBlockBind } from "@/types";

import {
    loadListenBlocks,
    filterListenBlocks,
    renderListenBlocks,
    openListenModal,
    applyListenPreset,
    saveListenBlock,
    deleteListenBlock,
    openListenBindModal,
    saveListenBind,
    deleteListenBind,
} from "@/sections/listen";

const makeBind = (overrides: Partial<ListenBlockBind> = {}): ListenBlockBind => ({
    id: 1,
    bind_line: "*:8404",
    sort_order: 0,
    ...overrides,
});

const makeListen = (overrides: Partial<ListenBlock> = {}): ListenBlock => ({
    id: 1,
    name: "stats",
    mode: "http",
    balance: null,
    maxconn: null,
    timeout_client: null,
    timeout_server: null,
    timeout_connect: null,
    default_server_params: null,
    option_forwardfor: false,
    option_httplog: false,
    option_tcplog: false,
    content: null,
    comment: null,
    binds: [],
    ...overrides,
});

const DOM = `
  <input id="listen-search" value="">
  <div id="listen-grid"></div>
  <div id="listen-empty" style="display:none"></div>
`;

describe("renderListenBlocks", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
    });

    it("shows empty state when no listen blocks", () => {
        renderListenBlocks([]);
        expect(document.getElementById("listen-grid")!.innerHTML).toBe("");
        expect(document.getElementById("listen-empty")!.style.display).toBe("block");
        expect(document.getElementById("listen-grid")!.style.display).toBe("none");
    });

    it("renders listen block cards", () => {
        renderListenBlocks([makeListen()]);
        const grid = document.getElementById("listen-grid")!;
        expect(grid.innerHTML).toContain("stats");
        expect(grid.style.display).toBe("grid");
    });

    it("shows mode badge in features", () => {
        renderListenBlocks([makeListen({ mode: "tcp" })]);
        const grid = document.getElementById("listen-grid")!;
        expect(grid.innerHTML).toContain("TCP");
    });

    it("shows balance badge when set", () => {
        renderListenBlocks([makeListen({ balance: "roundrobin" })]);
        const grid = document.getElementById("listen-grid")!;
        expect(grid.innerHTML).toContain("roundrobin");
    });

    it("renders bind addresses", () => {
        renderListenBlocks([makeListen({ binds: [makeBind({ bind_line: "*:3306" })] })]);
        const grid = document.getElementById("listen-grid")!;
        expect(grid.innerHTML).toContain("*:3306");
        expect(grid.innerHTML).toContain(":3306");
    });

    it("renders SSL badge on bind", () => {
        renderListenBlocks([makeListen({ binds: [makeBind({ bind_line: "*:443 ssl crt /cert" })] })]);
        const grid = document.getElementById("listen-grid")!;
        expect(grid.innerHTML).toContain("ssl");
    });

    it("renders content directives", () => {
        renderListenBlocks([makeListen({ content: "stats enable\nstats uri /stats" })]);
        const grid = document.getElementById("listen-grid")!;
        expect(grid.innerHTML).toContain("stats enable");
        expect(grid.innerHTML).toContain("stats uri /stats");
        expect(grid.innerHTML).toContain("STATS");
    });

    it("renders detail rows for timeouts and maxconn", () => {
        renderListenBlocks([
            makeListen({
                timeout_client: "30s",
                timeout_server: "30s",
                timeout_connect: "5s",
                maxconn: 1000,
            }),
        ]);
        const grid = document.getElementById("listen-grid")!;
        expect(grid.innerHTML).toContain("Client Timeout");
        expect(grid.innerHTML).toContain("Server Timeout");
        expect(grid.innerHTML).toContain("Connect Timeout");
        expect(grid.innerHTML).toContain("Max Connections");
    });

    it("renders comment", () => {
        renderListenBlocks([makeListen({ comment: "My stats dashboard" })]);
        const grid = document.getElementById("listen-grid")!;
        expect(grid.innerHTML).toContain("My stats dashboard");
    });

    it("renders feature badges for log options", () => {
        renderListenBlocks([makeListen({ option_httplog: true, option_forwardfor: true })]);
        const grid = document.getElementById("listen-grid")!;
        expect(grid.innerHTML).toContain("HTTP LOG");
        expect(grid.innerHTML).toContain("X-FWD-FOR");
    });
});

describe("filterListenBlocks", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allListenBlocks = [
            makeListen({ id: 1, name: "stats", mode: "http" }),
            makeListen({ id: 2, name: "mysql-lb", mode: "tcp", balance: "roundrobin" }),
        ];
    });

    it("filters by name", () => {
        (document.getElementById("listen-search") as HTMLInputElement).value = "mysql";
        filterListenBlocks();
        const grid = document.getElementById("listen-grid")!;
        expect(grid.innerHTML).toContain("mysql-lb");
        expect(grid.innerHTML).not.toContain("stats");
    });

    it("filters by mode", () => {
        (document.getElementById("listen-search") as HTMLInputElement).value = "tcp";
        filterListenBlocks();
        const grid = document.getElementById("listen-grid")!;
        expect(grid.innerHTML).toContain("mysql-lb");
    });

    it("shows all when empty", () => {
        (document.getElementById("listen-search") as HTMLInputElement).value = "";
        filterListenBlocks();
        const grid = document.getElementById("listen-grid")!;
        expect(grid.innerHTML).toContain("stats");
        expect(grid.innerHTML).toContain("mysql-lb");
    });
});

describe("loadListenBlocks", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allListenBlocks = [];
    });

    it("fetches and renders", async () => {
        const items = [makeListen({ name: "loaded-lb" })];
        vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items }),
        } as Response);

        await loadListenBlocks();
        expect(state.allListenBlocks).toEqual(items);
        expect(document.getElementById("listen-grid")!.innerHTML).toContain("loaded-lb");
    });

    it("shows toast on error", async () => {
        vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new Error("Net error"));
        await loadListenBlocks();
        expect(document.getElementById("toast-container")!.innerHTML).toContain("Net error");
    });
});

describe("openListenModal", () => {
    it("opens create modal with presets", () => {
        openListenModal();
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("New Listen Block");
        expect(content.innerHTML).toContain("Preset");
    });

    it("opens edit modal", () => {
        openListenModal(makeListen({ name: "edit-lb", balance: "leastconn" }));
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("Edit Listen Block");
        expect(content.innerHTML).toContain("edit-lb");
    });
});

describe("applyListenPreset", () => {
    beforeEach(() => {
        openListenModal();
    });

    it("fills form from preset", () => {
        applyListenPreset(0);
        const name = (document.getElementById("m-name") as HTMLInputElement).value;
        expect(name).toBe("HAProxy Stats Dashboard");
    });

    it("handles invalid index", () => {
        applyListenPreset(999);
        // no crash
    });
});

describe("saveListenBlock", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        openListenModal();
    });

    it("creates via POST", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "new-lb";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 201,
            json: () => Promise.resolve({ id: 1 }),
        } as Response);
        await saveListenBlock(null);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/listen-blocks");
    });

    it("updates via PUT", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "upd-lb";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ id: 5 }),
        } as Response);
        await saveListenBlock(5);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/listen-blocks/5");
        expect((fetchSpy.mock.calls[0][1] as any).method).toBe("PUT");
    });
});

describe("deleteListenBlock", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allListenBlocks = [];
    });

    it("deletes after confirmation", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [] }),
        } as Response);
        await deleteListenBlock(3);
        expect(fetchSpy).toHaveBeenCalledWith("/api/listen-blocks/3", expect.objectContaining({ method: "DELETE" }));
    });
});

describe("openListenBindModal", () => {
    it("opens create bind modal", () => {
        openListenBindModal(1);
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("Add Bind Address");
    });

    it("opens edit bind modal", () => {
        openListenBindModal(1, makeBind({ bind_line: "*:3306 ssl" }));
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("Edit Bind Address");
        expect(content.innerHTML).toContain("*:3306 ssl");
    });
});

describe("saveListenBind", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        openListenBindModal(1);
    });

    it("creates bind via POST", async () => {
        (document.getElementById("m-ln-bind-line") as HTMLInputElement).value = "*:8404";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 201,
            json: () => Promise.resolve({ id: 1 }),
        } as Response);
        await saveListenBind(1, null);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/listen-blocks/1/binds");
    });

    it("updates bind via PUT", async () => {
        (document.getElementById("m-ln-bind-line") as HTMLInputElement).value = "*:9090";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ id: 5 }),
        } as Response);
        await saveListenBind(1, 5);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/listen-blocks/1/binds/5");
    });
});

describe("deleteListenBind", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allListenBlocks = [];
    });

    it("deletes after confirmation", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [] }),
        } as Response);
        await deleteListenBind(2, 5);
        expect(fetchSpy).toHaveBeenCalledWith("/api/listen-blocks/2/binds/5", expect.objectContaining({ method: "DELETE" }));
    });
});
