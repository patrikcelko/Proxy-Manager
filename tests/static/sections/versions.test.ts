/**
 * Tests version control (badges, save/discard)
 * =============================================
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { state } from "@/state";
import type { SectionDiff } from "@/types";
import {
    checkVersionStatus,
    refreshPendingBadges,
    openSaveVersionModal,
    saveVersion,
    discardChanges,
    applySectionChangeMarkers,
    viewSectionChanges,
} from "@/sections/versions";

describe("checkVersionStatus", () => {
    let container: HTMLDivElement;

    beforeEach(() => {
        container = document.createElement("div");
        container.innerHTML = `
            <div id="sidebar">
                <div class="nav-item" data-section="global">Global</div>
                <div class="nav-item" data-section="backends">Backends</div>
                <div class="nav-item" data-section="frontends">Frontends</div>
            </div>
            <div id="sidebar-actions" style="display:none"></div>
            <div id="toast-container"></div>
        `;
        document.body.appendChild(container);
    });

    afterEach(() => container.remove());

    it("returns true when initialized", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () =>
                Promise.resolve({
                    initialized: true,
                    has_pending: false,
                    pending_counts: {},
                    current_hash: "abc123",
                }),
        } as Response);

        const result = await checkVersionStatus();
        expect(result).toBe(true);
    });

    it("returns false when not initialized", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () =>
                Promise.resolve({
                    initialized: false,
                    has_pending: false,
                    pending_counts: {},
                    current_hash: null,
                }),
        } as Response);

        const result = await checkVersionStatus();
        expect(result).toBe(false);
    });

    it("updates state.versionStatus", async () => {
        const status = {
            initialized: true,
            has_pending: true,
            pending_counts: { backends: 2 },
            current_hash: "abc123",
        };
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve(status),
        } as Response);

        await checkVersionStatus();
        expect(state.versionStatus).toEqual(status);
    });

    it("returns false on fetch error (fail safe)", async () => {
        vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("network"));
        const result = await checkVersionStatus();
        expect(result).toBe(false);
    });
});

describe("refreshPendingBadges", () => {
    let container: HTMLDivElement;

    beforeEach(() => {
        container = document.createElement("div");
        container.innerHTML = `
            <div class="nav-item" data-section="global">Global</div>
            <div class="nav-item" data-section="backends">Backends</div>
            <div class="nav-item" data-section="frontends">Frontends</div>
            <div id="sidebar-actions" style="display:none"></div>
            <div id="toast-container"></div>
        `;
        document.body.appendChild(container);
    });

    afterEach(() => container.remove());

    it("adds badges to nav items with pending counts", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () =>
                Promise.resolve({
                    has_pending: true,
                    pending_counts: { backends: 3, global_settings: 1 },
                    sections: {},
                }),
        } as Response);

        await refreshPendingBadges();

        const backendBadge = document.querySelector('.nav-item[data-section="backends"] .nav-badge');
        expect(backendBadge).not.toBeNull();
        expect(backendBadge!.textContent).toBe("3");

        const globalBadge = document.querySelector('.nav-item[data-section="global"] .nav-badge');
        expect(globalBadge).not.toBeNull();
        expect(globalBadge!.textContent).toBe("1");
    });

    it("removes badges for sections with zero counts", async () => {
        // First set a badge
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () =>
                Promise.resolve({
                    has_pending: true,
                    pending_counts: { backends: 2 },
                    sections: {},
                }),
        } as Response);
        await refreshPendingBadges();
        expect(document.querySelectorAll(".nav-badge")).toHaveLength(1);

        // Now clear it
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () =>
                Promise.resolve({
                    has_pending: false,
                    pending_counts: { backends: 0 },
                    sections: {},
                }),
        } as Response);
        await refreshPendingBadges();
        expect(document.querySelectorAll(".nav-badge")).toHaveLength(0);
    });

    it("shows sidebar actions when has_pending is true", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () =>
                Promise.resolve({
                    has_pending: true,
                    pending_counts: { backends: 1 },
                    sections: {},
                }),
        } as Response);

        await refreshPendingBadges();
        expect(document.getElementById("sidebar-actions")!.style.display).toBe("flex");
    });

    it("hides sidebar actions when has_pending is false", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () =>
                Promise.resolve({
                    has_pending: false,
                    pending_counts: {},
                    sections: {},
                }),
        } as Response);

        await refreshPendingBadges();
        expect(document.getElementById("sidebar-actions")!.style.display).toBe("none");
    });
});

describe("openSaveVersionModal", () => {
    let container: HTMLDivElement;

    beforeEach(() => {
        container = document.createElement("div");
        container.innerHTML = `<div id="modal-overlay" style="display:none"><div id="modal-content"></div></div>`;
        document.body.appendChild(container);
    });

    afterEach(() => container.remove());

    it("opens modal with commit message input", () => {
        openSaveVersionModal();
        const modal = document.getElementById("modal-content");
        expect(modal!.innerHTML).toContain("Save Version");
        expect(modal!.innerHTML).toContain("sv-message");
    });
});

describe("saveVersion", () => {
    let container: HTMLDivElement;

    beforeEach(() => {
        container = document.createElement("div");
        container.innerHTML = `
            <input id="sv-message" value="test commit" />
            <div id="modal-overlay" style="display:flex"><div id="modal-content"></div></div>
            <div id="sidebar-actions" style="display:none"></div>
            <div id="toast-container"></div>
        `;
        document.body.appendChild(container);
    });

    afterEach(() => container.remove());

    it("sends POST with message", async () => {
        // Mock at module-level api function to avoid fetch-level issues
        const { api: apiMod } = await import("@/core/api");
        vi.spyOn({ api: apiMod }, "api");

        // Use global fetch mock as fallback
        vi.spyOn(globalThis, "fetch").mockImplementation(async (_url: any) => {
            return {
                ok: true,
                status: 200,
                json: () => Promise.resolve({ initialized: true, has_pending: false, pending_counts: {}, current_hash: "abc", hash: "abc" }),
            } as Response;
        });

        const event = { preventDefault: vi.fn() } as unknown as Event;
        await saveVersion(event);

        expect(event.preventDefault).toHaveBeenCalled();
        // The function should not have returned early
        expect(document.querySelector(".toast")).not.toBeNull();
    });

    it("shows error for empty message", async () => {
        (document.getElementById("sv-message") as HTMLInputElement).value = "   ";
        const event = { preventDefault: vi.fn() } as unknown as Event;
        await saveVersion(event);
        // Should show toast error, not call API
        expect(document.querySelector(".toast")).not.toBeNull();
    });
});

describe("discardChanges", () => {
    let container: HTMLDivElement;

    beforeEach(() => {
        container = document.createElement("div");
        container.innerHTML = `
            <div class="nav-item active" data-section="backends">Backends</div>
            <div id="sidebar-actions" style="display:flex"></div>
            <div id="toast-container"></div>
            <div id="sec-backends"></div>
            <div id="top-bar-page-title"></div>
        `;
        document.body.appendChild(container);
    });

    afterEach(() => container.remove());

    it("calls discard API when confirmed", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ detail: "discarded" }),
        } as Response);

        await discardChanges();

        const discardCall = fetchSpy.mock.calls.find((c) => String(c[0]).includes("/api/versions/discard"));
        expect(discardCall).toBeDefined();
    });

    it("does nothing when cancelled", async () => {
        (globalThis as any).__confirmPopupMock.mockResolvedValueOnce(false);
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({}),
        } as Response);

        await discardChanges();

        const discardCall = fetchSpy.mock.calls.find((c) => String(c[0]).includes("/api/versions/discard"));
        expect(discardCall).toBeUndefined();
    });
});

describe("applySectionChangeMarkers", () => {
    let container: HTMLDivElement;

    afterEach(() => {
        container?.remove();
        state.pendingDiff = null;
    });

    function setup(sidebarSection: string, cardsHtml: string): void {
        container = document.createElement("div");
        container.innerHTML = `
            <div class="nav-item active" data-section="${sidebarSection}">Section</div>
            <section id="sec-${sidebarSection}">
                <div class="section-header">Header</div>
                ${cardsHtml}
            </section>
        `;
        document.body.appendChild(container);
    }

    function makeDiff(opts: {
        created?: Record<string, unknown>[];
        deleted?: Record<string, unknown>[];
        updated?: { entity: string; old: Record<string, unknown>; new: Record<string, unknown>; changes: { field: string; old: unknown; new: unknown }[] }[];
    }): SectionDiff {
        const created = opts.created ?? [];
        const deleted = opts.deleted ?? [];
        const updated = opts.updated ?? [];
        return { created, deleted, updated, total: created.length + deleted.length + updated.length };
    }

    it("marks backend cards as modified when updated", () => {
        setup(
            "backends",
            `<div class="item-card be-card" data-entity-name="accounts_prod">
                <div class="item-header"><h3>accounts_prod</h3>
                    <div><button class="btn-icon">E</button><button class="btn-icon danger">D</button></div>
                </div>
            </div>`,
        );

        state.pendingDiff = {
            has_pending: true,
            pending_counts: { backends: 1 },
            sections: {
                backends: makeDiff({
                    updated: [
                        {
                            entity: "accounts_prod",
                            old: { name: "accounts_prod", mode: "http" },
                            new: { name: "accounts_prod", mode: "tcp" },
                            changes: [{ field: "mode", old: "http", new: "tcp" }],
                        },
                    ],
                }),
            },
        };

        applySectionChangeMarkers();

        const card = document.querySelector("[data-entity-name='accounts_prod']")!;
        expect(card.classList.contains("entity-modified")).toBe(true);
        expect(card.querySelector(".entity-change-badge")!.textContent).toBe("Modified");
    });

    it("marks backend cards as new when created", () => {
        setup(
            "backends",
            `<div class="item-card be-card" data-entity-name="new_backend">
                <div class="item-header"><h3>new_backend</h3>
                    <div><button class="btn-icon">E</button></div>
                </div>
            </div>`,
        );

        state.pendingDiff = {
            has_pending: true,
            pending_counts: { backends: 1 },
            sections: {
                backends: makeDiff({
                    created: [{ name: "new_backend", mode: "http" }],
                }),
            },
        };

        applySectionChangeMarkers();

        const card = document.querySelector("[data-entity-name='new_backend']")!;
        expect(card.classList.contains("entity-created")).toBe(true);
        expect(card.querySelector(".entity-change-badge")!.textContent).toBe("New");
    });

    it("marks renamed backends as modified (rename detection on backend side)", () => {
        // After the backend fix, renamed entities arrive as "updated" not "created+deleted"
        setup(
            "backends",
            `<div class="item-card be-card" data-entity-name="daccounts_dev">
                <div class="item-header"><h3>daccounts_dev</h3>
                    <div><button class="btn-icon">E</button></div>
                </div>
            </div>`,
        );

        state.pendingDiff = {
            has_pending: true,
            pending_counts: { backends: 1 },
            sections: {
                backends: makeDiff({
                    updated: [
                        {
                            entity: "daccounts_dev",
                            old: { name: "accounts_dev", mode: "http" },
                            new: { name: "daccounts_dev", mode: "http" },
                            changes: [{ field: "name", old: "accounts_dev", new: "daccounts_dev" }],
                        },
                    ],
                }),
            },
        };

        applySectionChangeMarkers();

        const card = document.querySelector("[data-entity-name='daccounts_dev']")!;
        expect(card.classList.contains("entity-modified")).toBe(true);
        expect(card.querySelector(".entity-change-badge")!.textContent).toBe("Modified");
    });

    it("marks listen blocks as modified when renamed", () => {
        setup(
            "listen",
            `<div class="item-card ln-card" data-entity-name="statsc">
                <div class="item-header"><h3>statsc</h3>
                    <div><button class="btn-icon">E</button></div>
                </div>
            </div>`,
        );

        state.pendingDiff = {
            has_pending: true,
            pending_counts: { listen_blocks: 1 },
            sections: {
                listen_blocks: makeDiff({
                    updated: [
                        {
                            entity: "statsc",
                            old: { name: "stats", mode: "http" },
                            new: { name: "statsc", mode: "http" },
                            changes: [{ field: "name", old: "stats", new: "statsc" }],
                        },
                    ],
                }),
            },
        };

        applySectionChangeMarkers();

        const card = document.querySelector("[data-entity-name='statsc']")!;
        expect(card.classList.contains("entity-modified")).toBe(true);
    });

    it("marks peers as modified when renamed", () => {
        setup(
            "peers",
            `<div class="item-card pe-card" data-entity-name="mypeersc">
                <div class="item-header"><h3>mypeersc</h3>
                    <div><button class="btn-icon">E</button></div>
                </div>
            </div>`,
        );

        state.pendingDiff = {
            has_pending: true,
            pending_counts: { peers: 1 },
            sections: {
                peers: makeDiff({
                    updated: [
                        {
                            entity: "mypeersc",
                            old: { name: "mypeers" },
                            new: { name: "mypeersc" },
                            changes: [{ field: "name", old: "mypeers", new: "mypeersc" }],
                        },
                    ],
                }),
            },
        };

        applySectionChangeMarkers();

        const card = document.querySelector("[data-entity-name='mypeersc']")!;
        expect(card.classList.contains("entity-modified")).toBe(true);
        expect(card.querySelector(".ecb-modified")).not.toBeNull();
    });

    it("marks ACL rows using composite key", () => {
        setup(
            "acl",
            `<table id="acl-table">
                <tbody>
                    <tr class="acl-row" data-entity-name="http:accounts.mergado.com:0">
                        <td class="acl-domain-cell">accounts.mergado.com</td>
                    </tr>
                </tbody>
            </table>`,
        );

        state.pendingDiff = {
            has_pending: true,
            pending_counts: { acl_rules: 1 },
            sections: {
                acl_rules: makeDiff({
                    updated: [
                        {
                            entity: "http:accounts.mergado.com:0",
                            old: { frontend_name: "http", domain: "accounts.mergado.com", sort_order: 0, comment: null },
                            new: { frontend_name: "http", domain: "accounts.mergado.com", sort_order: 0, comment: "edited" },
                            changes: [{ field: "comment", old: null, new: "edited" }],
                        },
                    ],
                }),
            },
        };

        applySectionChangeMarkers();

        const row = document.querySelector("[data-entity-name='http:accounts.mergado.com:0']")!;
        expect(row.classList.contains("entity-modified")).toBe(true);
    });

    it("marks newly created ACL rules using entity id", () => {
        setup(
            "acl",
            `<table id="acl-table">
                <tbody>
                    <tr class="acl-row" data-entity-name="42">
                        <td class="acl-domain-cell">new.com</td>
                    </tr>
                </tbody>
            </table>`,
        );

        state.pendingDiff = {
            has_pending: true,
            pending_counts: { acl_rules: 1 },
            sections: {
                acl_rules: makeDiff({
                    created: [{ id: 42, frontend_name: "http", domain: "new.com", sort_order: 0 }],
                }),
            },
        };

        applySectionChangeMarkers();

        const row = document.querySelector("[data-entity-name='42']")!;
        expect(row.classList.contains("entity-created")).toBe(true);
    });

    it("inserts change banner with counts", () => {
        setup(
            "backends",
            `<div class="item-card" data-entity-name="a"><div class="item-header"><h3>a</h3><div><button class="btn-icon">E</button></div></div></div>`,
        );

        state.pendingDiff = {
            has_pending: true,
            pending_counts: { backends: 3 },
            sections: {
                backends: makeDiff({
                    created: [{ name: "x" }],
                    updated: [
                        { entity: "a", old: { name: "a" }, new: { name: "a" }, changes: [] },
                    ],
                    deleted: [{ name: "z" }],
                }),
            },
        };

        applySectionChangeMarkers();

        const banner = document.querySelector(".change-banner")!;
        expect(banner).not.toBeNull();
        expect(banner.querySelector(".cb-created")!.textContent).toContain("1 new");
        expect(banner.querySelector(".cb-modified")!.textContent).toContain("1 modified");
        expect(banner.querySelector(".cb-deleted")!.textContent).toContain("1 deleted");
    });

    it("does nothing when no pending diff", () => {
        setup("backends", `<div data-entity-name="a"></div>`);
        state.pendingDiff = null;

        applySectionChangeMarkers();

        expect(document.querySelector(".entity-change-badge")).toBeNull();
        expect(document.querySelector(".change-banner")).toBeNull();
    });

    it("does not mark entities in overview section", () => {
        container = document.createElement("div");
        container.innerHTML = `
            <div class="nav-item active" data-section="overview">Overview</div>
            <section id="sec-overview"><div data-entity-name="test"></div></section>
        `;
        document.body.appendChild(container);

        state.pendingDiff = {
            has_pending: true,
            pending_counts: {},
            sections: {},
        };

        applySectionChangeMarkers();
        expect(document.querySelector(".entity-change-badge")).toBeNull();
    });

    it("places badge inside the name element, not as a separate flex child", () => {
        setup(
            "backends",
            `<div class="item-card be-card" data-entity-name="web">
                <div class="item-header"><h3>web</h3>
                    <div class="entity-actions"><button class="btn-icon">E</button><button class="btn-icon danger">D</button></div>
                </div>
            </div>`,
        );

        state.pendingDiff = {
            has_pending: true,
            pending_counts: { backends: 1 },
            sections: {
                backends: makeDiff({
                    updated: [
                        {
                            entity: "web",
                            old: { name: "web", mode: "http" },
                            new: { name: "web", mode: "tcp" },
                            changes: [{ field: "mode", old: "http", new: "tcp" }],
                        },
                    ],
                }),
            },
        };

        applySectionChangeMarkers();

        // Badge must be INSIDE h3, not a sibling (otherwise space-between pushes it to center)
        const h3 = document.querySelector(".item-header h3")!;
        const badge = h3.querySelector(".entity-change-badge");
        expect(badge).not.toBeNull();
        expect(badge!.textContent).toBe("Modified");

        // Verify it's NOT a direct child of .item-header (would break flex layout)
        const headerDirectBadge = document.querySelector(".item-header > .entity-change-badge");
        expect(headerDirectBadge).toBeNull();
    });

    it("cleans up old markers before applying new ones", () => {
        setup("backends", `<div class="item-card" data-entity-name="a"><div class="item-header"><h3>a</h3><div><button class="btn-icon">E</button></div></div></div>`);

        state.pendingDiff = {
            has_pending: true,
            pending_counts: { backends: 1 },
            sections: {
                backends: makeDiff({
                    updated: [{ entity: "a", old: { name: "a" }, new: { name: "a" }, changes: [] }],
                }),
            },
        };

        // Apply twice
        applySectionChangeMarkers();
        applySectionChangeMarkers();

        // Should only have one badge, not two
        const badges = document.querySelectorAll(".entity-change-badge");
        expect(badges).toHaveLength(1);
    });
});

describe("viewSectionChanges", () => {
    let container: HTMLDivElement;

    beforeEach(() => {
        container = document.createElement("div");
        container.innerHTML = `
            <div id="modal-overlay"><div id="modal-content"></div></div>
        `;
        document.body.appendChild(container);
    });

    afterEach(() => {
        container.remove();
        state.pendingDiff = null;
        // Clear modal content left from previous test
        const mc = document.getElementById("modal-content");
        if (mc) mc.innerHTML = "";
    });

    it("opens modal with diff tabs for a specific section", () => {
        state.pendingDiff = {
            has_pending: true,
            pending_counts: { backends: 1 },
            sections: {
                backends: {
                    created: [{ name: "new_be" }],
                    deleted: [],
                    updated: [],
                    total: 1,
                },
            },
        };

        viewSectionChanges("backends");

        const modal = document.getElementById("modal-content")!;
        expect(modal.innerHTML).toContain("Pending Changes");
        expect(modal.innerHTML).toContain("Backends");
        expect(modal.querySelector(".dtab-wrap")).not.toBeNull();
        expect(modal.querySelector(".dtab-btn")).not.toBeNull();
    });

    it("does nothing when no pending diff", () => {
        state.pendingDiff = null;
        viewSectionChanges("backends");
        const modal = document.getElementById("modal-content")!;
        // No modal-wide class or view-changes content since function returned early
        expect(modal.querySelector(".view-changes-modal")).toBeNull();
    });

    it("shows View Changes button in change banner", () => {
        container.innerHTML += `
            <div class="nav-item active" data-section="backends">Backends</div>
            <section id="sec-backends">
                <div class="section-header">Header</div>
                <div class="item-card" data-entity-name="a">
                    <div class="item-header"><h3>a</h3><div><button class="btn-icon">E</button></div></div>
                </div>
            </section>
        `;

        state.pendingDiff = {
            has_pending: true,
            pending_counts: { backends: 1 },
            sections: {
                backends: {
                    created: [],
                    deleted: [],
                    updated: [{ entity: "a", old: { name: "a" }, new: { name: "a" }, changes: [] }],
                    total: 1,
                },
            },
        };

        applySectionChangeMarkers();

        const viewBtn = document.querySelector(".btn-view-changes");
        expect(viewBtn).not.toBeNull();
        expect(viewBtn!.textContent).toContain("View Changes");
    });
});
