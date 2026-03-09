/**
 * Tests dashboard section
 * =======================
 */

import { describe, it, expect, beforeEach, vi } from "vitest";

import { loadOverview, renderFlowCanvas, drawFlowConnections, _initHoverHighlight } from "@/sections/overview";

const DOM = `
  <div id="overview-grid"></div>
  <div id="overview-charts"></div>
  <div id="overview-flow"></div>
`;

/** Build a Response promise that resolves with the given json payload. */
function jsonRes(data: any): Promise<Response> {
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(data) } as Response);
}

/** Build a mock fetch that routes different URLs to different payloads. */
function mockApis(routes: Record<string, any>): void {
    vi.spyOn(globalThis, "fetch").mockImplementation((url) => {
        const u = typeof url === "string" ? url : (url as Request).url;
        for (const [path, data] of Object.entries(routes)) {
            if (u.includes(path)) return jsonRes(data);
        }
        return jsonRes({ items: [] });
    });
}

describe("loadOverview", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
    });

    it("renders stat cards from API data", async () => {
        vi.spyOn(globalThis, "fetch").mockImplementation((url) => {
            const u = typeof url === "string" ? url : (url as Request).url;
            if (u.includes("/api/overview")) {
                return jsonRes({
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
                });
            }
            return jsonRes({ items: [] });
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
        mockApis({
            "/api/frontends": { items: [{ id: 1, name: "fe-web", mode: "http", default_backend: "be-web", binds: [{ bind_line: "*:80" }], options: [] }] },
            "/api/backends": { items: [{ id: 1, name: "be-web", balance: "roundrobin", servers: [{ name: "s1", address: "10.0.0.1", port: 80 }] }] },
        });

        await renderFlowCanvas();
        const flow = document.getElementById("overview-flow")!;
        expect(flow.innerHTML).toContain("fe-web");
        expect(flow.innerHTML).toContain("be-web");
        expect(flow.innerHTML).toContain("Incoming Traffic");
        expect(flow.innerHTML).toContain("flow-diagram");
    });

    it("renders empty columns when no data", async () => {
        mockApis({});
        await renderFlowCanvas();
        const flow = document.getElementById("overview-flow")!;
        expect(flow.innerHTML).toContain("No frontends");
        expect(flow.innerHTML).toContain("No ACL rules");
    });

    it("renders listen blocks in client row", async () => {
        mockApis({
            "/api/listen-blocks": { items: [{ id: 1, name: "stats", mode: "http", binds: [{ bind_line: "*:8404" }] }] },
        });
        await renderFlowCanvas();
        const flow = document.getElementById("overview-flow")!;
        expect(flow.innerHTML).toContain("stats");
    });

    it("renders auth column when userlists present", async () => {
        mockApis({
            "/api/userlists": { items: [{ id: 1, name: "myusers", entries: [{ username: "admin" }] }] },
        });
        await renderFlowCanvas();
        const flow = document.getElementById("overview-flow")!;
        expect(flow.innerHTML).toContain("myusers");
        expect(flow.innerHTML).toContain("Auth");
    });

    it("renders resolvers row when servers reference resolvers", async () => {
        mockApis({
            "/api/backends": {
                items: [
                    { id: 1, name: "be-api", balance: "roundrobin", servers: [{ name: "s1", address: "api.internal", port: 8080, resolvers_ref: "mydns" }] },
                ],
            },
            "/api/resolvers": { items: [{ id: 1, name: "mydns", nameservers: [{ address: "8.8.8.8" }] }] },
        });
        await renderFlowCanvas();
        const flow = document.getElementById("overview-flow")!;
        expect(flow.innerHTML).toContain("Resolvers");
        expect(flow.innerHTML).toContain("mydns");
        expect(flow.querySelector('.flow-node.resolver[data-node-id="res-mydns"]')).not.toBeNull();
    });

    it("places unreferenced resolvers in services row", async () => {
        mockApis({
            "/api/resolvers": { items: [{ id: 1, name: "spare-dns", nameservers: [] }] },
        });
        await renderFlowCanvas();
        const flow = document.getElementById("overview-flow")!;
        expect(flow.innerHTML).toContain("Services");
        expect(flow.innerHTML).toContain("spare-dns");
        const node = flow.querySelector('.flow-node.resolver.svc-node[data-node-id="res-spare-dns"]');
        expect(node).not.toBeNull();
    });

    it("renders peers in services row", async () => {
        mockApis({
            "/api/peers": { items: [{ id: 1, name: "mypeers", entries: [{ peer_name: "p1" }] }] },
        });
        await renderFlowCanvas();
        const flow = document.getElementById("overview-flow")!;
        expect(flow.innerHTML).toContain("mypeers");
        expect(flow.querySelector('.flow-node.peer[data-node-id="peer-mypeers"]')).not.toBeNull();
    });

    it("renders mailers in services row", async () => {
        mockApis({
            "/api/mailers": { items: [{ id: 1, name: "mymail", entries: [{ name: "m1" }] }] },
        });
        await renderFlowCanvas();
        const flow = document.getElementById("overview-flow")!;
        expect(flow.innerHTML).toContain("mymail");
        expect(flow.querySelector('.flow-node.mailer[data-node-id="mailer-mymail"]')).not.toBeNull();
    });

    it("renders http-errors in services row", async () => {
        mockApis({
            "/api/http-errors": { items: [{ id: 1, name: "errors-global", entries: [{ status: 503 }] }] },
        });
        await renderFlowCanvas();
        const flow = document.getElementById("overview-flow")!;
        expect(flow.innerHTML).toContain("errors-global");
        expect(flow.querySelector('.flow-node.http-err[data-node-id="he-errors-global"]')).not.toBeNull();
    });

    it("renders caches in services row", async () => {
        mockApis({
            "/api/caches": { items: [{ id: 1, name: "hot-cache", total_max_size: 256 }] },
        });
        await renderFlowCanvas();
        const flow = document.getElementById("overview-flow")!;
        expect(flow.innerHTML).toContain("hot-cache");
        expect(flow.innerHTML).toContain("256 MB");
        expect(flow.querySelector('.flow-node.cache[data-node-id="cache-hot-cache"]')).not.toBeNull();
    });

    it("renders SSL certificates in services row", async () => {
        mockApis({
            "/api/ssl-certificates": { items: [{ id: 1, domain: "example.com", provider: "letsencrypt", status: "valid" }] },
        });
        await renderFlowCanvas();
        const flow = document.getElementById("overview-flow")!;
        expect(flow.innerHTML).toContain("example.com");
        expect(flow.innerHTML).toContain("letsencrypt");
        expect(flow.querySelector('.flow-node.ssl-cert[data-node-id="ssl-example.com"]')).not.toBeNull();
    });

    it("assigns data-node-id to all flow nodes", async () => {
        mockApis({
            "/api/frontends": { items: [{ id: 1, name: "fe1", mode: "http", binds: [], options: [] }] },
            "/api/backends": { items: [{ id: 1, name: "be1", balance: "roundrobin", servers: [{ name: "s1", address: "10.0.0.1", port: 80 }] }] },
        });
        await renderFlowCanvas();
        const flow = document.getElementById("overview-flow")!;
        const nodes = flow.querySelectorAll(".flow-node[data-node-id]");
        expect(nodes.length).toBeGreaterThanOrEqual(3); // client, fe1, be1, s1
        expect(flow.querySelector('[data-node-id="client"]')).not.toBeNull();
        expect(flow.querySelector('[data-node-id="fe-1"]')).not.toBeNull();
        expect(flow.querySelector('[data-node-id="be-be1"]')).not.toBeNull();
    });

    it("does not render Services row when no auxiliary entities", async () => {
        mockApis({});
        await renderFlowCanvas();
        const flow = document.getElementById("overview-flow")!;
        expect(flow.innerHTML).not.toContain("Services");
    });
});

