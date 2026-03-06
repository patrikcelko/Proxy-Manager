/*
Overview / Dashboard Section

Displays stat cards with entity counts and renders a flow
topology diagram showing the traffic path from clients through
frontends, ACL rules, auth, backends to servers.
*/

/* Loads overview stats from the API and renders stat cards and the flow canvas */
async function loadOverview() {
    try {
        const d = await api('/api/overview');
        const items = [
            { key: 'global_settings', label: 'Global Settings', section: 'global', color: 'var(--accent)' },
            { key: 'default_settings', label: 'Default Settings', section: 'defaults', color: 'var(--info)' },
            { key: 'frontends', label: 'Frontends', section: 'frontends', color: 'var(--ok)' },
            { key: 'backends', label: 'Backends', section: 'backends', color: 'var(--warn)' },
            { key: 'backend_servers', label: 'Backend Servers', section: 'backends', color: '#a78bfa' },
            { key: 'acl_rules', label: 'ACL Rules', section: 'acl', color: 'var(--danger)' },
            { key: 'listen_blocks', label: 'Listen Blocks', section: 'listen', color: '#f472b6' },
            { key: 'userlists', label: 'User Lists', section: 'userlists', color: '#34d399' },
            { key: 'resolvers', label: 'Resolvers', section: 'resolvers', color: '#60a5fa' },
            { key: 'peers', label: 'Peers', section: 'peers', color: '#c084fc' },
            { key: 'mailers', label: 'Mailers', section: 'mailers', color: '#fbbf24' },
            { key: 'http_errors', label: 'HTTP Errors', section: 'http-errors', color: '#fb923c' },
            { key: 'caches', label: 'Caches', section: 'caches', color: '#2dd4bf' },
            { key: 'ssl_certificates', label: 'SSL Certificates', section: 'ssl-certificates', color: '#22d3ee' },
        ];
        document.getElementById('overview-grid').innerHTML = items.map(i => `
            <div class="stat-card" onclick="switchSection('${i.section}')">
                <div class="stat-number" style="color:${i.color}">${d[i.key] || 0}</div>
                <div class="stat-label">${i.label}</div>
            </div>
        `).join('');

        document.getElementById('overview-charts').innerHTML = '';

        // Flow Canvas - topology diagram
        renderFlowCanvas();
    } catch (err) { toast(err.message, 'error'); }
}

