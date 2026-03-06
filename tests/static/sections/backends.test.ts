/**
 * Tests backends section
 * ======================
 *
 * Covers loadBackends, renderBackends, filterBackends,
 * openBackendModal, saveBackend, deleteBackend,
 * openServerModal, saveServer, deleteServer.
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { state } from "@/state";
import type { Backend, BackendServer } from "@/types";

import {
    loadBackends,
    renderBackends,
    filterBackends,
    openBackendModal,
    saveBackend,
    deleteBackend,
    openServerModal,
    saveServer,
    deleteServer,
} from "@/sections/backends";

const makeServer = (overrides: Partial<BackendServer> = {}): BackendServer => ({
    id: 1,
    name: "web1",
    address: "10.0.0.1",
    port: 8080,
    check_enabled: true,
    ssl_enabled: false,
    ssl_verify: null,
    backup: false,
    weight: null,
    maxconn: null,
    maxqueue: null,
    inter: null,
    fastinter: null,
    downinter: null,
    rise: null,
    fall: null,
    cookie_value: null,
    send_proxy: false,
    send_proxy_v2: false,
    slowstart: null,
    resolve_prefer: null,
    resolvers_ref: null,
    on_marked_down: null,
    disabled: false,
    extra_params: null,
    sort_order: 0,
    ...overrides,
});

const makeBackend = (overrides: Partial<Backend> = {}): Backend => ({
    id: 1,
    name: "be-web",
    mode: "http",
    balance: "roundrobin",
    servers: [],
    option_forwardfor: false,
    option_redispatch: false,
    option_httplog: false,
    option_tcplog: false,
    retries: null,
    retry_on: null,
    auth_userlist: null,
    health_check_enabled: false,
    health_check_method: null,
    health_check_uri: null,
    http_check_expect: null,
    cookie: null,
    http_reuse: null,
    hash_type: null,
    timeout_server: null,
    timeout_connect: null,
    timeout_queue: null,
    compression_algo: null,
    compression_type: null,
    default_server_options: null,
    errorfile: null,
    comment: null,
    extra_options: null,
    ...overrides,
});

const DOM = `
  <input id="backend-search" value="">
  <div id="backends-grid"></div>
  <div id="backends-empty" style="display:none"></div>
`;

describe("renderBackends", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
    });

    it("shows empty state when no backends", () => {
        renderBackends([]);
        expect(document.getElementById("backends-grid")!.innerHTML).toBe("");
        expect(document.getElementById("backends-empty")!.style.display).toBe("block");
        expect(document.getElementById("backends-grid")!.style.display).toBe("none");
    });

    it("renders backend cards", () => {
        renderBackends([makeBackend()]);
        const grid = document.getElementById("backends-grid")!;
        expect(grid.innerHTML).toContain("be-web");
        expect(grid.style.display).toBe("grid");
        expect(document.getElementById("backends-empty")!.style.display).toBe("none");
    });

    it("renders multiple backends", () => {
        renderBackends([makeBackend({ id: 1, name: "be-web" }), makeBackend({ id: 2, name: "be-api" })]);
        const grid = document.getElementById("backends-grid")!;
        expect(grid.innerHTML).toContain("be-web");
        expect(grid.innerHTML).toContain("be-api");
    });

    it("renders server sub-cards", () => {
        const srv = makeServer({ name: "web1", address: "10.0.0.1", port: 8080 });
        renderBackends([makeBackend({ servers: [srv] })]);
        const grid = document.getElementById("backends-grid")!;
        expect(grid.innerHTML).toContain("web1");
        expect(grid.innerHTML).toContain("10.0.0.1");
        expect(grid.innerHTML).toContain("8080");
    });

    it("shows feature badges for options", () => {
        renderBackends([
            makeBackend({
                option_forwardfor: true,
                option_httplog: true,
                health_check_enabled: true,
                cookie: "SRVID insert",
                http_reuse: "aggressive",
                compression_algo: "gzip",
            }),
        ]);
        const grid = document.getElementById("backends-grid")!;
        expect(grid.innerHTML).toContain("X-Fwd-For");
        expect(grid.innerHTML).toContain("HTTP Log");
        expect(grid.innerHTML).toContain("Health");
        expect(grid.innerHTML).toContain("Cookie");
        expect(grid.innerHTML).toContain("Reuse");
        expect(grid.innerHTML).toContain("Compress");
    });

    it("renders detail rows for timeouts and settings", () => {
        renderBackends([
            makeBackend({
                timeout_server: "30s",
                timeout_connect: "5s",
                cookie: "SRVID insert",
                hash_type: "consistent",
            }),
        ]);
        const grid = document.getElementById("backends-grid")!;
        expect(grid.innerHTML).toContain("Server Timeout");
        expect(grid.innerHTML).toContain("30s");
        expect(grid.innerHTML).toContain("Connect Timeout");
        expect(grid.innerHTML).toContain("5s");
        expect(grid.innerHTML).toContain("consistent");
    });

    it("renders server badges for check, ssl, backup, weight, disabled", () => {
        renderBackends([
            makeBackend({
                servers: [
                    makeServer({
                        check_enabled: true,
                        ssl_enabled: true,
                        backup: true,
                        weight: 150,
                        maxconn: 256,
                        disabled: true,
                    }),
                ],
            }),
        ]);
        const grid = document.getElementById("backends-grid")!;
        expect(grid.innerHTML).toContain("badge-ok");
        expect(grid.innerHTML).toContain("badge-info");
        expect(grid.innerHTML).toContain("badge-warn");
        expect(grid.innerHTML).toContain("w:150");
        expect(grid.innerHTML).toContain("mc:256");
        expect(grid.innerHTML).toContain("badge-danger");
    });

    it("renders extra_options and comment", () => {
        renderBackends([makeBackend({ extra_options: "stick-table type ip", comment: "My backend" })]);
        const grid = document.getElementById("backends-grid")!;
        expect(grid.innerHTML).toContain("Stick Table");
        expect(grid.innerHTML).toContain("My backend");
    });

    it("renders auth userlist badge", () => {
        renderBackends([makeBackend({ auth_userlist: "myusers" })]);
        const grid = document.getElementById("backends-grid")!;
        expect(grid.innerHTML).toContain("myusers");
    });
});

describe("filterBackends", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allBackends = [makeBackend({ id: 1, name: "be-web", mode: "http" }), makeBackend({ id: 2, name: "be-api", mode: "tcp", balance: "leastconn" })];
    });

    it("filters by name", () => {
        (document.getElementById("backend-search") as HTMLInputElement).value = "api";
        filterBackends();
        const grid = document.getElementById("backends-grid")!;
        expect(grid.innerHTML).toContain("be-api");
        expect(grid.innerHTML).not.toContain("be-web");
    });

    it("filters by mode", () => {
        (document.getElementById("backend-search") as HTMLInputElement).value = "tcp";
        filterBackends();
        const grid = document.getElementById("backends-grid")!;
        expect(grid.innerHTML).toContain("be-api");
        expect(grid.innerHTML).not.toContain("be-web");
    });

    it("shows all when search is empty", () => {
        (document.getElementById("backend-search") as HTMLInputElement).value = "";
        filterBackends();
        const grid = document.getElementById("backends-grid")!;
        expect(grid.innerHTML).toContain("be-web");
        expect(grid.innerHTML).toContain("be-api");
    });
});

describe("loadBackends", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allBackends = [];
    });

    it("fetches and renders backends", async () => {
        const items = [makeBackend({ name: "loaded-be" })];
        vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items }),
        } as Response);

        await loadBackends();
        expect(state.allBackends).toEqual(items);
        expect(document.getElementById("backends-grid")!.innerHTML).toContain("loaded-be");
    });

    it("shows toast on error", async () => {
        vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new Error("Network fail"));
        await loadBackends();
        expect(document.getElementById("toast-container")!.innerHTML).toContain("Network fail");
    });
});

describe("openBackendModal", () => {
    it("opens create modal", () => {
        state.cachedUserlists = [];
        openBackendModal();
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("New Backend");
        expect(document.getElementById("modal-overlay")!.classList.contains("show")).toBe(true);
    });

    it("opens edit modal with existing data", () => {
        state.cachedUserlists = [];
        openBackendModal(makeBackend({ name: "edit-be", balance: "leastconn", cookie: "SRVID" }));
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("Edit Backend");
        expect(content.innerHTML).toContain("edit-be");
        expect(content.innerHTML).toContain("SRVID");
    });
});

describe("saveBackend", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.cachedUserlists = [];
        openBackendModal();
    });

    it("creates a new backend via POST", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "new-be";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 201,
            json: () => Promise.resolve({ id: 1, name: "new-be" }),
        } as Response);

        await saveBackend(null);
        const call = fetchSpy.mock.calls[0];
        expect(call[0]).toBe("/api/backends");
        expect(JSON.parse((call[1] as any).body).name).toBe("new-be");
    });

    it("updates an existing backend via PUT", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "upd-be";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ id: 5, name: "upd-be" }),
        } as Response);

        await saveBackend(5);
        const call = fetchSpy.mock.calls[0];
        expect(call[0]).toBe("/api/backends/5");
        expect((call[1] as any).method).toBe("PUT");
    });
});

describe("deleteBackend", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allBackends = [];
    });

    it("deletes after confirmation", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [] }),
        } as Response);

        await deleteBackend(3);
        expect(fetchSpy).toHaveBeenCalledWith("/api/backends/3", expect.objectContaining({ method: "DELETE" }));
    });
});

describe("openServerModal", () => {
    it("opens create server modal", () => {
        openServerModal(1);
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("New Server");
    });

    it("opens edit server modal with existing data", () => {
        openServerModal(1, makeServer({ name: "srv-edit", address: "192.168.1.1", port: 443 }));
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("Edit Server");
        expect(content.innerHTML).toContain("srv-edit");
        expect(content.innerHTML).toContain("192.168.1.1");
    });
});

describe("saveServer", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        openServerModal(1);
    });

    it("creates a new server via POST", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "new-srv";
        (document.getElementById("m-address") as HTMLInputElement).value = "10.0.0.5";
        (document.getElementById("m-port") as HTMLInputElement).value = "8080";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 201,
            json: () => Promise.resolve({ id: 1 }),
        } as Response);

        await saveServer(1, null);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/backends/1/servers");
    });

    it("updates an existing server via PUT", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "upd-srv";
        (document.getElementById("m-address") as HTMLInputElement).value = "10.0.0.6";
        (document.getElementById("m-port") as HTMLInputElement).value = "9090";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ id: 7 }),
        } as Response);

        await saveServer(1, 7);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/backends/1/servers/7");
        expect((fetchSpy.mock.calls[0][1] as any).method).toBe("PUT");
    });
});

describe("deleteServer", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allBackends = [];
    });

    it("deletes after confirmation", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [] }),
        } as Response);

        await deleteServer(2, 5);
        expect(fetchSpy).toHaveBeenCalledWith("/api/backends/2/servers/5", expect.objectContaining({ method: "DELETE" }));
    });
});
