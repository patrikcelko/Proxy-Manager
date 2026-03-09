/**
 * Vitest setup
 * ============
 */
import { vi } from "vitest";

document.body.innerHTML = `
  <div id="auth-overlay" style="display:flex"></div>
  <div id="setup-overlay" style="display:none"></div>
  <div id="app-layout" style="display:none"></div>
  <div id="app-footer" style="display:none"></div>
  <div id="toast-container"></div>
  <div id="modal-overlay"><div id="modal-content"></div></div>
  <div id="confirm-overlay">
    <div class="confirm-dialog">
      <h4 id="confirm-title">Confirm</h4>
      <p id="confirm-message"></p>
      <div class="confirm-actions">
        <button id="confirm-cancel">Cancel</button>
        <button id="confirm-ok">Confirm</button>
      </div>
    </div>
  </div>
  <div id="sidebar"><button id="sidebar-collapse-btn"></button></div>
  <div id="sidebar-backdrop"></div>
  <div id="top-bar-page-title"></div>
  <div id="top-bar-user"></div>
  <div id="user-dropdown"></div>
  <div id="user-name"></div>
  <div id="user-avatar"></div>
  <div id="dropdown-user-name"></div>
  <div id="dropdown-user-email"></div>
`;

Object.assign(navigator, {
    clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
        readText: vi.fn().mockResolvedValue(""),
    },
});

window.confirm = vi.fn(() => true);

// Mock confirmPopup globally - inject a resolvable promise so delete/discard
// tests don't hang waiting for user interaction.
const _confirmPopupMock = vi.fn((): Promise<boolean> => Promise.resolve(true));

vi.mock("@/core/ui", async () => {
    // We cannot use importOriginal here because ui.ts has circular imports with
    // every section module. Instead, provide the handful of exports that the
    // production code actually calls and let vi.fn() stubs handle the rest.
    return {
        confirmPopup: _confirmPopupMock,
        openModal: vi.fn((html: string, opts?: { wide?: boolean }) => {
            const m = document.getElementById("modal-content")!;
            m.innerHTML = html;
            m.classList.toggle("modal-wide", !!opts?.wide);
            document.getElementById("modal-overlay")!.classList.add("show");
        }),
        closeModal: vi.fn(() => {
            document.getElementById("modal-overlay")?.classList.remove("show");
        }),
        switchSection: vi.fn(),
        toggleCollapsible: vi.fn((el: HTMLElement) => {
            el.classList.toggle("open");
            (el.nextElementSibling as HTMLElement | null)?.classList.toggle("open");
        }),
        toggleEntityCard: vi.fn((el: HTMLElement) => {
            el.closest(".entity-card")?.classList.toggle("open");
        }),
        initModalListeners: vi.fn(),
        icon: vi.fn(() => ""),
    };
});

// Expose so individual tests can switch confirmPopup to return false
(globalThis as any).__confirmPopupMock = _confirmPopupMock;

// Polyfill methods not available in jsdom
Element.prototype.scrollIntoView = vi.fn();
if (typeof CSS === "undefined") {
    (globalThis as any).CSS = { escape: (s: string) => s.replace(/([^\w-])/g, "\\$1") };
} else if (!CSS.escape) {
    CSS.escape = (s: string) => s.replace(/([^\w-])/g, "\\$1");
}
