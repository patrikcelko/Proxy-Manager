/**
 * Tests userlists section
 * =======================
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { state } from "@/state";
import type { Userlist, UserlistEntry } from "@/types";

import {
    loadUserlists,
    filterUserlists,
    renderUserlists,
    openUserlistModal,
    openEntryModal,
    openChangePasswordModal,
    togglePwVis,
    saveEntry,
    savePasswordChange,
    deleteEntry,
    saveUserlist,
    deleteUserlist,
} from "@/sections/userlists";

const makeUserEntry = (overrides: Partial<UserlistEntry> = {}): UserlistEntry => ({
    id: 1,
    username: "admin",
    has_password: true,
    sort_order: 0,
    ...overrides,
});

const makeUserlist = (overrides: Partial<Userlist> = {}): Userlist => ({
    id: 1,
    name: "myusers",
    entries: [],
    ...overrides,
});

const DOM = `
  <input id="userlist-search" value="">
  <div id="userlists-grid"></div>
  <div id="userlists-empty" style="display:none"></div>
`;

describe("loadUserlists + renderUserlists", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allUserlists = [];
    });

    it("fetches and renders userlists", async () => {
        const items = [makeUserlist({ name: "loaded-list" })];
        vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items }),
        } as Response);

        await loadUserlists();
        expect(state.allUserlists).toEqual(items);
        expect(document.getElementById("userlists-grid")!.innerHTML).toContain("loaded-list");
    });

    it("shows empty state when no userlists", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [] }),
        } as Response);

        await loadUserlists();
        expect(document.getElementById("userlists-grid")!.innerHTML).toBe("");
        expect(document.getElementById("userlists-empty")!.style.display).toBe("block");
    });

    it("renders user entries with badges", () => {
        const list = [
            makeUserlist({
                entries: [
                    makeUserEntry({ username: "alice", has_password: true }),
                    makeUserEntry({ id: 2, username: "bob", has_password: false }),
                ],
            }),
        ];
        renderUserlists(list);
        const grid = document.getElementById("userlists-grid")!;
        expect(grid.innerHTML).toContain("alice");
        expect(grid.innerHTML).toContain("bob");
        expect(grid.innerHTML).toContain("secured");
        expect(grid.innerHTML).toContain("no password");
    });

    it("shows user count", () => {
        const list = [
            makeUserlist({
                entries: [makeUserEntry(), makeUserEntry({ id: 2, username: "user2" })],
            }),
        ];
        renderUserlists(list);
        const grid = document.getElementById("userlists-grid")!;
        expect(grid.innerHTML).toContain("2 users");
    });

    it("shows singular user count", () => {
        const list = [
            makeUserlist({
                entries: [makeUserEntry()],
            }),
        ];
        renderUserlists(list);
        const grid = document.getElementById("userlists-grid")!;
        expect(grid.innerHTML).toContain("1 user");
    });

    it("shows no users configured when empty entries", () => {
        renderUserlists([makeUserlist({ entries: [] })]);
        const grid = document.getElementById("userlists-grid")!;
        expect(grid.innerHTML).toContain("No users configured");
    });

    it("shows error toast on fetch failure", async () => {
        vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new Error("UL fetch fail"));
        await loadUserlists();
        expect(document.getElementById("toast-container")!.innerHTML).toContain("UL fetch fail");
    });
});

describe("filterUserlists", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allUserlists = [
            makeUserlist({ id: 1, name: "admin-users" }),
            makeUserlist({
                id: 2,
                name: "api-users",
                entries: [makeUserEntry({ username: "apibot" })],
            }),
        ];
    });

    it("filters by list name", () => {
        (document.getElementById("userlist-search") as HTMLInputElement).value = "admin";
        filterUserlists();
        const grid = document.getElementById("userlists-grid")!;
        expect(grid.innerHTML).toContain("admin-users");
        expect(grid.innerHTML).not.toContain("api-users");
    });

    it("filters by username", () => {
        (document.getElementById("userlist-search") as HTMLInputElement).value = "apibot";
        filterUserlists();
        const grid = document.getElementById("userlists-grid")!;
        expect(grid.innerHTML).toContain("api-users");
        expect(grid.innerHTML).not.toContain("admin-users");
    });

    it("shows all when search empty", () => {
        (document.getElementById("userlist-search") as HTMLInputElement).value = "";
        filterUserlists();
        const grid = document.getElementById("userlists-grid")!;
        expect(grid.innerHTML).toContain("admin-users");
        expect(grid.innerHTML).toContain("api-users");
    });
});

describe("openUserlistModal", () => {
    it("opens create modal", () => {
        openUserlistModal();
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("New");
        expect(content.innerHTML).toContain("Auth List");
    });

    it("opens edit modal", () => {
        openUserlistModal(makeUserlist({ name: "edit-list" }));
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("Edit");
        expect(content.innerHTML).toContain("edit-list");
    });
});

describe("saveUserlist", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        openUserlistModal();
    });

    it("creates via POST", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "new-list";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 201,
            json: () => Promise.resolve({ id: 1 }),
        } as Response);
        await saveUserlist(null);
        const first = fetchSpy.mock.calls[0];
        expect(first[0]).toBe("/api/userlists");
        expect((first[1] as any).method).toBe("POST");
    });

    it("updates via PUT", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "upd-list";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ id: 5 }),
        } as Response);
        await saveUserlist(5);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/userlists/5");
    });

    it("shows error toast when name is empty", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "";
        await saveUserlist(null);
        expect(document.getElementById("toast-container")!.innerHTML).toContain("Name is required");
    });
});

describe("deleteUserlist", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allUserlists = [];
    });

    it("deletes after confirmation", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [] }),
        } as Response);
        await deleteUserlist(7);
        expect(fetchSpy).toHaveBeenCalledWith("/api/userlists/7", expect.objectContaining({ method: "DELETE" }));
    });
});

describe("openEntryModal", () => {
    beforeEach(() => {
        state.allUserlists = [];
    });

    it("opens create modal (no entry id)", () => {
        openEntryModal(1);
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("New");
        expect(content.innerHTML).toContain("User Entry");
        // Create mode has password fields
        expect(content.querySelector("#m-password")).toBeTruthy();
        expect(content.querySelector("#m-password-confirm")).toBeTruthy();
    });

    it("opens edit modal with existing entry", () => {
        state.allUserlists = [
            makeUserlist({
                id: 1,
                entries: [makeUserEntry({ id: 10, username: "edituser" })],
            }),
        ];
        openEntryModal(1, 10);
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("Edit");
        expect(content.innerHTML).toContain("edituser");
        // Edit mode should NOT have password fields
        expect(content.querySelector("#m-password")).toBeNull();
    });
});

describe("saveEntry", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allUserlists = [];
        openEntryModal(1); // Create mode
    });

    it("shows error if username is empty", async () => {
        (document.getElementById("m-username") as HTMLInputElement).value = "";
        await saveEntry(1, null);
        expect(document.getElementById("toast-container")!.innerHTML).toContain("Username is required");
    });

    it("shows error if password is empty (create)", async () => {
        (document.getElementById("m-username") as HTMLInputElement).value = "testuser";
        (document.getElementById("m-password") as HTMLInputElement).value = "";
        await saveEntry(1, null);
        expect(document.getElementById("toast-container")!.innerHTML).toContain("Password is required");
    });

    it("shows error if password too short", async () => {
        (document.getElementById("m-username") as HTMLInputElement).value = "testuser";
        (document.getElementById("m-password") as HTMLInputElement).value = "ab";
        (document.getElementById("m-password-confirm") as HTMLInputElement).value = "ab";
        await saveEntry(1, null);
        expect(document.getElementById("toast-container")!.innerHTML).toContain("at least 4");
    });

    it("shows error if passwords do not match", async () => {
        (document.getElementById("m-username") as HTMLInputElement).value = "testuser";
        (document.getElementById("m-password") as HTMLInputElement).value = "password1";
        (document.getElementById("m-password-confirm") as HTMLInputElement).value = "different";
        await saveEntry(1, null);
        expect(document.getElementById("toast-container")!.innerHTML).toContain("do not match");
    });

    it("creates via POST with valid data", async () => {
        (document.getElementById("m-username") as HTMLInputElement).value = "newuser";
        (document.getElementById("m-password") as HTMLInputElement).value = "securepass";
        (document.getElementById("m-password-confirm") as HTMLInputElement).value = "securepass";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 201,
            json: () => Promise.resolve({ id: 1 }),
        } as Response);
        await saveEntry(1, null);
        const first = fetchSpy.mock.calls[0];
        expect(first[0]).toBe("/api/userlists/1/entries");
        expect((first[1] as any).method).toBe("POST");
        const body = JSON.parse((first[1] as any).body);
        expect(body.username).toBe("newuser");
        expect(body.password).toBe("securepass");
    });

    it("updates via PUT (edit mode, no password fields)", async () => {
        // Re-open in edit mode
        state.allUserlists = [
            makeUserlist({
                id: 1,
                entries: [makeUserEntry({ id: 10, username: "edituser" })],
            }),
        ];
        openEntryModal(1, 10);
        (document.getElementById("m-username") as HTMLInputElement).value = "upduser";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ id: 10 }),
        } as Response);
        await saveEntry(1, 10);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/userlists/1/entries/10");
        expect((fetchSpy.mock.calls[0][1] as any).method).toBe("PUT");
    });
});

describe("deleteEntry", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allUserlists = [];
    });

    it("deletes after confirmation", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [] }),
        } as Response);
        await deleteEntry(2, 8);
        expect(fetchSpy).toHaveBeenCalledWith("/api/userlists/2/entries/8", expect.objectContaining({ method: "DELETE" }));
    });
});

describe("openChangePasswordModal + savePasswordChange", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allUserlists = [];
    });

    it("opens change password modal", () => {
        openChangePasswordModal(1, 5);
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("Change Password");
        expect(content.querySelector("#m-new-pw")).toBeTruthy();
        expect(content.querySelector("#m-new-pw-confirm")).toBeTruthy();
    });

    it("shows error if new password is empty", async () => {
        openChangePasswordModal(1, 5);
        (document.getElementById("m-new-pw") as HTMLInputElement).value = "";
        await savePasswordChange(1, 5);
        expect(document.getElementById("toast-container")!.innerHTML).toContain("Password is required");
    });

    it("shows error if new password too short", async () => {
        openChangePasswordModal(1, 5);
        (document.getElementById("m-new-pw") as HTMLInputElement).value = "ab";
        (document.getElementById("m-new-pw-confirm") as HTMLInputElement).value = "ab";
        await savePasswordChange(1, 5);
        expect(document.getElementById("toast-container")!.innerHTML).toContain("at least 4");
    });

    it("shows error if new passwords do not match", async () => {
        openChangePasswordModal(1, 5);
        (document.getElementById("m-new-pw") as HTMLInputElement).value = "password1";
        (document.getElementById("m-new-pw-confirm") as HTMLInputElement).value = "different";
        await savePasswordChange(1, 5);
        expect(document.getElementById("toast-container")!.innerHTML).toContain("do not match");
    });

    it("saves password change via PUT", async () => {
        openChangePasswordModal(1, 5);
        (document.getElementById("m-new-pw") as HTMLInputElement).value = "newsecure";
        (document.getElementById("m-new-pw-confirm") as HTMLInputElement).value = "newsecure";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ id: 5 }),
        } as Response);
        await savePasswordChange(1, 5);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/userlists/1/entries/5");
        const body = JSON.parse((fetchSpy.mock.calls[0][1] as any).body);
        expect(body.password).toBe("newsecure");
    });
});

describe("togglePwVis", () => {
    it("toggles password to text and back", () => {
        document.body.insertAdjacentHTML(
            "beforeend",
            `<input type="password" id="pw-test-field"><button id="pw-test-btn"></button>`,
        );
        const btn = document.getElementById("pw-test-btn") as HTMLButtonElement;
        const inp = document.getElementById("pw-test-field") as HTMLInputElement;

        expect(inp.type).toBe("password");
        togglePwVis("pw-test-field", btn);
        expect(inp.type).toBe("text");
        togglePwVis("pw-test-field", btn);
        expect(inp.type).toBe("password");
    });

    it("handles missing input gracefully", () => {
        const btn = document.createElement("button");
        expect(() => togglePwVis("nonexistent", btn)).not.toThrow();
    });
});
