/**
 * Tests mailers section
 * =====================
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { state } from "@/state";
import type { Mailer, MailerEntry } from "@/types";

import {
    loadMailers,
    filterMailers,
    openMailerModal,
    saveMailer,
    deleteMailer,
    openMailerEntryModal,
    saveMailerEntry,
    deleteMailerEntry,
} from "@/sections/mailers";

const makeEntry = (overrides: Partial<MailerEntry> = {}): MailerEntry => ({
    id: 1,
    name: "smtp1",
    address: "smtp.example.com",
    port: 25,
    sort_order: 0,
    smtp_auth: false,
    smtp_user: null,
    smtp_password: null,
    use_tls: false,
    use_starttls: false,
    ...overrides,
});

const makeMailer = (overrides: Partial<Mailer> = {}): Mailer => ({
    id: 1,
    name: "mymailers",
    comment: null,
    timeout_mail: null,
    extra_options: null,
    entries: [],
    ...overrides,
});

const DOM = `
  <input id="mailer-search" value="">
  <div id="mailers-grid"></div>
  <div id="mailers-empty" style="display:none"></div>
`;

describe("loadMailers + render", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allMailers = [];
    });

    it("fetches and renders mailers", async () => {
        const items = [makeMailer({ name: "loaded-mailer" })];
        vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items }),
        } as Response);

        await loadMailers();
        expect(state.allMailers).toEqual(items);
        expect(document.getElementById("mailers-grid")!.innerHTML).toContain("loaded-mailer");
    });

    it("shows empty state", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [] }),
        } as Response);

        await loadMailers();
        expect(document.getElementById("mailers-grid")!.innerHTML).toBe("");
        expect(document.getElementById("mailers-empty")!.style.display).toBe("block");
    });

    it("renders entry sub-cards with badges", async () => {
        const items = [
            makeMailer({
                entries: [makeEntry({ name: "tls-smtp", smtp_auth: true, use_tls: true, use_starttls: true, smtp_user: "admin@test.com" })],
            }),
        ];
        vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items }),
        } as Response);

        await loadMailers();
        const grid = document.getElementById("mailers-grid")!;
        expect(grid.innerHTML).toContain("tls-smtp");
        expect(grid.innerHTML).toContain("AUTH");
        expect(grid.innerHTML).toContain("TLS");
        expect(grid.innerHTML).toContain("STARTTLS");
        expect(grid.innerHTML).toContain("admin@test.com");
    });

    it("renders timeout feature badge", async () => {
        const items = [makeMailer({ timeout_mail: "10s" })];
        vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items }),
        } as Response);

        await loadMailers();
        const grid = document.getElementById("mailers-grid")!;
        expect(grid.innerHTML).toContain("10s");
    });

    it("shows toast on error", async () => {
        vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new Error("Mail error"));
        await loadMailers();
        expect(document.getElementById("toast-container")!.innerHTML).toContain("Mail error");
    });
});

describe("filterMailers", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allMailers = [
            makeMailer({ id: 1, name: "prod-mailers", comment: "production smtp" }),
            makeMailer({ id: 2, name: "dev-mailers", entries: [makeEntry({ name: "localhost-smtp" })] }),
        ];
    });

    it("filters by name", () => {
        (document.getElementById("mailer-search") as HTMLInputElement).value = "prod";
        filterMailers();
        const grid = document.getElementById("mailers-grid")!;
        expect(grid.innerHTML).toContain("prod-mailers");
        expect(grid.innerHTML).not.toContain("dev-mailers");
    });

    it("filters by comment", () => {
        (document.getElementById("mailer-search") as HTMLInputElement).value = "production";
        filterMailers();
        const grid = document.getElementById("mailers-grid")!;
        expect(grid.innerHTML).toContain("prod-mailers");
    });

    it("filters by entry name", () => {
        (document.getElementById("mailer-search") as HTMLInputElement).value = "localhost";
        filterMailers();
        const grid = document.getElementById("mailers-grid")!;
        expect(grid.innerHTML).toContain("dev-mailers");
        expect(grid.innerHTML).not.toContain("prod-mailers");
    });

    it("shows all when empty", () => {
        (document.getElementById("mailer-search") as HTMLInputElement).value = "";
        filterMailers();
        const grid = document.getElementById("mailers-grid")!;
        expect(grid.innerHTML).toContain("prod-mailers");
        expect(grid.innerHTML).toContain("dev-mailers");
    });
});

describe("openMailerModal", () => {
    it("opens create modal", () => {
        openMailerModal();
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("New Mailer Section");
    });

    it("opens edit modal", () => {
        openMailerModal(makeMailer({ name: "edit-mailer", timeout_mail: "30s" }));
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("Edit Mailer Section");
        expect(content.innerHTML).toContain("edit-mailer");
    });
});

describe("saveMailer", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        openMailerModal();
    });

    it("creates via POST", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "new-mailer";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 201,
            json: () => Promise.resolve({ id: 1 }),
        } as Response);
        await saveMailer(null);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/mailers");
    });

    it("updates via PUT", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "upd-mailer";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ id: 5 }),
        } as Response);
        await saveMailer(5);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/mailers/5");
        expect((fetchSpy.mock.calls[0][1] as any).method).toBe("PUT");
    });
});

describe("deleteMailer", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allMailers = [];
    });

    it("deletes after confirmation", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [] }),
        } as Response);
        await deleteMailer(3);
        expect(fetchSpy).toHaveBeenCalledWith("/api/mailers/3", expect.objectContaining({ method: "DELETE" }));
    });
});

describe("openMailerEntryModal", () => {
    it("opens create modal", () => {
        openMailerEntryModal(1);
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("New Mailer Entry");
    });

    it("opens edit modal", () => {
        openMailerEntryModal(1, makeEntry({ name: "edit-smtp", smtp_auth: true }));
        const content = document.getElementById("modal-content")!;
        expect(content.innerHTML).toContain("Edit Mailer Entry");
        expect(content.innerHTML).toContain("edit-smtp");
        expect(content.innerHTML).toContain("checked");
    });
});

describe("saveMailerEntry", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        openMailerEntryModal(1);
    });

    it("creates via POST", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "new-smtp";
        (document.getElementById("m-address") as HTMLInputElement).value = "smtp.test.com";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 201,
            json: () => Promise.resolve({ id: 1 }),
        } as Response);
        await saveMailerEntry(1, null);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/mailers/1/entries");
    });

    it("updates via PUT", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "upd-smtp";
        (document.getElementById("m-address") as HTMLInputElement).value = "smtp.test.com";
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ id: 7 }),
        } as Response);
        await saveMailerEntry(1, 7);
        expect(fetchSpy.mock.calls[0][0]).toBe("/api/mailers/1/entries/7");
    });

    it("includes smtp auth fields when checked", async () => {
        (document.getElementById("m-name") as HTMLInputElement).value = "auth-smtp";
        (document.getElementById("m-address") as HTMLInputElement).value = "smtp.test.com";
        (document.getElementById("m-smtp-auth") as HTMLInputElement).checked = true;
        (document.getElementById("m-smtp-user") as HTMLInputElement).value = "user@test.com";
        (document.getElementById("m-smtp-password") as HTMLInputElement).value = "secret";
        (document.getElementById("m-use-tls") as HTMLInputElement).checked = true;
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 201,
            json: () => Promise.resolve({ id: 1 }),
        } as Response);
        await saveMailerEntry(1, null);
        const body = JSON.parse((fetchSpy.mock.calls[0][1] as any).body);
        expect(body.smtp_auth).toBe(true);
        expect(body.smtp_user).toBe("user@test.com");
        expect(body.smtp_password).toBe("secret");
        expect(body.use_tls).toBe(true);
    });
});

describe("deleteMailerEntry", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML("beforeend", DOM);
        state.allMailers = [];
    });

    it("deletes after confirmation", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [] }),
        } as Response);
        await deleteMailerEntry(2, 5);
        expect(fetchSpy).toHaveBeenCalledWith("/api/mailers/2/entries/5", expect.objectContaining({ method: "DELETE" }));
    });
});
