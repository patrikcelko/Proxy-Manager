/**
 * State tests
 * ===========
 */

import { describe, it, expect } from "vitest";
import { state } from "@/state";

describe("state", () => {
    it("has all expected arrays initialized empty", () => {
        const arrayKeys = [
            "allFrontends",
            "allBackends",
            "allAclRules",
            "allListenBlocks",
            "allUserlists",
            "allResolvers",
            "allPeers",
            "allMailers",
            "allHttpErrors",
            "allCaches",
            "allSslCertificates",
        ];
        for (const key of arrayKeys) {
            expect(Array.isArray((state as any)[key])).toBe(true);
            expect((state as any)[key].length).toBe(0);
        }
    });

    it("has cachedUserlists initially null", () => {
        expect(state.cachedUserlists).toBeNull();
    });

    it("has currentUser initially null", () => {
        expect(state.currentUser).toBeNull();
    });

    it("allows mutation of arrays", () => {
        state.allFrontends = [{ id: 1, name: "fe1" } as any];
        expect(state.allFrontends.length).toBe(1);
        expect(state.allFrontends[0].name).toBe("fe1");
        state.allFrontends = [];
    });
});
