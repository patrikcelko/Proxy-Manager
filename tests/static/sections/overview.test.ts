/**
 * Tests dashboard section
 * =======================
 */

import { describe, it, expect, beforeEach, vi } from "vitest";

import { loadOverview, renderFlowCanvas, drawFlowConnections } from "@/sections/overview";

const DOM = `
  <div id="overview-grid"></div>
  <div id="overview-charts"></div>
  <div id="overview-flow"></div>
`;

describe("loadOverview", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
    });

    it("renders stat cards from API data", async () => {
        vi.spyOn(globalThis, "fetch").mockImplementation((url) => {
            const u = typeof url === "string" ? url : (url as Request).url;
            if (u.includes("/api/overview")) {
                return Promise.resolve({
                    ok: true,
                    status: 200,
                    json: () =>
                        Promise.resolve({
                            global_settings: 5,
                            default_settings: 12,
                            frontends: 3,
                            backends: 4,
                            backend_servers: 8,
                            acl_rules: 6,
                            listen_blocks: 2,
                            userlists: 1,
                            resolvers: 1,
                            peers: 0,
                            mailers: 0,
                            http_errors: 1,
                            caches: 2,
                            ssl_certificates: 3,
                        }),
                } as Response);
            }
            // other API calls from renderFlowCanvas
            return Promise.resolve({
                ok: true,
                status: 200,
                json: () => Promise.resolve({ items: [] }),
            } as Response);
        });

        await loadOverview();
        const grid = document.getElementById("overview-grid")!;
        expect(grid.innerHTML).toContain("Frontends");
        expect(grid.innerHTML).toContain("Backends");
        expect(grid.innerHTML).toContain("3"); // frontends count
        expect(grid.innerHTML).toContain("4"); // backends count
        expect(grid.innerHTML).toContain("Global Settings");
        expect(grid.innerHTML).toContain("Listen Blocks");
    });

    it("shows toast on error", async () => {
        vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new Error("API down"));
        await loadOverview();
        expect(document.getElementById("toast-container")!.innerHTML).toContain("API down");
    });
});

describe("renderFlowCanvas", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
    });

    it("renders flow diagram with fetched data", async () => {
        vi.spyOn(globalThis, "fetch").mockImplementation((url) => {
            const u = typeof url === "string" ? url : (url as Request).url;
            if (u.includes("/api/frontends")) {
                return Promise.resolve({
                    ok: true,
                    status: 200,
                    json: () =>
                        Promise.resolve({
                            items: [{ id: 1, name: "fe-web", mode: "http", default_backend: "be-web", binds: [{ bind_line: "*:80" }], options: [] }],
                        }),
                } as Response);
            }
            if (u.includes("/api/backends")) {
                return Promise.resolve({
                    ok: true,
                    status: 200,
                    json: () =>
                        Promise.resolve({
                            items: [{ id: 1, name: "be-web", balance: "roundrobin", servers: [{ name: "s1", address: "10.0.0.1", port: 80 }] }],
                        }),
                } as Response);
            }
            return Promise.resolve({
                ok: true,
                status: 200,
                json: () => Promise.resolve({ items: [] }),
            } as Response);
        });

        await renderFlowCanvas();
        const flow = document.getElementById("overview-flow")!;
        expect(flow.innerHTML).toContain("fe-web");
        expect(flow.innerHTML).toContain("be-web");
        expect(flow.innerHTML).toContain("Incoming Traffic");
        expect(flow.innerHTML).toContain("flow-diagram");
    });

    it("renders empty columns when no data", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [] }),
        } as Response);

        await renderFlowCanvas();
        const flow = document.getElementById("overview-flow")!;
        expect(flow.innerHTML).toContain("No frontends");
        expect(flow.innerHTML).toContain("No ACL rules");
    });

    it("renders listen blocks in client row", async () => {
        vi.spyOn(globalThis, "fetch").mockImplementation((url) => {
            const u = typeof url === "string" ? url : (url as Request).url;
            if (u.includes("/api/listen-blocks")) {
                return Promise.resolve({
                    ok: true,
                    status: 200,
                    json: () => Promise.resolve({ items: [{ id: 1, name: "stats", mode: "http", binds: [{ bind_line: "*:8404" }] }] }),
                } as Response);
            }
            return Promise.resolve({
                ok: true,
                status: 200,
                json: () => Promise.resolve({ items: [] }),
            } as Response);
        });

        await renderFlowCanvas();
        const flow = document.getElementById("overview-flow")!;
        expect(flow.innerHTML).toContain("stats");
    });

    it("renders auth column when userlists present", async () => {
        vi.spyOn(globalThis, "fetch").mockImplementation((url) => {
            const u = typeof url === "string" ? url : (url as Request).url;
            if (u.includes("/api/userlists")) {
                return Promise.resolve({
                    ok: true,
                    status: 200,
                    json: () => Promise.resolve({ items: [{ id: 1, name: "myusers", entries: [{ username: "admin" }] }] }),
                } as Response);
            }
            return Promise.resolve({
                ok: true,
                status: 200,
                json: () => Promise.resolve({ items: [] }),
            } as Response);
        });

        await renderFlowCanvas();
        const flow = document.getElementById("overview-flow")!;
        expect(flow.innerHTML).toContain("myusers");
        expect(flow.innerHTML).toContain("Auth");
    });
});

describe("drawFlowConnections", () => {
    it("handles missing SVG/diagram elements gracefully", () => {
        drawFlowConnections();
        // no crash
    });

    it("draws SVG paths when diagram exists", async () => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        vi.spyOn(globalThis, "fetch").mockImplementation((url) => {
            const u = typeof url === "string" ? url : (url as Request).url;
            if (u.includes("/api/frontends")) {
                return Promise.resolve({
                    ok: true,
                    status: 200,
                    json: () =>
                        Promise.resolve({
                            items: [{ id: 1, name: "fe-web", mode: "http", default_backend: "be-web", binds: [], options: [] }],
                        }),
                } as Response);
            }
            if (u.includes("/api/backends")) {
                return Promise.resolve({
                    ok: true,
                    status: 200,
                    json: () =>
                        Promise.resolve({
                            items: [{ id: 1, name: "be-web", balance: "roundrobin", servers: [{ name: "s1", address: "10.0.0.1", port: 80 }] }],
                        }),
                } as Response);
            }
            return Promise.resolve({
                ok: true,
                status: 200,
                json: () => Promise.resolve({ items: [] }),
            } as Response);
        });

        await renderFlowCanvas();
        // Wait for rAF (jsdom has mock rAF)
        drawFlowConnections();
        const svg = document.getElementById("flow-svg");
        expect(svg).not.toBeNull();
    });
});
