/**
 * Tests icons
 * ===========
 *
 */

import { describe, it, expect } from "vitest";
import { icon, SVG } from "@/core/icons";

describe("icon", () => {
    it("generates an svg element with use href", () => {
        const result = icon("edit-document");
        expect(result).toContain('<use href="#i-edit-document"/>');
        expect(result).toContain('width="14"');
        expect(result).toContain('height="14"');
        expect(result).toContain('stroke-width="2"');
    });

    it("accepts custom size and stroke-width", () => {
        const result = icon("trash", 20, 3);
        expect(result).toContain('width="20"');
        expect(result).toContain('height="20"');
        expect(result).toContain('stroke-width="3"');
    });

    it("includes class when provided", () => {
        const result = icon("chevron-down", 14, 2, "chevron");
        expect(result).toContain('class="chevron"');
    });

    it("omits class attribute when empty", () => {
        const result = icon("lock");
        expect(result).not.toContain("class=");
    });
});

describe("SVG constants", () => {
    it("has edit icon", () => {
        expect(SVG.edit).toContain("edit-document");
    });

    it("has delete icon", () => {
        expect(SVG.del).toContain("trash");
    });

    it("has plus icon", () => {
        expect(SVG.plus).toContain("plus");
    });

    it("has lock icon", () => {
        expect(SVG.lock).toContain("lock");
    });

    it("has copy icon", () => {
        expect(SVG.copy).toContain("copy");
    });

    it("has code icon", () => {
        expect(SVG.code).toContain("code");
    });

    it("editSm has smaller size", () => {
        expect(SVG.editSm).toContain('width="12"');
    });

    it("arrow uses different structure", () => {
        expect(SVG.arrow).toContain("arrow-right-narrow");
        expect(SVG.arrow).toContain('width="24"');
    });
});
