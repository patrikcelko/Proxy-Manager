/**
 * Overview / Dashboard Section
 * ============================
 *
 * Displays stat cards with entity counts and renders a flow
 * topology diagram showing the traffic path from clients through
 * frontends, ACL rules, auth, backends to servers, plus auxiliary
 * service nodes (resolvers, peers, mailers, caches, http-errors,
 * SSL certificates).
 */

import { api, toast } from "../core/api";
import { icon } from "../core/icons";
import { switchSection } from "../core/ui";
import { escHtml } from "../core/utils";
import type { FlowPoint, StatCardItem } from "../types";

/* Connection graph (built during drawFlowConnections)  */

/** Map from nodeId -> set of directly connected nodeIds. */
let _graph: Record<string, Set<string>> = {};

/** AbortController for hover listeners – prevents stacking on re-render. */
let _hoverAC: AbortController | null = null;

/** Loads overview stats from the API and renders stat cards and the flow canvas. */
export async function loadOverview(): Promise<void> {
    try {
        const d = await api("/api/overview");
        const items: StatCardItem[] = [
            { key: "global_settings", label: "Global Settings", section: "global", color: "var(--accent)", icon: "settings" },
            { key: "default_settings", label: "Default Settings", section: "defaults", color: "var(--info)", icon: "edit-pen" },
            { key: "frontends", label: "Frontends", section: "frontends", color: "var(--ok)", icon: "globe" },
            { key: "backends", label: "Backends", section: "backends", color: "var(--warn)", icon: "server" },
            { key: "backend_servers", label: "Backend Servers", section: "backends", color: "#a78bfa", icon: "cluster" },
            { key: "acl_rules", label: "ACL Rules", section: "acl", color: "var(--danger)", icon: "routing" },
            { key: "listen_blocks", label: "Listen Blocks", section: "listen", color: "#f472b6", icon: "activity" },
            { key: "userlists", label: "Auth Lists", section: "userlists", color: "#34d399", icon: "users" },
            { key: "resolvers", label: "Resolvers", section: "resolvers", color: "#60a5fa", icon: "clock" },
            { key: "peers", label: "Peers", section: "peers", color: "#c084fc", icon: "rss" },
            { key: "mailers", label: "Mailers", section: "mailers", color: "#fbbf24", icon: "mail" },
            { key: "http_errors", label: "HTTP Errors", section: "http-errors", color: "#fb923c", icon: "alert-triangle" },
            { key: "caches", label: "Caches", section: "caches", color: "#2dd4bf", icon: "activity" },
            { key: "ssl_certificates", label: "SSL Certificates", section: "ssl-certificates", color: "#22d3ee", icon: "shield" },
        ];
        document.getElementById("overview-grid")!.innerHTML = items
            .map(
                (i) => `
      <div class="stat-card" onclick="switchSection('${i.section}')">
        <div class="stat-number" style="color:${i.color}">${(d as any)[i.key] || 0}</div>
        <div class="stat-label">${icon(i.icon, 12, 2)} ${i.label}</div>
      </div>
    `,
            )
            .join("");

        document.getElementById("overview-charts")!.innerHTML = "";
        renderFlowCanvas();
    } catch (err) {
        toast((err as Error).message, "error");
    }
}

/*  Flow Canvas   */

