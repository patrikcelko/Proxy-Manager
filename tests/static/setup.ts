/**
 * Vitest setup
 */
import { vi } from "vitest";

document.body.innerHTML = `
  <div id="auth-overlay" style="display:flex"></div>
  <div id="app-layout" style="display:none"></div>
  <div id="app-footer" style="display:none"></div>
  <div id="toast-container"></div>
  <div id="modal-overlay"><div id="modal-content"></div></div>
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