/* Renders the full traffic flow topology diagram with sorted nodes to minimize crossing lines */
async function renderFlowCanvas() {
    try {
        const [feRes, beRes, aclRes, listenRes, ulRes] = await Promise.all([
            api('/api/frontends').catch(() => []),
            api('/api/backends').catch(() => []),
            api('/api/acl-rules').catch(() => []),
            api('/api/listen-blocks').catch(() => []),
            api('/api/userlists').catch(() => []),
        ]);
        const fes = feRes.items || feRes || [];
        const bes = beRes.items || beRes || [];
        const acls = aclRes.items || aclRes || [];
        const listens = listenRes.items || listenRes || [];
        const userlists = ulRes.items || ulRes || [];

        const container = document.getElementById('overview-flow');

        /* Build a frontend index for ordering */
        const feIndex = {};
        fes.forEach((f, i) => { feIndex[String(f.id)] = i; });

        /* Sort ACLs by frontend position so grouped ACLs sit under their frontend */
        const sortedAcls = [...acls].sort((a, b) => {
            const fa = feIndex[String(a.frontend_id)] ?? 9999;
            const fb = feIndex[String(b.frontend_id)] ?? 9999;
            if (fa !== fb) return fa - fb;
            return (a.domain || '').localeCompare(b.domain || '');
        });

        /* Order backends so they appear under the ACLs that reference them */
        const beOrder = [];
        const beAdded = new Set();
        /* First place backends in the order they appear via ACLs */
        sortedAcls.forEach(a => {
            const n = a.backend_name;
            if (n && !beAdded.has(n)) {
                const be = bes.find(b => b.name === n);
                if (be) { beOrder.push(be); beAdded.add(n); }
            }
        });
        /* Then add any backends referenced by default_backend */
        fes.forEach(f => {
            const n = f.default_backend;
            if (n && !beAdded.has(n)) {
                const be = bes.find(b => b.name === n);
                if (be) { beOrder.push(be); beAdded.add(n); }
            }
        });
        /* Finally add remaining backends */
        bes.forEach(b => { if (!beAdded.has(b.name)) { beOrder.push(b); beAdded.add(b.name); } });

        /* Build backend position index for server ordering */
        const beIdx = {};
        beOrder.forEach((b, i) => { beIdx[b.name] = i; });

        /* ── Build node HTML ── */
        const clientCol = `<div class="flow-node client" data-fid="client">
            <div class="fn-name">Incoming Traffic</div>
            <div class="fn-detail">HTTP / HTTPS / TCP</div>
        </div>`;

        const feCol = fes.length ? fes.map(f => {
            const hasSSL = (f.binds || []).some(b => /ssl\b/.test(b.bind_line || ''));
            const hasAuth = (f.options || []).some(o => /http-request\s+auth/.test(o.directive || ''));
            const authBadge = hasAuth ? '<span style="color:#f472b6;font-size:.6rem;font-weight:700;margin-left:.3rem" title="Auth required">🔒</span>' : '';
            const sslBadge = hasSSL ? '<span style="color:#4ade80;font-size:.6rem;font-weight:700;margin-left:.3rem" title="SSL/TLS">🔐</span>' : '';
            return `<div class="flow-node fe" data-id="${f.id}" data-default-backend="${escHtml(f.default_backend || '')}">
            <div class="fn-name">${escHtml(f.name)}${sslBadge}${authBadge}</div>
            <div class="fn-detail">${escHtml(f.mode || 'http')} &bull; ${(f.binds || []).length} bind(s)</div>
        </div>`;
        }).join('') : '<div class="flow-empty-col">No frontends</div>';

        const aclCol = sortedAcls.length ? sortedAcls.map(a => `<div class="flow-node acl" data-backend="${escHtml(a.backend_name || '')}" data-fid="${a.frontend_id || ''}">
            <div class="fn-name">${escHtml(a.domain)}</div>
            <div class="fn-detail">${a.is_redirect ? 'redirect ' + (a.redirect_code || 301) : '-> ' + escHtml(a.backend_name || '')}</div>
        </div>`).join('')
            : '<div class="flow-empty-col">No ACL rules</div>';

        /* Auth row - userlists (placed between ACLs and Backends as auth gate) */
        const authCol = userlists.length ? userlists.map(u => `<div class="flow-node auth-ul" data-name="${escHtml(u.name)}" style="border-left-color:#f472b6">
            <div class="fn-name">🔒 ${escHtml(u.name)}</div>
            <div class="fn-detail">${(u.entries || []).length} user(s)</div>
        </div>`).join('') : '';

        /* Backends sorted to align with ACL references */
        const beCol = beOrder.length ? beOrder.map(b => {
            const authBadge = b.auth_userlist ? '<span style="color:#f472b6;font-size:.6rem;font-weight:700;margin-left:.3rem" title="Auth: ' + escHtml(b.auth_userlist) + '">🔒</span>' : '';
            const hcBadge = b.health_check_enabled ? '<span style="color:#4ade80;font-size:.6rem;font-weight:700;margin-left:.3rem" title="Health check">♥</span>' : '';
            return `<div class="flow-node be" data-name="${escHtml(b.name)}" data-auth="${escHtml(b.auth_userlist || '')}">
            <div class="fn-name">${escHtml(b.name)}${authBadge}${hcBadge}</div>
            <div class="fn-detail">${escHtml(b.balance || 'roundrobin')} &bull; ${(b.servers || []).length} srv(s)</div>
        </div>`;
        }).join('') : '<div class="flow-empty-col">No backends</div>';

        /* Servers sorted by backend order */
        const srvCol = beOrder.length ? beOrder.flatMap(b => (b.servers || []).map(s => `<div class="flow-node srv" data-backend="${escHtml(b.name)}">
            <div class="fn-name">${escHtml(s.name)}</div>
            <div class="fn-detail">${escHtml(s.address)}:${s.port}</div>
        </div>`)).join('') || '<div class="flow-empty-col">No servers</div>'
            : '<div class="flow-empty-col">No servers</div>';

        const sepDown = `<div class="flow-separator-v">
            ${icon('arrow-down-flow', 24, 1.5)}
        </div>`;

        container.innerHTML = `
            <div class="flow-viewport" id="flow-viewport">
            <div class="flow-diagram flow-vertical" id="flow-diagram">
                <svg id="flow-svg" class="flow-arrows"></svg>
                <div class="flow-row">
                    <div class="flow-row-label">Clients</div>
                    <div class="flow-row-nodes">${clientCol}
                        ${listens.length ? listens.map(l => `<div class="flow-node listen-n">
                            <div class="fn-name">${escHtml(l.name)}</div>
                            <div class="fn-detail">${(l.binds || []).map(b => b.bind_line).join(', ') || 'no bind'} &bull; ${escHtml(l.mode || 'tcp')}</div>
                        </div>`).join('') : ''}
                    </div>
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
                ${authCol ? `${sepDown}<div class="flow-row">
                    <div class="flow-row-label">Auth (${userlists.length})</div>
                    <div class="flow-row-nodes">${authCol}</div>
                </div>` : ''}
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
            </div>
            </div>
        `;

        container._zoomLevel = 1;
        requestAnimationFrame(() => requestAnimationFrame(() => drawFlowConnections()));
    } catch (err) { console.warn('Flow canvas error:', err); }
}

