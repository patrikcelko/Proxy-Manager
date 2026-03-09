/**
 * Tests manual edit section (config)
 * ====================================
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { exportConfig, copyExport, loadManualEdit, saveManualEdit, discardManualEdit } from "@/sections/config";

const DOM = `
    <textarea id="config-export-text"></textarea>
    <div id="manual-edit-version-bar" style="display:none"></div>
    <span id="mev-label"></span>
    <div id="config-validation-msg" style="display:none"></div>
    <div id="toast-container"></div>
`;

describe("loadManualEdit / exportConfig", () => {
    let container: HTMLDivElement;
    beforeEach(() => {
        container = document.createElement("div");
        container.innerHTML = DOM;
        document.body.appendChild(container);
        vi.restoreAllMocks();
    });
    afterEach(() => container.remove());

    it("fills textarea with exported config", async () => {
        vi.spyOn(globalThis, "fetch").mockImplementation((url) => {
            const u = typeof url === "string" ? url : (url as Request).url;
            if (u.includes("/api/config/export")) {
                return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ config_text: "global\n  maxconn 4096" }) } as Response);
            }
            if (u.includes("/api/versions/status")) {
                return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ current_hash: "abc12345def" }) } as Response);
            }
            return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) } as Response);
        });

        await exportConfig();
        expect((document.getElementById("config-export-text") as HTMLTextAreaElement).value).toBe("global\n  maxconn 4096");
    });

    it("shows version bar with hash", async () => {
        vi.spyOn(globalThis, "fetch").mockImplementation((url) => {
            const u = typeof url === "string" ? url : (url as Request).url;
            if (u.includes("/api/config/export")) {
                return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ config_text: "defaults\n  mode http" }) } as Response);
            }
            if (u.includes("/api/versions/status")) {
                return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ current_hash: "abcdef1234567890" }) } as Response);
            }
            return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) } as Response);
        });

        await loadManualEdit();
        const label = document.getElementById("mev-label")!;
        expect(label.textContent).toContain("abcdef12");
    });
});

describe("copyExport", () => {
    let container: HTMLDivElement;
    beforeEach(() => {
        Object.assign(navigator, {
            clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
        });
        container = document.createElement("div");
        container.innerHTML = DOM;
        document.body.appendChild(container);
        (document.getElementById("config-export-text") as HTMLTextAreaElement).value = "test config";
    });
    afterEach(() => container.remove());

    it("copies textarea content to clipboard", async () => {
        await copyExport();
        expect(navigator.clipboard.writeText).toHaveBeenCalledWith("test config");
    });

    it("shows error when textarea is empty", () => {
        (document.getElementById("config-export-text") as HTMLTextAreaElement).value = "";
        copyExport();
        const toasts = document.getElementById("toast-container")!;
        expect(toasts.textContent).toContain("Nothing to copy");
    });
});

describe("saveManualEdit", () => {
    let container: HTMLDivElement;
    beforeEach(() => {
        container = document.createElement("div");
        container.innerHTML = DOM;
        document.body.appendChild(container);
        vi.restoreAllMocks();
    });
    afterEach(() => container.remove());

    it("shows error when textarea is empty", async () => {
        (document.getElementById("config-export-text") as HTMLTextAreaElement).value = "";
        await saveManualEdit();
        const msg = document.getElementById("config-validation-msg")!;
        expect(msg.style.display).toBe("block");
        expect(msg.textContent).toContain("empty");
    });
});

describe("discardManualEdit", () => {
    let container: HTMLDivElement;
    beforeEach(() => {
        container = document.createElement("div");
        container.innerHTML = DOM;
        document.body.appendChild(container);
        vi.restoreAllMocks();
    });
    afterEach(() => container.remove());

    it("resets validation message", async () => {
        const msg = document.getElementById("config-validation-msg")!;
        msg.style.display = "block";
        msg.textContent = "Some error";

        await discardManualEdit();

        expect(msg.style.display).toBe("none");
    });
});
