/**
 * Test types
 * ==========
 */

import { describe, it, expect } from "vitest";
import type {
    Frontend,
    FrontendBind,
    FrontendOption,
    Backend,
    BackendServer,
    AclRule,
    ListenBlock,
    ListenBlockBind,
    Userlist,
    UserlistEntry,
    Resolver,
    Nameserver,
    Peer,
    PeerEntry,
    Mailer,
    MailerEntry,
    HttpErrorGroup,
    HttpErrorEntry,
    Cache,
    SslCertificate,
    Setting,
    OverviewStats,
    UserProfile,
    BindPreset,
    SettingPreset,
} from "@/types";

describe("type interfaces", () => {
    it("Frontend with binds and options", () => {
        const bind: FrontendBind = { id: 1, bind_line: "0.0.0.0:443" };
        const opt: FrontendOption = { id: 1, directive: "option httplog", value: "" };
        const fe: Frontend = { id: 1, name: "web", mode: "http", default_backend: "app", binds: [bind], options: [opt] };
        expect(fe.name).toBe("web");
        expect(fe.binds![0].bind_line).toBe("0.0.0.0:443");
    });

    it("Backend with servers", () => {
        const srv: BackendServer = { id: 1, name: "app1", address: "10.0.0.1", port: 8080 };
        const be: Backend = { id: 1, name: "app", mode: "http", servers: [srv] };
        expect(be.servers![0].address).toBe("10.0.0.1");
    });

    it("AclRule", () => {
        const acl: AclRule = { id: 1, domain: "example.com", acl_match_type: "hdr", backend_name: "app" };
        expect(acl.domain).toBe("example.com");
    });

    it("ListenBlock with binds", () => {
        const bind: ListenBlockBind = { id: 1, bind_line: "0.0.0.0:9999" };
        const lb: ListenBlock = { id: 1, name: "stats", mode: "http", binds: [bind] };
        expect(lb.binds![0].bind_line).toBe("0.0.0.0:9999");
    });

    it("Userlist with entries", () => {
        const entry: UserlistEntry = { id: 1, username: "admin", has_password: true, sort_order: 0 };
        const ul: Userlist = { id: 1, name: "auth-users", entries: [entry] };
        expect(ul.entries![0].username).toBe("admin");
    });

    it("Resolver with nameservers", () => {
        const ns: Nameserver = { id: 1, name: "ns1", address: "8.8.8.8", port: 53 };
        const r: Resolver = {
            id: 1,
            name: "dns",
            hold_valid: "30s",
            hold_obsolete: "10s",
            hold_timeout: "5s",
            hold_refused: "5s",
            hold_aa: "0",
            parse_resolv_conf: 1,
            nameservers: [ns],
        };
        expect(r.nameservers![0].address).toBe("8.8.8.8");
        expect(r.parse_resolv_conf).toBe(1);
    });

    it("Peer with entries", () => {
        const pe: PeerEntry = { id: 1, name: "peer1", address: "10.0.0.2", port: 1024 };
        const p: Peer = { id: 1, name: "mypeers", entries: [pe] };
        expect(p.entries![0].name).toBe("peer1");
    });

    it("Mailer with entries", () => {
        const me: MailerEntry = { id: 1, name: "smtp1", address: "mail.example.com", port: 587, smtp_auth: true, use_tls: true };
        const m: Mailer = { id: 1, name: "alerts", entries: [me] };
        expect(m.entries![0].smtp_auth).toBe(true);
    });

    it("HttpErrorGroup with entries", () => {
        const entry: HttpErrorEntry = { id: 1, status_code: 503, type: "errorfile", value: "/etc/haproxy/errors/503.http" };
        const g: HttpErrorGroup = { id: 1, name: "default-errors", entries: [entry] };
        expect(g.entries![0].status_code).toBe(503);
    });

    it("Cache with process_vary as number", () => {
        const c: Cache = { id: 1, name: "mycache", total_max_size: 100, process_vary: 1 };
        expect(c.process_vary).toBe(1);
    });

    it("SslCertificate with all fields", () => {
        const ssl: SslCertificate = {
            id: 1,
            domain: "example.com",
            alt_domains: "www.example.com, api.example.com",
            email: "admin@example.com",
            provider: "certbot",
            status: "active",
            challenge_type: "http-01",
            cert_path: "/etc/letsencrypt/live/example.com/cert.pem",
            key_path: "/etc/letsencrypt/live/example.com/privkey.pem",
            fullchain_path: "/etc/letsencrypt/live/example.com/fullchain.pem",
            issued_at: "2024-01-01T00:00:00",
            expires_at: "2024-04-01T00:00:00",
            auto_renew: true,
            dns_plugin: null,
            last_renewal_at: null,
            last_error: null,
            comment: "Production cert",
        };
        expect(ssl.domain).toBe("example.com");
        expect(ssl.fullchain_path).toContain("fullchain");
        expect(ssl.challenge_type).toBe("http-01");
    });

    it("Setting", () => {
        const s: Setting = { id: 1, directive: "maxconn", value: "4096", type: "global", sort_order: 0, category: "performance" };
        expect(s.directive).toBe("maxconn");
    });

    it("OverviewStats", () => {
        const o: OverviewStats = {
            global_settings: 1, default_settings: 2, frontends: 5, backends: 3,
            backend_servers: 8, acl_rules: 10, listen_blocks: 2, userlists: 1,
            resolvers: 1, peers: 0, mailers: 0, http_errors: 1, caches: 1, ssl_certificates: 2,
        };
        expect(o.frontends).toBe(5);
    });

    it("UserProfile", () => {
        const u: UserProfile = { id: 1, name: "Admin", email: "admin@test.com" };
        expect(u.name).toBe("Admin");
    });

    it("BindPreset", () => {
        const bp: BindPreset = { cat: "ssl", line: "0.0.0.0:443 ssl", h: "Standard HTTPS" };
        expect(bp.line).toBe("0.0.0.0:443 ssl");
    });

    it("SettingPreset", () => {
        const sp: SettingPreset = { d: "maxconn", v: "4096", h: "Max connections", c: "performance" };
        expect(sp.d).toBe("maxconn");
    });
});
