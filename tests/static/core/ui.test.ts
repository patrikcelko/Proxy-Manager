/**
 * Tests UI
 * ========
 *
 * Covers switchSection, openModal, closeModal, initModalListeners,
 * toggleCollapsible, toggleEntityCard.
 */

import { describe, it, expect, beforeEach } from "vitest";
import { openModal, closeModal, toggleCollapsible, toggleEntityCard } from "@/core/ui";

describe("openModal / closeModal", () => {
    beforeEach(() => {
        const overlay = document.getElementById("modal-overlay")!;
        overlay.classList.remove("show");
        document.getElementById("modal-content")!.innerHTML = "";
    });

    it("opens the modal with content", () => {
        openModal("<p>Test</p>");
        expect(document.getElementById("modal-overlay")!.classList.contains("show")).toBe(true);
        expect(document.getElementById("modal-content")!.innerHTML).toContain("Test");
    });

    it("closes the modal", () => {
        openModal("<p>Test</p>");
        closeModal();
        expect(document.getElementById("modal-overlay")!.classList.contains("show")).toBe(false);
    });

    it("adds modal-wide class when opts.wide is true", () => {
        openModal("<p>Wide</p>", { wide: true });
        expect(document.getElementById("modal-content")!.classList.contains("modal-wide")).toBe(true);
    });

    it("removes modal-wide class when opts.wide is false", () => {
        openModal("<p>Wide</p>", { wide: true });
        openModal("<p>Normal</p>", { wide: false });
        expect(document.getElementById("modal-content")!.classList.contains("modal-wide")).toBe(false);
    });
});

describe("toggleCollapsible", () => {
    it("toggles open class on element and its next sibling", () => {
        document.body.insertAdjacentHTML("beforeend", '<div id="tc-head" class="form-collapsible-head">Head</div><div id="tc-body" class="form-collapsible-body">Body</div>');
        const head = document.getElementById("tc-head")!;
        const body = document.getElementById("tc-body")!;

        toggleCollapsible(head);
        expect(head.classList.contains("open")).toBe(true);
        expect(body.classList.contains("open")).toBe(true);

        toggleCollapsible(head);
        expect(head.classList.contains("open")).toBe(false);
        expect(body.classList.contains("open")).toBe(false);
    });
});

describe("toggleEntityCard", () => {
    it("toggles open class on closest entity-card", () => {
        document.body.insertAdjacentHTML("beforeend", '<div class="entity-card"><div id="ec-toggle">Toggle</div></div>');
        const toggle = document.getElementById("ec-toggle")!;
        const card = toggle.closest(".entity-card") as HTMLElement;

        toggleEntityCard(toggle);
        expect(card.classList.contains("open")).toBe(true);

        toggleEntityCard(toggle);
        expect(card.classList.contains("open")).toBe(false);
    });
});