/** Renders the full traffic flow topology diagram. */
export async function renderFlowCanvas(): Promise<void> {
    try {
        const [feRes, beRes, aclRes, listenRes, ulRes, resRes, peerRes, mailerRes, heRes, cacheRes, sslRes]: any[] =
            await Promise.all([
                api("/api/frontends").catch(() => []),
                api("/api/backends").catch(() => []),
                api("/api/acl-rules").catch(() => []),
                api("/api/listen-blocks").catch(() => []),
                api("/api/userlists").catch(() => []),
                api("/api/resolvers").catch(() => []),
                api("/api/peers").catch(() => []),
                api("/api/mailers").catch(() => []),
                api("/api/http-errors").catch(() => []),
                api("/api/caches").catch(() => []),
                api("/api/ssl-certificates").catch(() => []),
            ]);
        const fes: any[] = feRes.items || feRes || [];
        const bes: any[] = beRes.items || beRes || [];
        const acls: any[] = aclRes.items || aclRes || [];
        const listens: any[] = listenRes.items || listenRes || [];
        const userlists: any[] = ulRes.items || ulRes || [];
        const resolvers: any[] = resRes.items || resRes || [];
        const peers: any[] = peerRes.items || peerRes || [];
        const mailers: any[] = mailerRes.items || mailerRes || [];
        const httpErrors: any[] = heRes.items || heRes || [];
        const caches: any[] = cacheRes.items || cacheRes || [];
        const sslCerts: any[] = sslRes.items || sslRes || [];

        const container = document.getElementById("overview-flow")!;

        /* Sort ACLs by frontend position  */
        const feIndex: Record<string, number> = {};
        fes.forEach((f: any, i: number) => {
            feIndex[String(f.id)] = i;
        });

        const sortedAcls = [...acls].sort((a: any, b: any) => {
            const fa = feIndex[String(a.frontend_id)] ?? 9999;
            const fb = feIndex[String(b.frontend_id)] ?? 9999;
            if (fa !== fb) return fa - fb;
            return (a.domain || "").localeCompare(b.domain || "");
        });

        /* Order backends to match ACL / frontend references  */
        const beOrder: any[] = [];
        const beAdded = new Set<string>();
        sortedAcls.forEach((a: any) => {
            const n = a.backend_name;
            if (n && !beAdded.has(n)) {
                const be = bes.find((b: any) => b.name === n);
                if (be) { beOrder.push(be); beAdded.add(n); }
            }
        });
        fes.forEach((f: any) => {
            const n = f.default_backend;
            if (n && !beAdded.has(n)) {
                const be = bes.find((b: any) => b.name === n);
                if (be) { beOrder.push(be); beAdded.add(n); }
            }
        });
        bes.forEach((b: any) => {
            if (!beAdded.has(b.name)) { beOrder.push(b); beAdded.add(b.name); }
        });

        /* Collect resolver names referenced by servers  */
        const usedResolvers = new Set<string>();
        beOrder.forEach((b: any) => {
            (b.servers || []).forEach((s: any) => {
                if (s.resolvers_ref) usedResolvers.add(s.resolvers_ref);
            });
        });

        /*  Build node HTML   */

        const clientCol = `<div class="flow-node client" data-node-id="client">
      <div class="fn-name">${icon("globe", 8)} Incoming Traffic</div>
      <div class="fn-detail">HTTP / HTTPS / TCP</div>
    </div>`;

        const listenCol = listens
            .map(
                (l: any) => `<div class="flow-node listen-n" data-node-id="listen-${escHtml(l.name)}">
          <div class="fn-name">${icon("activity", 8)} ${escHtml(l.name)}</div>
          <div class="fn-detail">${(l.binds || []).map((b: any) => b.bind_line).join(", ") || "no bind"} &bull; ${escHtml(l.mode || "tcp")}</div>
        </div>`,
            )
            .join("");

        const feCol = fes.length
            ? fes
                .map((f: any) => {
                    const hasSSL = (f.binds || []).some((b: any) => /ssl\b/.test(b.bind_line || ""));
                    const hasAuth = (f.options || []).some((o: any) => /http-request\s+auth/.test(o.directive || ""));
                    const badges = [
                        hasSSL ? `<span class="fn-badge fn-badge-ssl" title="SSL/TLS">${icon("lock", 9)}</span>` : "",
                        hasAuth ? `<span class="fn-badge fn-badge-auth" title="Auth required">${icon("lock", 9)}</span>` : "",
                    ].filter(Boolean).join("");
                    const mode = (f.mode || "http").toLowerCase();
                    const ports = Array.from(new Set<string>((f.binds || []).flatMap((b: any) => {
                        const matches = (b.bind_line || "").match(/:(\d+)/g) || [];
                        return matches.map((m: string) => m.slice(1));
                    }))).sort((a, b) => Number(a) - Number(b));
                    const pills: string[] = [];
                    pills.push(`<span class="fn-mode-pill fn-mode-${escHtml(mode)}">${escHtml(mode)}</span>`);
                    if (f.option_forwardfor) pills.push(`<span class="fn-mode-pill fn-mode-fwd">X-Fwd-For</span>`);
                    if (ports.length) pills.push(`<span class="fn-mode-pill fn-mode-port">${ports.join(", ")}</span>`);
                    return `<div class="flow-node fe" data-node-id="fe-${f.id}" data-id="${f.id}" data-default-backend="${escHtml(f.default_backend || "")}">
          <div class="fn-name">${icon("globe", 8)} ${escHtml(f.name)}${badges}</div>
          <div class="fn-detail">${pills.join(" ")}</div>
        </div>`;
                })
                .join("")
            : '<div class="flow-empty-col">No frontends</div>';

        const aclCol = sortedAcls.length
            ? sortedAcls
                .map(
                    (a: any, idx: number) => {
                        const matchType = escHtml(a.acl_match_type || "hdr");
                        const detail = a.is_redirect
                            ? `<span class="fn-mode-pill fn-mode-redirect">${icon("redirect", 8)} ${a.redirect_code || 301}</span>`
                            : `<span class="fn-mode-pill fn-mode-backend">${icon("server", 8)}</span>`;
                        return `<div class="flow-node acl" data-node-id="acl-${idx}" data-backend="${escHtml(a.backend_name || "")}" data-fid="${a.frontend_id || ""}">
          <div class="fn-name">${icon("routing", 8)} ${escHtml(a.domain)}</div>
          <div class="fn-detail"><span class="fn-mode-pill fn-mode-match">${matchType}</span> ${detail}</div>
        </div>`;
                    },
                )
                .join("")
            : '<div class="flow-empty-col">No ACL rules</div>';

        const authCol = userlists.length
            ? userlists
                .map(
                    (u: any) =>
                        `<div class="flow-node auth-ul" data-node-id="auth-${escHtml(u.name)}" data-name="${escHtml(u.name)}" style="border-left-color:#f472b6">
          <div class="fn-name">${icon("users", 8)} ${escHtml(u.name)}</div>
          <div class="fn-detail">${(u.entries || []).length} user(s)</div>
        </div>`,
                )
                .join("")
            : "";

        const beCol = beOrder.length
            ? beOrder
                .map((b: any) => {
                    const badges = [
                        b.auth_userlist
                            ? `<span class="fn-badge fn-badge-auth" title="Auth: ${escHtml(b.auth_userlist)}">${icon("lock", 9)}</span>`
                            : "",
                        b.health_check_enabled
                            ? `<span class="fn-badge fn-badge-health" title="Health check">${icon("activity", 9)}</span>`
                            : "",
                    ].filter(Boolean).join("");
                    const mode = (b.mode || "http").toLowerCase();
                    const srvCount = (b.servers || []).length;
                    const pills: string[] = [];
                    pills.push(`<span class="fn-mode-pill fn-mode-${escHtml(mode)}">${escHtml(mode)}</span>`);
                    if (b.option_forwardfor) pills.push(`<span class="fn-mode-pill fn-mode-fwd">X-Fwd-For</span>`);
                    return `<div class="flow-node be" data-node-id="be-${escHtml(b.name)}" data-name="${escHtml(b.name)}" data-auth="${escHtml(b.auth_userlist || "")}">
          <div class="fn-name">${icon("server", 8)} ${escHtml(b.name)}${badges}</div>
          <div class="fn-detail">${icon("balance", 8)} ${pills.join(" ")} ${icon("cluster", 8)} ${srvCount}</div>
        </div>`;
                })
                .join("")
            : '<div class="flow-empty-col">No backends</div>';

        const srvCol = beOrder.length
            ? beOrder
                .flatMap((b: any) =>
                    (b.servers || []).map(
                        (s: any) =>
                            `<div class="flow-node srv" data-node-id="srv-${escHtml(b.name)}-${escHtml(s.name)}" data-backend="${escHtml(b.name)}" data-resolver="${escHtml(s.resolvers_ref || "")}">
            <div class="fn-name">${icon("cluster", 8)} ${escHtml(s.name)}</div>
            <div class="fn-detail">${escHtml(s.address)}:${s.port}${s.resolvers_ref ? " &bull; " + icon("clock", 9) + " " + escHtml(s.resolvers_ref) : ""}</div>
          </div>`,
                    ),
                )
                .join("") || '<div class="flow-empty-col">No servers</div>'
            : '<div class="flow-empty-col">No servers</div>';

        /* Resolvers row (only those referenced by servers)  */
        const activeResolvers = resolvers.filter((r: any) => usedResolvers.has(r.name));
        const resolverCol = activeResolvers.length
            ? activeResolvers
                .map(
                    (r: any) =>
                        `<div class="flow-node resolver" data-node-id="res-${escHtml(r.name)}" data-name="${escHtml(r.name)}">
          <div class="fn-name">${icon("clock", 8)} ${escHtml(r.name)}</div>
          <div class="fn-detail">${(r.nameservers || []).length} nameserver(s)</div>
        </div>`,
                )
                .join("")
            : "";

        /* Unreferenced resolvers go to services  */
        const unrefResolvers = resolvers.filter((r: any) => !usedResolvers.has(r.name));

        /* Services row (standalone / auxiliary sections)  */
        const serviceNodes: string[] = [];

        unrefResolvers.forEach((r: any) => {
            const nsCnt = (r.nameservers || []).length;
            const pills: string[] = [];
            if (r.timeout_resolve) pills.push(`<span class="fn-mode-pill fn-mode-port">${escHtml(r.timeout_resolve)}</span>`);
            pills.push(`<span class="fn-mode-pill fn-mode-match">${icon("server", 8)} ${nsCnt}</span>`);
            serviceNodes.push(
                `<div class="flow-node resolver svc-node" data-node-id="res-${escHtml(r.name)}" data-name="${escHtml(r.name)}">
        <div class="fn-name">${icon("clock", 8)} ${escHtml(r.name)}</div>
        <div class="fn-detail">${pills.join(" ")}</div>
      </div>`,
            );
        });

        peers.forEach((p: any) => {
            const entryCnt = (p.entries || []).length;
            const ports = [...new Set((p.entries || []).map((e: any) => String(e.port)))].sort();
            const pills: string[] = [];
            pills.push(`<span class="fn-mode-pill fn-mode-http">${icon("rss", 8)} ${entryCnt}</span>`);
            if (ports.length) pills.push(`<span class="fn-mode-pill fn-mode-port">${ports.join(", ")}</span>`);
            serviceNodes.push(
                `<div class="flow-node peer svc-node" data-node-id="peer-${escHtml(p.name)}">
        <div class="fn-name">${icon("rss", 8)} ${escHtml(p.name)}</div>
        <div class="fn-detail">${pills.join(" ")}</div>
      </div>`,
            );
        });

        mailers.forEach((m: any) => {
            const entryCnt = (m.entries || []).length;
            const hasTls = (m.entries || []).some((e: any) => e.use_tls || e.use_starttls);
            const pills: string[] = [];
            pills.push(`<span class="fn-mode-pill fn-mode-http">${icon("mail", 8)} ${entryCnt}</span>`);
            if (m.timeout_mail) pills.push(`<span class="fn-mode-pill fn-mode-port">${escHtml(m.timeout_mail)}</span>`);
            if (hasTls) pills.push(`<span class="fn-mode-pill fn-mode-ssl">TLS</span>`);
            serviceNodes.push(
                `<div class="flow-node mailer svc-node" data-node-id="mailer-${escHtml(m.name)}">
        <div class="fn-name">${icon("mail", 8)} ${escHtml(m.name)}</div>
        <div class="fn-detail">${pills.join(" ")}</div>
      </div>`,
            );
        });

        httpErrors.forEach((he: any) => {
            const entryCnt = (he.entries || []).length;
            const codes = (he.entries || []).map((e: any) => String(e.status_code)).sort();
            const pills: string[] = [];
            pills.push(`<span class="fn-mode-pill fn-mode-redirect">${icon("alert-triangle", 8)} ${entryCnt}</span>`);
            if (codes.length) pills.push(`<span class="fn-mode-pill fn-mode-match">${codes.join(", ")}</span>`);
            serviceNodes.push(
                `<div class="flow-node http-err svc-node" data-node-id="he-${escHtml(he.name)}">
        <div class="fn-name">${icon("alert-triangle", 8)} ${escHtml(he.name)}</div>
        <div class="fn-detail">${pills.join(" ")}</div>
      </div>`,
            );
        });

        caches.forEach((c: any) => {
            const pills: string[] = [];
            if (c.total_max_size) pills.push(`<span class="fn-mode-pill fn-mode-http">${c.total_max_size} MB</span>`);
            if (c.max_age) pills.push(`<span class="fn-mode-pill fn-mode-port">${c.max_age}s</span>`);
            if (c.process_vary) pills.push(`<span class="fn-mode-pill fn-mode-fwd">vary</span>`);
            serviceNodes.push(
                `<div class="flow-node cache svc-node" data-node-id="cache-${escHtml(c.name)}">
        <div class="fn-name">${icon("activity", 8)} ${escHtml(c.name)}</div>
        <div class="fn-detail">${pills.length ? pills.join(" ") : '<span class="fn-mode-pill fn-mode-port">default</span>'}</div>
      </div>`,
            );
        });

        sslCerts.forEach((sc: any) => {
            const pills: string[] = [];
            pills.push(`<span class="fn-mode-pill fn-mode-ssl">${escHtml(sc.provider || "manual")}</span>`);
            pills.push(`<span class="fn-mode-pill fn-mode-${sc.status === "active" ? "http" : sc.status === "expired" ? "match" : "port"}">${escHtml(sc.status || "pending")}</span>`);
            if (sc.auto_renew) pills.push(`<span class="fn-mode-pill fn-mode-fwd">auto</span>`);
            serviceNodes.push(
                `<div class="flow-node ssl-cert svc-node" data-node-id="ssl-${escHtml(sc.domain)}" data-domain="${escHtml(sc.domain)}">
        <div class="fn-name">${icon("shield", 8)} ${escHtml(sc.domain)}</div>
        <div class="fn-detail">${pills.join(" ")}</div>
      </div>`,
            );
        });

        const sepDown = `<div class="flow-separator-v"></div>`;

        container.innerHTML = `
      <div class="flow-viewport" id="flow-viewport">
      <div class="flow-diagram flow-vertical" id="flow-diagram">
        <svg id="flow-svg" class="flow-arrows"></svg>
        <div class="flow-row">
          <div class="flow-row-label">Clients</div>
          <div class="flow-row-nodes">${clientCol}${listenCol}</div>
        </div>
        ${sepDown}
        <div class="flow-row">
          <div class="flow-row-label">Frontends (${fes.length})</div>
          <div class="flow-row-nodes">${feCol}</div>
        </div>
        ${sepDown}
        <div class="flow-row">
          <div class="flow-row-label">ACL Routing (${sortedAcls.length})</div>
          <div class="flow-row-nodes">${aclCol}</div>
        </div>
        ${authCol
                ? `${sepDown}<div class="flow-row">
          <div class="flow-row-label">Auth (${userlists.length})</div>
          <div class="flow-row-nodes">${authCol}</div>
        </div>`
                : ""
            }
        ${sepDown}
        <div class="flow-row">
          <div class="flow-row-label">Backends (${beOrder.length})</div>
          <div class="flow-row-nodes">${beCol}</div>
        </div>
        ${sepDown}
        <div class="flow-row">
          <div class="flow-row-label">Servers</div>
          <div class="flow-row-nodes">${srvCol}</div>
        </div>
        ${resolverCol
                ? `${sepDown}<div class="flow-row">
          <div class="flow-row-label">Resolvers (${activeResolvers.length})</div>
          <div class="flow-row-nodes">${resolverCol}</div>
        </div>`
                : ""
            }
        ${serviceNodes.length > 0
                ? `${sepDown}<div class="flow-row">
          <div class="flow-row-label">Services (${serviceNodes.length})</div>
          <div class="flow-row-nodes">${serviceNodes.join("")}</div>
        </div>`
                : ""
            }
      </div>
      </div>
    `;

        requestAnimationFrame(() =>
            requestAnimationFrame(() => {
                drawFlowConnections();
                _initHoverHighlight();
            }),
        );
    } catch (err) {
        console.warn("Flow canvas error:", err);
    }
}

