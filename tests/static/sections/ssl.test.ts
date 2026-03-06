/**
 * Tests SSL certificates section
 * ==============================
 *
 * Covers renderSslCertificates, filterSslCertificates, and helper functions.
 */

import { describe, it, expect, beforeEach } from "vitest";
import { state } from "@/state";
import type { SslCertificate } from "@/types";

/* Must import after state so module-level references resolve */
import { renderSslCertificates, filterSslCertificates, autofillCertPaths, toggleDnsPlugin, switchDomainTab, addAltDomain, removeAltDomain } from "@/sections/ssl";

const makeCert = (overrides: Partial<SslCertificate> = {}): SslCertificate => ({
    id: 1,
    domain: "example.com",
    alt_domains: null,
    email: "admin@example.com",
    provider: "certbot",
    status: "active",
    challenge_type: "http-01",
    cert_path: "/etc/letsencrypt/live/example.com/cert.pem",
    key_path: "/etc/letsencrypt/live/example.com/privkey.pem",
    fullchain_path: "/etc/letsencrypt/live/example.com/fullchain.pem",
    issued_at: "2024-01-01T00:00:00",
    expires_at: "2025-01-01T00:00:00",
    auto_renew: true,
    dns_plugin: null,
    last_renewal_at: null,
    last_error: null,
    comment: null,
    ...overrides,
});

describe("renderSslCertificates", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML(
            "beforeend",
            `
      <div id="ssl-certificates-grid"></div>
      <div id="ssl-certificates-empty" style="display:none"></div>
    `,
        );
    });

    it("shows empty state when list is empty", () => {
        renderSslCertificates([]);
        expect(document.getElementById("ssl-certificates-grid")!.innerHTML).toBe("");
        expect(document.getElementById("ssl-certificates-empty")!.style.display).toBe("block");
    });

    it("renders certificate cards", () => {
        renderSslCertificates([makeCert()]);
        const grid = document.getElementById("ssl-certificates-grid")!;
        expect(grid.style.display).toBe("grid");
        expect(grid.querySelectorAll(".item-card").length).toBe(1);
        expect(grid.innerHTML).toContain("example.com");
    });

    it("renders alt domains as chips", () => {
        renderSslCertificates([makeCert({ alt_domains: "www.example.com, api.example.com" })]);
        const chips = document.querySelectorAll(".sc-domain-chip");
        expect(chips.length).toBe(2);
    });

    it("shows auto-renew badge", () => {
        renderSslCertificates([makeCert({ auto_renew: true })]);
        expect(document.querySelector(".sc-feat-autorenew")).toBeTruthy();
    });

    it("shows no-renew badge when auto_renew is false", () => {
        renderSslCertificates([makeCert({ auto_renew: false })]);
        expect(document.querySelector(".sc-feat-norenew")).toBeTruthy();
    });

    it("shows last error section", () => {
        renderSslCertificates([makeCert({ last_error: "Connection refused" })]);
        expect(document.querySelector(".sc-error-section")).toBeTruthy();
        expect(document.querySelector(".sc-error-text")!.textContent).toContain("Connection refused");
    });

    it("shows wildcard badge for wildcard domains", () => {
        renderSslCertificates([makeCert({ domain: "*.example.com" })]);
        expect(document.querySelector(".sc-feat-wildcard")).toBeTruthy();
    });

    it("shows dns plugin badge", () => {
        renderSslCertificates([makeCert({ dns_plugin: "cloudflare", challenge_type: "dns-01" })]);
        expect(document.querySelector(".sc-feat-dns")).toBeTruthy();
    });

    it("shows certificate paths", () => {
        renderSslCertificates([makeCert()]);
        expect(document.querySelector(".sc-paths-section")).toBeTruthy();
        const paths = document.querySelectorAll(".sc-path-item");
        expect(paths.length).toBe(3);
    });

    it("shows comment as note", () => {
        renderSslCertificates([makeCert({ comment: "Test note" })]);
        expect(document.querySelector(".sc-comment")).toBeTruthy();
        expect(document.querySelector(".sc-comment")!.textContent).toContain("Test note");
    });
});

describe("filterSslCertificates", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML(
            "beforeend",
            `
      <input id="ssl-search" value="">
      <div id="ssl-certificates-grid"></div>
      <div id="ssl-certificates-empty" style="display:none"></div>
    `,
        );
        state.allSslCertificates = [makeCert({ id: 1, domain: "example.com" }), makeCert({ id: 2, domain: "other.org", provider: "manual" })];
    });

    it("filters by domain", () => {
        (document.getElementById("ssl-search") as HTMLInputElement).value = "other";
        filterSslCertificates();
        const cards = document.querySelectorAll("#ssl-certificates-grid .item-card");
        expect(cards.length).toBe(1);
    });

    it("shows all when search is empty", () => {
        (document.getElementById("ssl-search") as HTMLInputElement).value = "";
        filterSslCertificates();
        const cards = document.querySelectorAll("#ssl-certificates-grid .item-card");
        expect(cards.length).toBe(2);
    });
});

