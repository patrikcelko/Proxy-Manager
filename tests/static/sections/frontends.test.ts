/**
 * Tests frontends section
 * =======================
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { state } from "@/state";
import type { Frontend, FrontendBind, FrontendOption } from "@/types";

import {
    loadFrontends,
    renderFrontends,
    filterFrontends,
    openFrontendModal,
    saveFrontend,
    deleteFrontend,
    categorizeFrontendOpt,
    renderBindChips,
    FE_OPT_CATS,
    BIND_PRESETS,
    FRONTEND_OPTIONS,
    openBindModal,
    saveBind,
    openOptionModal,
    saveOption,
    filterFeOpts,
    applyOptPreset,
} from "@/sections/frontends";

const makeBind = (overrides: Partial<FrontendBind> = {}): FrontendBind => ({
    id: 1,
    bind_line: "*:80",
    sort_order: 0,
    ...overrides,
});

const makeOption = (overrides: Partial<FrontendOption> = {}): FrontendOption => ({
    id: 1,
    directive: "option httplog",
    value: "",
    comment: "",
    sort_order: 0,
    ...overrides,
});

const makeFrontend = (overrides: Partial<Frontend> = {}): Frontend => ({
    id: 1,
    name: "fe-web",
    mode: "http",
    default_backend: "be-web",
    maxconn: null,
    timeout_client: null,
    timeout_http_request: null,
    timeout_http_keep_alive: null,
    option_forwardfor: false,
    option_httplog: false,
    option_tcplog: false,
    compression_algo: null,
    compression_type: null,
    comment: null,
    binds: [],
    options: [],
    ...overrides,
});

const DOM = `
  <input id="frontend-search" value="">
  <div id="frontends-grid"></div>
  <div id="frontends-empty" style="display:none"></div>
`;

describe("FE_OPT_CATS", () => {
    it("has all expected categories", () => {
        expect(Object.keys(FE_OPT_CATS)).toContain("all");
        expect(Object.keys(FE_OPT_CATS)).toContain("logging");
        expect(Object.keys(FE_OPT_CATS)).toContain("http");
        expect(Object.keys(FE_OPT_CATS)).toContain("security");
        expect(Object.keys(FE_OPT_CATS)).toContain("routing");
        expect(Object.keys(FE_OPT_CATS)).toContain("timeout");
        expect(Object.keys(FE_OPT_CATS)).toContain("acl");
        expect(Object.keys(FE_OPT_CATS)).toContain("perf");
        expect(Object.keys(FE_OPT_CATS)).toContain("other");
    });
});

describe("categorizeFrontendOpt", () => {
    it("categorizes logging directives", () => {
        expect(categorizeFrontendOpt("option httplog")).toBe("logging");
        expect(categorizeFrontendOpt("option dontlognull")).toBe("logging");
        expect(categorizeFrontendOpt("log global")).toBe("logging");
    });

    it("categorizes http directives", () => {
        expect(categorizeFrontendOpt("option forwardfor")).toBe("http");
        expect(categorizeFrontendOpt("http-request set-header X-Real-IP %[src]")).toBe("http");
        expect(categorizeFrontendOpt("compression algo gzip")).toBe("http");
    });

    it("categorizes security directives", () => {
        expect(categorizeFrontendOpt("rate-limit sessions 100")).toBe("security");
        expect(categorizeFrontendOpt("stick-table type ip size 200k")).toBe("security");
    });

    it("categorizes routing directives", () => {
        expect(categorizeFrontendOpt("use_backend api-servers if { path_beg /api/ }")).toBe("routing");
        expect(categorizeFrontendOpt("redirect prefix https://www.example.com")).toBe("routing");
    });

    it("categorizes timeout directives", () => {
        expect(categorizeFrontendOpt("timeout client 30s")).toBe("timeout");
    });

    it("categorizes acl directives", () => {
        expect(categorizeFrontendOpt("acl is_ssl dst_port 443")).toBe("acl");
    });

    it("categorizes performance directives", () => {
        expect(categorizeFrontendOpt("maxconn 5000")).toBe("perf");
        expect(categorizeFrontendOpt("option splice-auto")).toBe("perf");
    });

    it("returns other for unmatched", () => {
        expect(categorizeFrontendOpt("some-unknown-directive")).toBe("other");
        expect(categorizeFrontendOpt("")).toBe("other");
    });
});

describe("renderBindChips", () => {
    it("renders single bind as one chip", () => {
        const html = renderBindChips("*:80");
        expect(html).toContain("bind-chip");
        expect(html).toContain("*:80");
    });

    it("renders comma-separated binds as multiple chips", () => {
        const html = renderBindChips("ipv4@*:80,ipv6@:::80");
        expect(html).toContain("ipv4@*:80");
        expect(html).toContain("ipv6@:::80");
    });

    it("extracts shared suffix when all parts have same opts", () => {
        const html = renderBindChips("ipv4@*:443 ssl crt /cert.pem,ipv6@:::443 ssl crt /cert.pem");
        expect(html).toContain("bind-opts-suffix");
        expect(html).toContain("ssl crt /cert.pem");
    });

    it("handles empty string", () => {
        const html = renderBindChips("");
        expect(html).toContain("bind-chip");
    });
});

describe("renderFrontends", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
    });

    it("shows empty state when no frontends", () => {
        renderFrontends([]);
        expect(document.getElementById("frontends-grid")!.innerHTML).toBe("");
        expect(document.getElementById("frontends-empty")!.style.display).toBe("block");
        expect(document.getElementById("frontends-grid")!.style.display).toBe("none");
    });

    it("renders frontend cards", () => {
        renderFrontends([makeFrontend()]);
        const grid = document.getElementById("frontends-grid")!;
        expect(grid.innerHTML).toContain("fe-web");
        expect(grid.style.display).toBe("flex");
        expect(document.getElementById("frontends-empty")!.style.display).toBe("none");
    });

    it("renders bind addresses", () => {
        renderFrontends([makeFrontend({ binds: [makeBind({ bind_line: "*:443 ssl" })] })]);
        const grid = document.getElementById("frontends-grid")!;
        expect(grid.innerHTML).toContain(":443");
        expect(grid.innerHTML).toContain("SSL");
    });

    it("renders options in entity list", () => {
        renderFrontends([makeFrontend({ options: [makeOption({ directive: "option httplog" })] })]);
        const grid = document.getElementById("frontends-grid")!;
        expect(grid.innerHTML).toContain("option httplog");
    });

    it("renders mode badge and default_backend", () => {
        renderFrontends([makeFrontend({ mode: "tcp", default_backend: "be-tcp" })]);
        const grid = document.getElementById("frontends-grid")!;
        expect(grid.innerHTML).toContain("tcp");
        expect(grid.innerHTML).toContain("be-tcp");
    });

    it("renders summary pills for features", () => {
        renderFrontends([
            makeFrontend({
                option_forwardfor: true,
                option_httplog: true,
                compression_algo: "gzip",
                binds: [makeBind({ bind_line: "*:443 ssl crt /cert.pem" })],
            }),
        ]);
        const grid = document.getElementById("frontends-grid")!;
        expect(grid.innerHTML).toContain("XFF");
        expect(grid.innerHTML).toContain("log");
        expect(grid.innerHTML).toContain("gzip");
        expect(grid.innerHTML).toContain("SSL");
    });

    it("renders detail rows for timeouts", () => {
        renderFrontends([makeFrontend({ timeout_client: "30s", timeout_http_request: "10s", maxconn: 5000 })]);
        const grid = document.getElementById("frontends-grid")!;
        expect(grid.innerHTML).toContain("Client Timeout");
        expect(grid.innerHTML).toContain("30s");
        expect(grid.innerHTML).toContain("5000");
    });

    it("renders comment section", () => {
        renderFrontends([makeFrontend({ comment: "My frontend" })]);
        const grid = document.getElementById("frontends-grid")!;
        expect(grid.innerHTML).toContain("My frontend");
    });

    it("separates IP access rules from regular options", () => {
        renderFrontends([
            makeFrontend({
                options: [
                    makeOption({ id: 1, directive: "tcp-request connection reject", value: "if { src 10.0.0.0/8 }" }),
                    makeOption({ id: 2, directive: "option httplog", value: "" }),
                ],
            }),
        ]);
        const grid = document.getElementById("frontends-grid")!;
        expect(grid.innerHTML).toContain("DENY");
        expect(grid.innerHTML).toContain("option httplog");
    });
});

describe("filterFrontends", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allFrontends = [
            makeFrontend({ id: 1, name: "fe-web", mode: "http", default_backend: "be-web" }),
            makeFrontend({ id: 2, name: "fe-api", mode: "tcp", default_backend: "be-api" }),
        ];
    });

    it("filters by name", () => {
        (document.getElementById("frontend-search") as HTMLInputElement).value = "api";
        filterFrontends();
        const grid = document.getElementById("frontends-grid")!;
        expect(grid.innerHTML).toContain("fe-api");
        expect(grid.innerHTML).not.toContain("fe-web");
    });

    it("filters by mode", () => {
        (document.getElementById("frontend-search") as HTMLInputElement).value = "tcp";
        filterFrontends();
        const grid = document.getElementById("frontends-grid")!;
        expect(grid.innerHTML).toContain("fe-api");
        expect(grid.innerHTML).not.toContain("fe-web");
    });

    it("filters by backend name", () => {
        (document.getElementById("frontend-search") as HTMLInputElement).value = "be-api";
        filterFrontends();
        const grid = document.getElementById("frontends-grid")!;
        expect(grid.innerHTML).toContain("fe-api");
        expect(grid.innerHTML).not.toContain("fe-web");
    });

    it("shows all when empty", () => {
        (document.getElementById("frontend-search") as HTMLInputElement).value = "";
        filterFrontends();
        const grid = document.getElementById("frontends-grid")!;
        expect(grid.innerHTML).toContain("fe-web");
        expect(grid.innerHTML).toContain("fe-api");
    });
});

describe("loadFrontends", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allFrontends = [];
    });

    it("fetches and renders frontends", async () => {
        const items = [makeFrontend({ name: "loaded-fe" })];
        vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items }),
        } as Response);

        await loadFrontends();
        expect(state.allFrontends).toEqual(items);
        expect(document.getElementById("frontends-grid")!.innerHTML).toContain("loaded-fe");
    });

    it("shows toast on error", async () => {
        vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new Error("Net fail"));
        await loadFrontends();
        expect(document.getElementById("toast-container")!.innerHTML).toContain("Net fail");
    });
});

describe("openFrontendModal", () => {
    beforeEach(() => {
        state.allBackends = [];
    });

    it("opens create modal", () => {
        openFrontendModal();
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("New Frontend");
        expect(document.getElementById("modal-overlay")!.classList.contains("show")).toBe(true);
    });

    it("opens edit modal with existing data", () => {
        openFrontendModal(makeFrontend({ name: "edit-fe", timeout_client: "60s" }));
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("Edit Frontend");
        expect(content.innerHTML).toContain("edit-fe");
    });
});

describe("saveFrontend", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allBackends = [];
        openFrontendModal();
    });

    it("creates via POST", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "new-fe";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 201,
            json: () => Promise.resolve({ id: 1, name: "new-fe" }),
        } as Response);
        await saveFrontend(null);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/frontends");
    });

    it("updates via PUT", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "upd-fe";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ id: 5, name: "upd-fe" }),
        } as Response);
        await saveFrontend(5);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/frontends/5");
        expect((fetchSpy.mock.calls[0][1] as any).method).toBe("PUT");
    });
});

describe("deleteFrontend", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allFrontends = [];
    });

    it("deletes after confirmation", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [] }),
        } as Response);
        await deleteFrontend(3);
        expect(fetchSpy).toHaveBeenCalledWith("/api/frontends/3", expect.objectContaining({ method: "DELETE" }));
    });
});

describe("BIND_PRESETS", () => {
    it("has presets with correct structure", () => {
        expect(BIND_PRESETS.length).toBeGreaterThan(0);
        BIND_PRESETS.forEach((p) => {
            expect(p).toHaveProperty("cat");
            expect(p).toHaveProperty("line");
            expect(p).toHaveProperty("h");
        });
    });

    it("has expected categories", () => {
        const cats = [...new Set(BIND_PRESETS.map((p) => p.cat))];
        expect(cats).toContain("HTTP");
        expect(cats).toContain("HTTPS");
        expect(cats).toContain("TCP");
    });
});

describe("FRONTEND_OPTIONS", () => {
    it("has presets with correct structure", () => {
        expect(FRONTEND_OPTIONS.length).toBeGreaterThan(0);
        FRONTEND_OPTIONS.forEach((p) => {
            expect(p).toHaveProperty("c");
            expect(p).toHaveProperty("d");
            expect(p).toHaveProperty("h");
        });
    });
});

describe("openBindModal", () => {
    it("opens create bind modal", () => {
        openBindModal(1);
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("New Bind");
    });

    it("opens edit bind modal", () => {
        openBindModal(1, makeBind({ bind_line: "*:443 ssl" }));
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("Edit Bind");
        expect(content.innerHTML).toContain("*:443 ssl");
    });
});

describe("saveBind", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        openBindModal(1);
    });

    it("creates bind via POST", async () => {
        (document.getElementById("m-bind-line") as HTMLInputElement).value = "*:8080";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 201,
            json: () => Promise.resolve({ id: 1 }),
        } as Response);
        await saveBind(1, null);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/frontends/1/binds");
    });

    it("updates bind via PUT", async () => {
        (document.getElementById("m-bind-line") as HTMLInputElement).value = "*:9090";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ id: 5 }),
        } as Response);
        await saveBind(1, 5);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/frontends/1/binds/5");
    });
});

describe("openOptionModal", () => {
    it("opens create option modal with presets", () => {
        openOptionModal(1);
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("New Frontend Option");
        expect(content.innerHTML).toContain("Templates");
    });

    it("opens edit option modal", () => {
        openOptionModal(1, makeOption({ directive: "option httplog" }));
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("Edit Frontend Option");
        expect(content.innerHTML).toContain("option httplog");
    });
});

describe("saveOption", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        openOptionModal(1);
    });

    it("creates option via POST", async () => {
        (document.getElementById("m-directive") as HTMLInputElement).value = "option httplog";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 201,
            json: () => Promise.resolve({ id: 1 }),
        } as Response);
        await saveOption(1, null);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/frontends/1/options");
    });
});

describe("applyOptPreset", () => {
    beforeEach(() => {
        openOptionModal(1);
    });

    it("fills form fields from preset", () => {
        applyOptPreset(0);
        const d = document.getElementById("m-directive") as HTMLInputElement;
        expect(d.value).toBe(FRONTEND_OPTIONS[0].d);
    });

    it("does nothing for invalid index", () => {
        applyOptPreset(99999);
        // no crash
    });
});

describe("filterFeOpts", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        renderFrontends([
            makeFrontend({
                id: 42,
                options: [
                    makeOption({ id: 1, directive: "option httplog", value: "" }),
                    makeOption({ id: 2, directive: "timeout client", value: "30s" }),
                ],
            }),
        ]);
    });

    it("filters options by category", () => {
        filterFeOpts(42, "timeout");
        const list = document.getElementById("fe-opts-42")!;
        const items = list.querySelectorAll<HTMLElement>("li[data-fe-cat]");
        const visible = [...items].filter((li) => li.style.display !== "none");
        expect(visible.length).toBeGreaterThanOrEqual(1);
    });

    it("shows all when category is all", () => {
        filterFeOpts(42, "all");
        const list = document.getElementById("fe-opts-42")!;
        const items = list.querySelectorAll<HTMLElement>("li[data-fe-cat]");
        const visible = [...items].filter((li) => li.style.display !== "none");
        expect(visible.length).toBe(2);
    });
});
