/**
 * Tests config import/export section
 * ==================================
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { exportConfig, copyExport } from "@/sections/config";

describe("exportConfig", () => {
    let container: HTMLDivElement;
    beforeEach(() => {
        container = document.createElement("div");
        container.innerHTML = '<textarea id="config-export-text"></textarea><div id="toast-container"></div>';
        document.body.appendChild(container);
        vi.restoreAllMocks();
    });
    afterEach(() => container.remove());

    it("fills textarea with exported config", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ config_text: "global\n  maxconn 4096" }),
        } as Response);

        await exportConfig();
        expect((document.getElementById("config-export-text") as HTMLTextAreaElement).value).toBe("global\n  maxconn 4096");
    });
});

describe("copyExport", () => {
    let container: HTMLDivElement;
    beforeEach(() => {
        Object.assign(navigator, {
            clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
        });
        container = document.createElement("div");
        container.innerHTML = '<textarea id="config-export-text">test config</textarea><div id="toast-container"></div>';
        document.body.appendChild(container);
    });
    afterEach(() => container.remove());

    it("copies textarea content to clipboard", async () => {
        await copyExport();
        expect(navigator.clipboard.writeText).toHaveBeenCalledWith("test config");
    });
});