/*  Drawing helpers   */

/** Calculates the edge coordinates of a node for a given side. */
function nodeEdge(node: Element, side: string, dr: DOMRect): FlowPoint {
    const r = node.getBoundingClientRect();
    if (side === "bottom") return { x: r.left - dr.left + r.width / 2, y: r.bottom - dr.top };
    if (side === "top") return { x: r.left - dr.left + r.width / 2, y: r.top - dr.top };
    if (side === "right") return { x: r.right - dr.left, y: r.top - dr.top + r.height / 2 };
    return { x: r.left - dr.left, y: r.top - dr.top + r.height / 2 };
}

/** Generates a vertical bezier curve SVG path between two points. */
function bezierV(
    from: FlowPoint,
    to: FlowPoint,
    color: string,
    opacity: number = 0.25,
    width: number = 1.5,
    fromId: string = "",
    toId: string = "",
): string {
    const dy = Math.abs(to.y - from.y) * 0.4;
    const dataAttr = fromId && toId ? ` data-from="${escHtml(fromId)}" data-to="${escHtml(toId)}"` : "";
    return `<path d="M${from.x},${from.y} C${from.x},${from.y + dy} ${to.x},${to.y - dy} ${to.x},${to.y}" fill="none" stroke="${color}" stroke-width="${width}" opacity="${opacity}"${dataAttr} />`;
}

