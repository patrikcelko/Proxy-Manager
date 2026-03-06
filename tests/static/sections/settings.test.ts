/**
 * Tests settings section
 * ======================
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import type { Setting } from "@/types";

import {
    GLOBAL_CATS,
    DEFAULTS_CATS,
    categorizeGlobal,
    categorizeDefaults,
    GLOBAL_PRESETS,
    DEFAULTS_PRESETS,
    loadSettings,
    renderSettingsTable,
    switchSettingsTab,
    filterSettingsCat,
    openGlobalQuickAdd,
    openDefaultsQuickAdd,
    openSettingsAddModal,
    applySettingPreset,
    openSettingModal,
    saveSetting,
    deleteSetting,
} from "@/sections/settings";

const makeSetting = (overrides: Partial<Setting> = {}): Setting => ({
    id: 1,
    directive: "maxconn",
    value: "10000",
    type: "global",
    sort_order: 0,
    comment: null,
    ...overrides,
});

const DOM = `
  <div>
    <div class="sett-tab active" data-tab="global">Global</div>
    <div class="sett-tab" data-tab="defaults">Defaults</div>
  </div>
  <div id="settings-section-label">Global Settings</div>
  <div id="settings-cat-tabs"></div>
  <div><table id="settings-table"><tbody></tbody></table></div>
  <div id="settings-empty" style="display:none"></div>
`;

describe("GLOBAL_CATS / DEFAULTS_CATS", () => {
    it("GLOBAL_CATS has required categories", () => {
        expect(GLOBAL_CATS).toHaveProperty("all");
        expect(GLOBAL_CATS).toHaveProperty("process");
        expect(GLOBAL_CATS).toHaveProperty("perf");
        expect(GLOBAL_CATS).toHaveProperty("ssl");
        expect(GLOBAL_CATS).toHaveProperty("logging");
        expect(GLOBAL_CATS).toHaveProperty("security");
        expect(GLOBAL_CATS).toHaveProperty("tuning");
        expect(GLOBAL_CATS).toHaveProperty("other");
    });

    it("DEFAULTS_CATS has required categories", () => {
        expect(DEFAULTS_CATS).toHaveProperty("all");
        expect(DEFAULTS_CATS).toHaveProperty("timeout");
        expect(DEFAULTS_CATS).toHaveProperty("logging");
        expect(DEFAULTS_CATS).toHaveProperty("http");
        expect(DEFAULTS_CATS).toHaveProperty("balance");
        expect(DEFAULTS_CATS).toHaveProperty("health");
        expect(DEFAULTS_CATS).toHaveProperty("retry");
        expect(DEFAULTS_CATS).toHaveProperty("perf");
        expect(DEFAULTS_CATS).toHaveProperty("other");
    });
});

describe("categorizeGlobal", () => {
    it.each([
        ["daemon", "process"],
        ["nbthread 4", "process"],
        ["pidfile /var/run/haproxy.pid", "process"],
        ["chroot /var/lib/haproxy", "process"],
        ["user haproxy", "process"],
        ["maxconn 10000", "perf"],
        ["maxsslconn 5000", "perf"],
        ["spread-checks 5", "perf"],
        ["ssl-default-bind-ciphers ECDHE", "ssl"],
        ["ca-base /etc/ssl/certs", "ssl"],
        ["crt-base /etc/ssl/private", "ssl"],
        ["log /dev/log local0", "logging"],
        ["log-send-hostname", "logging"],
        ["stats socket /run/haproxy.sock", "security"],
        ["tune.bufsize 16384", "tuning"],
        ["server-state-file /tmp/state", "tuning"],
        ["some-unknown-directive", "other"],
    ])("categorizes '%s' as '%s'", (directive, expected) => {
        expect(categorizeGlobal(directive)).toBe(expected);
    });

    it("handles empty string", () => {
        expect(categorizeGlobal("")).toBe("other");
    });
});

describe("categorizeDefaults", () => {
    it.each([
        ["timeout connect 5s", "timeout"],
        ["timeout client 30s", "timeout"],
        ["timeout server 30s", "timeout"],
        ["log global", "logging"],
        ["option httplog", "logging"],
        ["option dontlognull", "logging"],
        ["option forwardfor", "http"],
        ["option http-server-close", "http"],
        ["http-reuse safe", "http"],
        ["balance roundrobin", "balance"],
        ["hash-type consistent", "balance"],
        ["option httpchk HEAD /", "health"],
        ["option ssl-hello-chk", "health"],
        ["default-server inter 3s", "health"],
        ["retries 3", "retry"],
        ["option redispatch", "retry"],
        ["retry-on all-retryable-errors", "retry"],
        ["maxconn 3000", "perf"],
        ["fullconn 1000", "perf"],
        ["option splice-auto", "perf"],
        ["backlog 10000", "perf"],
        ["unknown-directive", "other"],
    ])("categorizes '%s' as '%s'", (directive, expected) => {
        expect(categorizeDefaults(directive)).toBe(expected);
    });
});

describe("GLOBAL_PRESETS / DEFAULTS_PRESETS", () => {
    it("GLOBAL_PRESETS has entries", () => {
        expect(GLOBAL_PRESETS.length).toBeGreaterThan(40);
        expect(GLOBAL_PRESETS[0]).toHaveProperty("d");
        expect(GLOBAL_PRESETS[0]).toHaveProperty("v");
        expect(GLOBAL_PRESETS[0]).toHaveProperty("h");
        expect(GLOBAL_PRESETS[0]).toHaveProperty("c");
    });

    it("DEFAULTS_PRESETS has entries", () => {
        expect(DEFAULTS_PRESETS.length).toBeGreaterThan(50);
    });

    it("all presets have valid categories", () => {
        const globalCats = new Set(Object.keys(GLOBAL_CATS));
        for (const p of GLOBAL_PRESETS) {
            expect(globalCats.has(p.c)).toBe(true);
        }
        const defaultCats = new Set(Object.keys(DEFAULTS_CATS));
        for (const p of DEFAULTS_PRESETS) {
            expect(defaultCats.has(p.c)).toBe(true);
        }
    });
});

describe("loadSettings", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
    });

    it("fetches and renders settings", async () => {
        const items = [
            makeSetting({ directive: "maxconn", value: "5000" }),
            makeSetting({ id: 2, directive: "daemon", value: "", sort_order: 1 }),
        ];
        vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items }),
        } as Response);

        await loadSettings("global");
        const tbody = document.querySelector("#settings-table tbody")!;
        expect(tbody.innerHTML).toContain("maxconn");
        expect(tbody.innerHTML).toContain("daemon");
    });

    it("shows empty state when no settings", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [] }),
        } as Response);

        await loadSettings("global");
        expect(document.getElementById("settings-empty")!.style.display).toBe("block");
    });

    it("shows error toast on failure", async () => {
        vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new Error("settings fetch fail"));
        await loadSettings();
        expect(document.getElementById("toast-container")!.innerHTML).toContain("settings fetch fail");
    });
});

describe("renderSettingsTable", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
    });

    it("renders sorted rows with directives and values", () => {
        const items = [
            makeSetting({ directive: "maxconn", value: "10000", sort_order: 1 }),
            makeSetting({ id: 2, directive: "daemon", value: "", sort_order: 0 }),
        ];
        renderSettingsTable(items);
        const tbody = document.querySelector("#settings-table tbody")!;
        const rows = tbody.querySelectorAll("tr");
        expect(rows.length).toBe(2);
        // Sorted by sort_order, daemon (0) first
        expect(rows[0].innerHTML).toContain("daemon");
        expect(rows[1].innerHTML).toContain("maxconn");
    });

    it("renders category tabs", () => {
        const items = [
            makeSetting({ directive: "maxconn", value: "10000" }),
            makeSetting({ id: 2, directive: "log /dev/log local0", value: "" }),
        ];
        renderSettingsTable(items);
        const catTabs = document.getElementById("settings-cat-tabs")!;
        expect(catTabs.innerHTML).toContain("All");
    });

    it("renders comment column", () => {
        const items = [makeSetting({ comment: "My comment here" })];
        renderSettingsTable(items);
        const tbody = document.querySelector("#settings-table tbody")!;
        expect(tbody.innerHTML).toContain("My comment here");
    });

    it("renders reorder buttons", () => {
        const items = [
            makeSetting({ id: 1, sort_order: 0 }),
            makeSetting({ id: 2, sort_order: 1, directive: "daemon" }),
        ];
        renderSettingsTable(items);
        const tbody = document.querySelector("#settings-table tbody")!;
        expect(tbody.innerHTML).toContain("reorderSetting");
    });
});

describe("switchSettingsTab", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
    });

    it("activates global tab", () => {
        switchSettingsTab("global");
        const label = document.getElementById("settings-section-label")!;
        expect(label.textContent).toBe("Global Settings");
        const globalTab = document.querySelector('.sett-tab[data-tab="global"]') as HTMLElement;
        expect(globalTab.classList.contains("active")).toBe(true);
    });

    it("activates defaults tab", () => {
        switchSettingsTab("defaults");
        const label = document.getElementById("settings-section-label")!;
        expect(label.textContent).toBe("Defaults");
        const defaultsTab = document.querySelector('.sett-tab[data-tab="defaults"]') as HTMLElement;
        expect(defaultsTab.classList.contains("active")).toBe(true);
    });
});

describe("filterSettingsCat", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        renderSettingsTable([
            makeSetting({ id: 1, directive: "maxconn", value: "10000" }),
            makeSetting({ id: 2, directive: "log /dev/log local0", value: "" }),
        ]);
    });

    it("shows all when 'all'", () => {
        filterSettingsCat("all");
        const rows = document.querySelectorAll<HTMLElement>("#settings-table tbody tr");
        rows.forEach((r) => expect(r.style.display).toBe(""));
    });

    it("hides non-matching categories", () => {
        filterSettingsCat("perf");
        const rows = document.querySelectorAll<HTMLElement>("#settings-table tbody tr");
        const visible = [...rows].filter((r) => r.style.display !== "none");
        const hidden = [...rows].filter((r) => r.style.display === "none");
        expect(visible.length).toBeGreaterThan(0);
        expect(hidden.length).toBeGreaterThan(0);
    });
});

describe("openSettingsAddModal / openGlobalQuickAdd / openDefaultsQuickAdd", () => {
    it("opens global quick-add modal", () => {
        openGlobalQuickAdd();
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("Quick Add");
        expect(content.innerHTML).toContain("Global");
    });

    it("opens defaults quick-add modal", () => {
        openDefaultsQuickAdd();
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("Quick Add");
        expect(content.innerHTML).toContain("Defaults");
    });

    it("renders preset cards in the grid", () => {
        openSettingsAddModal("global");
        const content = document.getElementById("modal-content")!;
        expect(content.querySelector("#settAddGrid")).toBeTruthy();
        const cards = content.querySelectorAll(".dir-card");
        expect(cards.length).toBe(GLOBAL_PRESETS.length);
    });

    it("renders search input", () => {
        openSettingsAddModal("defaults");
        const content = document.getElementById("modal-content")!;
        expect(content.querySelector("#sett-preset-filter")).toBeTruthy();
    });
});

describe("applySettingPreset", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
    });

    it("applies global preset via POST", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 201,
            json: () => Promise.resolve({ id: 1 }),
        } as Response);
        await applySettingPreset("global", 0);
        const first = fetchSpy.mock.calls[0];
        expect(first[0]).toBe("/api/settings");
        expect((first[1] as any).method).toBe("POST");
        const body = JSON.parse((first[1] as any).body);
        expect(body.directive).toBe(GLOBAL_PRESETS[0].d);
        expect(body.value).toBe(GLOBAL_PRESETS[0].v);
        expect(body.type).toBe("global");
    });

    it("applies defaults preset via POST", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 201,
            json: () => Promise.resolve({ id: 1 }),
        } as Response);
        await applySettingPreset("defaults", 0);
        const body = JSON.parse((fetchSpy.mock.calls[0][1] as any).body);
        expect(body.directive).toBe(DEFAULTS_PRESETS[0].d);
        expect(body.type).toBe("defaults");
    });

    it("does nothing for out-of-range index", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch");
        await applySettingPreset("global", 9999);
        expect(fetchSpy).not.toHaveBeenCalled();
    });
});

describe("openSettingModal", () => {
    it("opens create modal", () => {
        openSettingModal();
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("New");
        expect(content.innerHTML).toContain("Setting");
        expect(content.querySelector("#m-directive")).toBeTruthy();
        expect(content.querySelector("#m-value")).toBeTruthy();
    });

    it("opens edit modal with pre-filled values", () => {
        openSettingModal(makeSetting({ directive: "maxconn", value: "5000", comment: "test comment" }));
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("Edit");
        expect(content.innerHTML).toContain("maxconn");
        expect(content.innerHTML).toContain("5000");
        expect(content.innerHTML).toContain("test comment");
    });
});

describe("saveSetting", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        openSettingModal();
    });

    it("creates via POST", async () => {
        (document.getElementById("m-directive") as HTMLInputElement).value = "maxconn";
        (document.getElementById("m-value") as HTMLInputElement).value = "10000";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 201,
            json: () => Promise.resolve({ id: 1 }),
        } as Response);
        await saveSetting(null);
        const first = fetchSpy.mock.calls[0];
        expect(first[0]).toBe("/api/settings");
        expect((first[1] as any).method).toBe("POST");
    });

    it("updates via PUT", async () => {
        (document.getElementById("m-directive") as HTMLInputElement).value = "maxconn";
        (document.getElementById("m-value") as HTMLInputElement).value = "20000";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ id: 5 }),
        } as Response);
        await saveSetting(5);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/settings/5");
        expect((fetchSpy.mock.calls[0][1] as any).method).toBe("PUT");
    });

    it("includes comment and sort_order in body", async () => {
        (document.getElementById("m-directive") as HTMLInputElement).value = "daemon";
        (document.getElementById("m-value") as HTMLInputElement).value = "";
        (document.getElementById("m-sort") as HTMLInputElement).value = "5";
        (document.getElementById("m-comment") as HTMLInputElement).value = "Run as daemon";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 201,
            json: () => Promise.resolve({ id: 1 }),
        } as Response);
        await saveSetting(null);
        const body = JSON.parse((fetchSpy.mock.calls[0][1] as any).body);
        expect(body.sort_order).toBe(5);
        expect(body.comment).toBe("Run as daemon");
    });
});

describe("deleteSetting", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
    });

    it("deletes via DELETE", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [] }),
        } as Response);
        await deleteSetting(3);
        expect(fetchSpy).toHaveBeenCalledWith("/api/settings/3", expect.objectContaining({ method: "DELETE" }));
    });
});