describe("autofillCertPaths", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML(
            "beforeend",
            `
      <div id="toast-container"></div>
      <input id="m-domain" value="example.com">
      <input id="m-cert-path" value="">
      <input id="m-key-path" value="">
      <input id="m-fullchain-path" value="">
    `,
        );
    });

    it("fills paths based on domain", () => {
        autofillCertPaths();
        expect((document.getElementById("m-cert-path") as HTMLInputElement).value).toBe("/etc/letsencrypt/live/example.com/cert.pem");
        expect((document.getElementById("m-key-path") as HTMLInputElement).value).toBe("/etc/letsencrypt/live/example.com/privkey.pem");
        expect((document.getElementById("m-fullchain-path") as HTMLInputElement).value).toBe("/etc/letsencrypt/live/example.com/fullchain.pem");
    });

    it("strips wildcard prefix from path", () => {
        (document.getElementById("m-domain") as HTMLInputElement).value = "*.example.com";
        autofillCertPaths();
        expect((document.getElementById("m-cert-path") as HTMLInputElement).value).toContain("/example.com/");
        expect((document.getElementById("m-cert-path") as HTMLInputElement).value).not.toContain("*.");
    });
});

describe("toggleDnsPlugin", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML(
            "beforeend",
            `
      <select id="m-challenge-type"><option value="http-01" selected>HTTP-01</option><option value="dns-01">DNS-01</option></select>
      <div id="dns-plugin-wrap" style="display:none"></div>
    `,
        );
    });

    it("shows dns plugin wrap when dns-01 is selected", () => {
        (document.getElementById("m-challenge-type") as HTMLSelectElement).value = "dns-01";
        toggleDnsPlugin();
        expect((document.getElementById("dns-plugin-wrap") as HTMLElement).style.display).toBe("block");
    });

    it("hides dns plugin wrap when not dns-01", () => {
        (document.getElementById("m-challenge-type") as HTMLSelectElement).value = "http-01";
        toggleDnsPlugin();
        expect((document.getElementById("dns-plugin-wrap") as HTMLElement).style.display).toBe("none");
    });
});

describe("switchDomainTab", () => {
    beforeEach(() => {
        document.body.insertAdjacentHTML(
            "beforeend",
            `
      <div class="sc-domain-picker">
        <button class="sc-domain-picker-tab active">Custom</button>
        <button class="sc-domain-picker-tab">ACL</button>
      </div>
      <div id="sc-domain-custom" style="display:block"></div>
      <div id="sc-domain-acl" style="display:none"></div>
    `,
        );
    });

    it("switches to ACL tab", () => {
        switchDomainTab("acl");
        expect((document.getElementById("sc-domain-acl") as HTMLElement).style.display).toBe("block");
        expect((document.getElementById("sc-domain-custom") as HTMLElement).style.display).toBe("none");
    });

    it("switches to custom tab", () => {
        switchDomainTab("acl");
        switchDomainTab("custom");
        expect((document.getElementById("sc-domain-custom") as HTMLElement).style.display).toBe("block");
        expect((document.getElementById("sc-domain-acl") as HTMLElement).style.display).toBe("none");
    });
});

describe("addAltDomain / removeAltDomain", () => {
    beforeEach(() => {
        // Clean up any previous test elements
        document.querySelectorAll("#m-alt-domain-input, #sc-alt-domains-list").forEach((el) => el.remove());
        document.body.insertAdjacentHTML(
            "beforeend",
            `
      <input id="m-alt-domain-input" value="new.example.com">
      <div id="sc-alt-domains-list"></div>
    `,
        );
    });

    it("adds a domain tag", () => {
        addAltDomain();
        const tags = document.querySelectorAll("#sc-alt-domains-list .sc-alt-domain-tag");
        expect(tags.length).toBe(1);
        expect(tags[0].textContent).toContain("new.example.com");
        expect((document.getElementById("m-alt-domain-input") as HTMLInputElement).value).toBe("");
    });

    it("does not add duplicate", () => {
        addAltDomain();
        (document.getElementById("m-alt-domain-input") as HTMLInputElement).value = "new.example.com";
        addAltDomain();
        expect(document.querySelectorAll("#sc-alt-domains-list .sc-alt-domain-tag").length).toBe(1);
    });

    it("does not add empty input", () => {
        (document.getElementById("m-alt-domain-input") as HTMLInputElement).value = "";
        addAltDomain();
        expect(document.querySelectorAll("#sc-alt-domains-list .sc-alt-domain-tag").length).toBe(0);
    });

    it("removes a domain tag", () => {
        addAltDomain();
        const removeBtn = document.querySelector("#sc-alt-domains-list .remove-tag") as HTMLElement;
        removeAltDomain(removeBtn);
        expect(document.querySelectorAll("#sc-alt-domains-list .sc-alt-domain-tag").length).toBe(0);
    });
});