/** Register a bidirectional edge in the connection graph. */
function _addEdge(a: string, b: string): void {
    if (!_graph[a]) _graph[a] = new Set();
    if (!_graph[b]) _graph[b] = new Set();
    _graph[a].add(b);
    _graph[b].add(a);
}

/** Draws SVG bezier connection lines between flow diagram nodes. */
export function drawFlowConnections(): void {
    const svg = document.getElementById("flow-svg");
    const diagram = document.getElementById("flow-diagram");
    if (!svg || !diagram) return;

    svg.setAttribute("width", String(diagram.scrollWidth));
    svg.setAttribute("height", String(diagram.scrollHeight));

    _graph = {};
    let paths = "";
    const dr = diagram.getBoundingClientRect();

    /* Client -> all Frontends */
    const clientNode = diagram.querySelector(".flow-node.client");
    if (clientNode) {
        diagram.querySelectorAll(".flow-node.fe").forEach((feNode) => {
            const feId = (feNode as HTMLElement).dataset.nodeId || "";
            _addEdge("client", feId);
            paths += bezierV(nodeEdge(clientNode, "bottom", dr), nodeEdge(feNode, "top", dr), "#60a5fa", 0.2, 1.5, "client", feId);
        });
        /* Client -> Listen blocks */
        diagram.querySelectorAll(".flow-node.listen-n").forEach((lnNode) => {
            const lnId = (lnNode as HTMLElement).dataset.nodeId || "";
            _addEdge("client", lnId);
            paths += bezierV(
                nodeEdge(clientNode, "bottom", dr),
                nodeEdge(lnNode, "top", dr),
                "#f472b6",
                0.2,
                1.5,
                "client",
                lnId,
            );
        });
    }

    /* Frontend -> ACL (if ACL has frontend_id) */
    diagram.querySelectorAll(".flow-node.acl").forEach((aclNode) => {
        const fid = (aclNode as HTMLElement).dataset.fid;
        const aclId = (aclNode as HTMLElement).dataset.nodeId || "";
        if (fid) {
            const feNode = diagram.querySelector(`.flow-node.fe[data-id="${fid}"]`);
            if (feNode) {
                const feId = (feNode as HTMLElement).dataset.nodeId || "";
                _addEdge(feId, aclId);
                paths += bezierV(nodeEdge(feNode, "bottom", dr), nodeEdge(aclNode, "top", dr), "#4ade80", 0.25, 1.5, feId, aclId);
            }
        }
    });

    /* Frontend -> Backend (default_backend, direct route without ACL) */
    diagram.querySelectorAll(".flow-node.fe").forEach((feNode) => {
        const defBe = (feNode as HTMLElement).dataset.defaultBackend;
        const feId = (feNode as HTMLElement).dataset.nodeId || "";
        if (defBe) {
            const beNode = diagram.querySelector(`.flow-node.be[data-name="${CSS.escape(defBe)}"]`);
            if (beNode) {
                const beId = (beNode as HTMLElement).dataset.nodeId || "";
                _addEdge(feId, beId);
                paths += bezierV(nodeEdge(feNode, "bottom", dr), nodeEdge(beNode, "top", dr), "#4ade80", 0.15, 1, feId, beId);
            }
        }
    });

    /* ACL -> Backend */
    diagram.querySelectorAll(".flow-node.acl").forEach((aclNode) => {
        const bName = (aclNode as HTMLElement).dataset.backend;
        const aclId = (aclNode as HTMLElement).dataset.nodeId || "";
        if (bName) {
            const beNode = diagram.querySelector(`.flow-node.be[data-name="${CSS.escape(bName)}"]`);
            if (beNode) {
                const beId = (beNode as HTMLElement).dataset.nodeId || "";
                _addEdge(aclId, beId);
                paths += bezierV(
                    nodeEdge(aclNode, "bottom", dr),
                    nodeEdge(beNode, "top", dr),
                    "#f87171",
                    0.25,
                    1.5,
                    aclId,
                    beId,
                );
            }
        }
    });

    /* Backend -> Auth userlist */
    diagram.querySelectorAll(".flow-node.be").forEach((beNode) => {
        const authName = (beNode as HTMLElement).dataset.auth;
        const beId = (beNode as HTMLElement).dataset.nodeId || "";
        if (authName) {
            const authNode = diagram.querySelector(`.flow-node.auth-ul[data-name="${CSS.escape(authName)}"]`);
            if (authNode) {
                const authId = (authNode as HTMLElement).dataset.nodeId || "";
                _addEdge(beId, authId);
                paths += bezierV(
                    nodeEdge(authNode, "bottom", dr),
                    nodeEdge(beNode, "top", dr),
                    "#f472b6",
                    0.3,
                    1.5,
                    authId,
                    beId,
                );
            }
        }
    });

    /* Backend -> Servers */
    diagram.querySelectorAll(".flow-node.srv").forEach((srvNode) => {
        const beName = (srvNode as HTMLElement).dataset.backend;
        const srvId = (srvNode as HTMLElement).dataset.nodeId || "";
        if (beName) {
            const beNode = diagram.querySelector(`.flow-node.be[data-name="${CSS.escape(beName)}"]`);
            if (beNode) {
                const beId = (beNode as HTMLElement).dataset.nodeId || "";
                _addEdge(beId, srvId);
                paths += bezierV(nodeEdge(beNode, "bottom", dr), nodeEdge(srvNode, "top", dr), "#fbbf24", 0.2, 1.5, beId, srvId);
            }
        }
    });

    /* Server -> Resolver */
    diagram.querySelectorAll(".flow-node.srv").forEach((srvNode) => {
        const resName = (srvNode as HTMLElement).dataset.resolver;
        const srvId = (srvNode as HTMLElement).dataset.nodeId || "";
        if (resName) {
            const resNode = diagram.querySelector(`.flow-node.resolver[data-name="${CSS.escape(resName)}"]`);
            if (resNode) {
                const resId = (resNode as HTMLElement).dataset.nodeId || "";
                _addEdge(srvId, resId);
                paths += bezierV(
                    nodeEdge(srvNode, "bottom", dr),
                    nodeEdge(resNode, "top", dr),
                    "#60a5fa",
                    0.25,
                    1.5,
                    srvId,
                    resId,
                );
            }
        }
    });

    /* Frontend -> SSL cert (bind lines containing ssl + crt path) */
    diagram.querySelectorAll(".flow-node.fe").forEach((feNode) => {
        const feId = (feNode as HTMLElement).dataset.nodeId || "";
        const feEl = feNode as HTMLElement;
        /* Check if frontend has SSL binds – if so, connect to all SSL cert nodes */
        const hasSsl = feEl.querySelector(".fn-badge-ssl");
        if (hasSsl) {
            diagram.querySelectorAll<HTMLElement>(".flow-node.ssl-cert").forEach((sslNode) => {
                const sslId = sslNode.dataset.nodeId || "";
                _addEdge(feId, sslId);
                paths += bezierV(nodeEdge(feNode, "bottom", dr), nodeEdge(sslNode, "top", dr), "#22d3ee", 0.15, 1, feId, sslId);
            });
        }
    });

    /* Backend -> HTTP error section (backends with errorfile field) */
    diagram.querySelectorAll(".flow-node.be").forEach((beNode) => {
        const beId = (beNode as HTMLElement).dataset.nodeId || "";
        const beName = (beNode as HTMLElement).dataset.name || "";
        if (beName) {
            diagram.querySelectorAll<HTMLElement>(".flow-node.http-err").forEach((heNode) => {
                const heId = heNode.dataset.nodeId || "";
                _addEdge(beId, heId);
                paths += bezierV(nodeEdge(beNode, "bottom", dr), nodeEdge(heNode, "top", dr), "#fb923c", 0.12, 1, beId, heId);
            });
        }
    });

    svg.innerHTML = paths;
}

