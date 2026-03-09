/**
 * Tests users section
 * ===================
 */

import { describe, it, expect, beforeEach, vi } from "vitest";

import { loadUsers, filterUsers, openAddUserModal, saveNewUser, deleteUserById } from "@/sections/users";

const DOM = `
  <div id="users-grid"></div>
  <div id="users-empty" style="display:none"></div>
  <input id="users-search" value="">
`;


describe("loadUsers", () => {
    let container: HTMLDivElement;
    beforeEach(() => {
        container = document.createElement("div");
        container.innerHTML = DOM;
        document.body.appendChild(container);
    });
    afterEach(() => container.remove());

    it("renders user cards from API", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () =>
                Promise.resolve([
                    { id: 1, name: "Alice Admin", email: "alice@example.com", created_at: "2024-01-01T00:00:00Z" },
                    { id: 2, name: "Bob User", email: "bob@example.com", created_at: "2024-06-15T00:00:00Z" },
                ]),
        } as any);

        await loadUsers();

        const cards = document.querySelectorAll("#users-grid .user-card");
        expect(cards.length).toBe(2);
    });

    it("shows empty state when no users", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve([]),
        } as any);

        await loadUsers();

        const empty = document.getElementById("users-empty")!;
        expect(empty.style.display).toBe("flex");
        expect(document.getElementById("users-grid")!.innerHTML).toBe("");
    });

    it("renders avatar initials from name", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () =>
                Promise.resolve([
                    { id: 1, name: "John Doe", email: "john@example.com", created_at: "2024-01-01T00:00:00Z" },
                ]),
        } as any);

        await loadUsers();

        const avatar = document.querySelector(".user-card-avatar");
        expect(avatar?.textContent).toBe("JD");
    });

    it("handles API error gracefully", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: false,
            status: 500,
            json: () => Promise.resolve({ detail: "Server error" }),
        } as any);

        await loadUsers();

        expect(document.getElementById("users-grid")!.innerHTML).toBe("");
    });
});

describe("filterUsers", () => {
    let container: HTMLDivElement;
    beforeEach(() => {
        container = document.createElement("div");
        container.innerHTML = DOM;
        document.body.appendChild(container);
        const grid = document.getElementById("users-grid")!;
        grid.innerHTML = `
            <div class="user-card" data-user-name="Alice" data-user-email="alice@example.com"></div>
            <div class="user-card" data-user-name="Bob" data-user-email="bob@other.com"></div>
        `;
    });
    afterEach(() => container.remove());

    it("shows all cards when search is empty", () => {
        (document.getElementById("users-search") as HTMLInputElement).value = "";
        filterUsers();
        const cards = document.querySelectorAll<HTMLElement>(".user-card");
        cards.forEach((c) => expect(c.style.display).toBe(""));
    });

    it("filters cards by name", () => {
        (document.getElementById("users-search") as HTMLInputElement).value = "alice";
        filterUsers();
        const cards = document.querySelectorAll<HTMLElement>(".user-card");
        expect(cards[0].style.display).toBe("");
        expect(cards[1].style.display).toBe("none");
    });

    it("filters cards by email", () => {
        (document.getElementById("users-search") as HTMLInputElement).value = "other.com";
        filterUsers();
        const cards = document.querySelectorAll<HTMLElement>(".user-card");
        expect(cards[0].style.display).toBe("none");
        expect(cards[1].style.display).toBe("");
    });

    it("shows empty state when no matches", () => {
        (document.getElementById("users-search") as HTMLInputElement).value = "zzz";
        filterUsers();
        const empty = document.getElementById("users-empty")!;
        expect(empty.style.display).toBe("flex");
    });
});

describe("openAddUserModal", () => {
    it("opens modal with form", () => {
        openAddUserModal();
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("Add New User");
        expect(content.querySelector("#nu-name")).toBeTruthy();
        expect(content.querySelector("#nu-email")).toBeTruthy();
        expect(content.querySelector("#nu-password")).toBeTruthy();
    });
});

describe("saveNewUser", () => {
    let container: HTMLDivElement;

    beforeEach(() => {
        container = document.createElement("div");
        container.innerHTML = `
            <div id="users-grid"></div>
            <div id="users-empty" style="display:none"></div>
            <input id="users-search">
            <input id="nu-name">
            <input id="nu-email">
            <input id="nu-password">
        `;
        document.body.appendChild(container);
        // Set values programmatically (jsdom doesn't sync value attribute -> property via innerHTML)
        (document.getElementById("nu-name") as HTMLInputElement).value = "New User";
        (document.getElementById("nu-email") as HTMLInputElement).value = "new@example.com";
        (document.getElementById("nu-password") as HTMLInputElement).value = "password123";
    });

    afterEach(() => container.remove());

    it("sends POST request to register", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch")
            .mockResolvedValueOnce({ ok: true, status: 200, json: () => Promise.resolve({ access_token: "t", user: { id: 2, name: "New User", email: "new@example.com" } }) } as any)
            .mockResolvedValueOnce({ ok: true, status: 200, json: () => Promise.resolve([]) } as any);

        const ev = { preventDefault: vi.fn() } as unknown as Event;
        await saveNewUser(ev);

        expect(fetchSpy).toHaveBeenCalledWith(
            expect.stringContaining("/auth/register"),
            expect.objectContaining({ method: "POST" }),
        );
    });

    it("shows error toast on empty fields", async () => {
        (document.getElementById("nu-name") as HTMLInputElement).value = "";
        const ev = { preventDefault: vi.fn() } as unknown as Event;
        await saveNewUser(ev);
        const toasts = document.getElementById("toast-container")!;
        expect(toasts.textContent).toContain("required");
    });
});

describe("deleteUserById", () => {
    let container: HTMLDivElement;
    beforeEach(() => {
        container = document.createElement("div");
        container.innerHTML = DOM;
        document.body.appendChild(container);
    });
    afterEach(() => container.remove());

    it("sends DELETE request and reloads", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch")
            .mockResolvedValueOnce({ ok: true, status: 200, json: () => Promise.resolve({ detail: "Deleted" }) } as any)
            .mockResolvedValueOnce({ ok: true, status: 200, json: () => Promise.resolve([]) } as any);

        await deleteUserById(5);

        expect(fetchSpy).toHaveBeenCalledWith(
            expect.stringContaining("/auth/users/5"),
            expect.objectContaining({ method: "DELETE" }),
        );
    });

    it("skips when confirm is declined", async () => {
        vi.spyOn(window, "confirm").mockReturnValue(false);
        const fetchSpy = vi.spyOn(globalThis, "fetch");

        await deleteUserById(5);

        expect(fetchSpy).not.toHaveBeenCalled();
    });
});
function afterEach(_arg0: () => void) {
    throw new Error("Function not implemented.");
}