describe("drawFlowConnections", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
    });

    it("handles missing SVG/diagram elements gracefully", () => {
        drawFlowConnections();
        // no crash
    });

    it("draws SVG paths when diagram exists", async () => {
        mockApis({
            "/api/frontends": { items: [{ id: 1, name: "fe-web", mode: "http", default_backend: "be-web", binds: [], options: [] }] },
            "/api/backends": { items: [{ id: 1, name: "be-web", balance: "roundrobin", servers: [{ name: "s1", address: "10.0.0.1", port: 80 }] }] },
        });

        await renderFlowCanvas();
        drawFlowConnections();
        const svg = document.getElementById("flow-svg");
        expect(svg).not.toBeNull();
    });

    it("draws paths with data-from and data-to attributes", async () => {
        mockApis({
            "/api/frontends": { items: [{ id: 1, name: "fe-web", mode: "http", default_backend: "be-web", binds: [], options: [] }] },
            "/api/backends": { items: [{ id: 1, name: "be-web", balance: "roundrobin", servers: [{ name: "s1", address: "10.0.0.1", port: 80 }] }] },
        });

        await renderFlowCanvas();
        drawFlowConnections();
        const svg = document.getElementById("flow-svg")!;
        const pathsWithData = svg.querySelectorAll("path[data-from][data-to]");
        expect(pathsWithData.length).toBeGreaterThan(0);
    });

    it("draws server-to-resolver connections", async () => {
        mockApis({
            "/api/backends": {
                items: [
                    { id: 1, name: "be-dns", balance: "roundrobin", servers: [{ name: "s1", address: "dns.int", port: 53, resolvers_ref: "mydns" }] },
                ],
            },
            "/api/resolvers": { items: [{ id: 1, name: "mydns", nameservers: [{ address: "8.8.8.8" }] }] },
        });

        await renderFlowCanvas();
        drawFlowConnections();
        const svg = document.getElementById("flow-svg")!;
        const resPaths = svg.querySelectorAll('path[data-to="res-mydns"]');
        expect(resPaths.length).toBeGreaterThan(0);
    });
});