/*  Hover Highlight   */

/** Initialize hover listeners on flow nodes for highlight / dim behavior. */
export function _initHoverHighlight(): void {
    const diagram = document.getElementById("flow-diagram");
    if (!diagram) return;

    /* Abort previous listeners so they never stack on re-render. */
    if (_hoverAC) _hoverAC.abort();
    _hoverAC = new AbortController();
    const opts = { capture: true, signal: _hoverAC.signal };

    diagram.addEventListener("mouseenter", _onNodeEnter, opts);
    diagram.addEventListener("mouseleave", _onNodeLeave, opts);
}

function _onNodeEnter(e: Event): void {
    const node = (e.target as HTMLElement).closest?.(".flow-node") as HTMLElement | null;
    if (!node) return;

    const diagram = document.getElementById("flow-diagram");
    if (!diagram) return;

    const nodeId = node.dataset.nodeId;
    if (!nodeId) return;

    /* Always clear previous highlight before applying new one  */
    _clearHighlight(diagram);

    /* Get all directly-connected node IDs */
    const connected = _graph[nodeId] || new Set<string>();
    const highlight = new Set<string>([nodeId, ...connected]);

    /* Add dimming class to diagram wrapper */
    diagram.classList.add("flow-hover-active");

    /* Mark highlighted / dimmed nodes */
    diagram.querySelectorAll<HTMLElement>(".flow-node[data-node-id]").forEach((n) => {
        const nid = n.dataset.nodeId || "";
        if (highlight.has(nid)) {
            n.classList.add("flow-highlight");
        } else {
            n.classList.add("flow-dimmed");
        }
    });

    /* Mark highlighted / dimmed paths */
    const svg = document.getElementById("flow-svg");
    if (svg) {
        svg.querySelectorAll<SVGPathElement>("path").forEach((path) => {
            const from = path.getAttribute("data-from") || "";
            const to = path.getAttribute("data-to") || "";
            if (from === nodeId || to === nodeId) {
                path.classList.add("flow-path-highlight");
            } else {
                path.classList.add("flow-path-dimmed");
            }
        });
    }
}

function _onNodeLeave(e: Event): void {
    const node = (e.target as HTMLElement).closest?.(".flow-node") as HTMLElement | null;
    if (!node) return;

    const diagram = document.getElementById("flow-diagram");
    if (!diagram) return;

    /* If we moved into another flow-node, skip clearing (mouseenter on the
       new node will redo the highlight immediately). */
    const related = (e as MouseEvent).relatedTarget as HTMLElement | null;
    if (related?.closest?.(".flow-node")) return;

    _clearHighlight(diagram);
}

function _clearHighlight(diagram: HTMLElement): void {
    diagram.classList.remove("flow-hover-active");
    diagram.querySelectorAll<HTMLElement>(".flow-highlight, .flow-dimmed").forEach((n) => {
        n.classList.remove("flow-highlight", "flow-dimmed");
    });
    const svg = document.getElementById("flow-svg");
    if (svg) {
        svg.querySelectorAll("path").forEach((p) => {
            p.classList.remove("flow-path-highlight", "flow-path-dimmed");
        });
    }
}

// Re-export switchSection for onclick handlers in overview cards
export { switchSection };