/* Draws SVG bezier connection lines between flow diagram nodes */
function drawFlowConnections() {
    const svg = document.getElementById('flow-svg');
    const diagram = document.getElementById('flow-diagram');
    if (!svg || !diagram) return;

    svg.setAttribute('width', diagram.scrollWidth);
    svg.setAttribute('height', diagram.scrollHeight);

    let paths = '';
    const dr = diagram.getBoundingClientRect();

    /* Calculates the edge coordinates of a node for a given side */
    function nodeEdge(node, side) {
        const r = node.getBoundingClientRect();
        if (side === 'bottom') return { x: r.left - dr.left + r.width / 2, y: r.bottom - dr.top };
        if (side === 'top') return { x: r.left - dr.left + r.width / 2, y: r.top - dr.top };
        if (side === 'right') return { x: r.right - dr.left, y: r.top - dr.top + r.height / 2 };
        return { x: r.left - dr.left, y: r.top - dr.top + r.height / 2 };
    }

    /* Generates a vertical bezier curve SVG path between two points */
    function bezierV(from, to, color, opacity = 0.25, width = 1.5) {
        const dy = Math.abs(to.y - from.y) * 0.4;
        return `<path d="M${from.x},${from.y} C${from.x},${from.y + dy} ${to.x},${to.y - dy} ${to.x},${to.y}" fill="none" stroke="${color}" stroke-width="${width}" opacity="${opacity}" />`;
    }

    /* Client -> all Frontends */
    const clientNode = diagram.querySelector('.flow-node.client');
    if (clientNode) {
        diagram.querySelectorAll('.flow-node.fe').forEach(feNode => {
            paths += bezierV(nodeEdge(clientNode, 'bottom'), nodeEdge(feNode, 'top'), '#60a5fa', 0.2);
        });
    }

    /* Frontend -> ACL (if ACL has frontend_id) */
    diagram.querySelectorAll('.flow-node.acl').forEach(aclNode => {
        const fid = aclNode.dataset.fid;
        if (fid) {
            const feNode = diagram.querySelector(`.flow-node.fe[data-id="${fid}"]`);
            if (feNode) {
                paths += bezierV(nodeEdge(feNode, 'bottom'), nodeEdge(aclNode, 'top'), '#4ade80', 0.25);
            }
        }
    });

    /* Frontend -> Backend (default_backend, direct route without ACL) */
    diagram.querySelectorAll('.flow-node.fe').forEach(feNode => {
        const defBe = feNode.dataset.defaultBackend;
        if (defBe) {
            const beNode = diagram.querySelector(`.flow-node.be[data-name="${CSS.escape(defBe)}"]`);
            if (beNode) {
                paths += bezierV(nodeEdge(feNode, 'bottom'), nodeEdge(beNode, 'top'), '#4ade80', 0.15, 1);
            }
        }
    });

    /* ACL -> Backend */
    diagram.querySelectorAll('.flow-node.acl').forEach(aclNode => {
        const bName = aclNode.dataset.backend;
        if (bName) {
            const beNode = diagram.querySelector(`.flow-node.be[data-name="${CSS.escape(bName)}"]`);
            if (beNode) {
                paths += bezierV(nodeEdge(aclNode, 'bottom'), nodeEdge(beNode, 'top'), '#f87171', 0.25);
            }
        }
    });

    /* Backend -> Auth userlist */
    diagram.querySelectorAll('.flow-node.be').forEach(beNode => {
        const authName = beNode.dataset.auth;
        if (authName) {
            const authNode = diagram.querySelector(`.flow-node.auth-ul[data-name="${CSS.escape(authName)}"]`);
            if (authNode) {
                paths += bezierV(nodeEdge(authNode, 'bottom'), nodeEdge(beNode, 'top'), '#f472b6', 0.3, 1.5);
            }
        }
    });

    /* Backend -> Servers */
    diagram.querySelectorAll('.flow-node.srv').forEach(srvNode => {
        const beName = srvNode.dataset.backend;
        if (beName) {
            const beNode = diagram.querySelector(`.flow-node.be[data-name="${CSS.escape(beName)}"]`);
            if (beNode) {
                paths += bezierV(nodeEdge(beNode, 'bottom'), nodeEdge(srvNode, 'top'), '#fbbf24', 0.2);
            }
        }
    });

    svg.innerHTML = paths;
}