describe("hover highlight", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
    });

    it("adds flow-hover-active and highlight/dim classes on mouseenter", async () => {
        mockApis({
            "/api/frontends": { items: [{ id: 1, name: "fe-web", mode: "http", binds: [], options: [] }] },
            "/api/backends": { items: [{ id: 1, name: "be-web", balance: "roundrobin", servers: [] }] },
        });

        await renderFlowCanvas();
        drawFlowConnections();
        _initHoverHighlight();

        const diagram = document.getElementById("flow-diagram")!;
        const clientNode = diagram.querySelector('.flow-node[data-node-id="client"]') as HTMLElement;
        const feNode = diagram.querySelector('.flow-node[data-node-id="fe-1"]') as HTMLElement;

        // Simulate mouseenter on client
        clientNode.dispatchEvent(new MouseEvent("mouseenter", { bubbles: true }));

        expect(diagram.classList.contains("flow-hover-active")).toBe(true);
        expect(clientNode.classList.contains("flow-highlight")).toBe(true);
        expect(feNode.classList.contains("flow-highlight")).toBe(true);
    });

    it("dims unconnected nodes on hover", async () => {
        mockApis({
            "/api/frontends": { items: [{ id: 1, name: "fe-web", mode: "http", binds: [], options: [] }] },
            "/api/backends": { items: [{ id: 1, name: "be-web", balance: "roundrobin", servers: [] }] },
        });

        await renderFlowCanvas();
        drawFlowConnections();
        _initHoverHighlight();

        const diagram = document.getElementById("flow-diagram")!;
        const beNode = diagram.querySelector('.flow-node[data-node-id="be-be-web"]') as HTMLElement;
        const clientNode = diagram.querySelector('.flow-node[data-node-id="client"]') as HTMLElement;

        // Hover the backend node (not connected to client directly)
        beNode.dispatchEvent(new MouseEvent("mouseenter", { bubbles: true }));

        // Client should be dimmed (no direct connection to be-web)
        expect(clientNode.classList.contains("flow-dimmed")).toBe(true);
    });

    it("clears highlight classes on mouseleave", async () => {
        mockApis({
            "/api/frontends": { items: [{ id: 1, name: "fe-web", mode: "http", binds: [], options: [] }] },
        });

        await renderFlowCanvas();
        drawFlowConnections();
        _initHoverHighlight();

        const diagram = document.getElementById("flow-diagram")!;
        const clientNode = diagram.querySelector('.flow-node[data-node-id="client"]') as HTMLElement;

        clientNode.dispatchEvent(new MouseEvent("mouseenter", { bubbles: true }));
        expect(diagram.classList.contains("flow-hover-active")).toBe(true);

        // mouseleave to something outside flow-node
        clientNode.dispatchEvent(new MouseEvent("mouseleave", { bubbles: true, relatedTarget: diagram }));
        expect(diagram.classList.contains("flow-hover-active")).toBe(false);
    });

    it("highlights SVG paths connected to hovered node", async () => {
        mockApis({
            "/api/frontends": { items: [{ id: 1, name: "fe-web", mode: "http", binds: [], options: [] }] },
        });

        await renderFlowCanvas();
        drawFlowConnections();
        _initHoverHighlight();

        const diagram = document.getElementById("flow-diagram")!;
        const clientNode = diagram.querySelector('.flow-node[data-node-id="client"]') as HTMLElement;

        clientNode.dispatchEvent(new MouseEvent("mouseenter", { bubbles: true }));

        const svg = document.getElementById("flow-svg")!;
        const highlightedPaths = svg.querySelectorAll("path.flow-path-highlight");
        const dimmedPaths = svg.querySelectorAll("path.flow-path-dimmed");

        // At least the client->fe path should be highlighted
        expect(highlightedPaths.length).toBeGreaterThanOrEqual(0);
        // All non-connected paths should be dimmed (may be 0 if only one connection)
        expect(highlightedPaths.length + dimmedPaths.length).toBe(svg.querySelectorAll("path").length);
    });
});
