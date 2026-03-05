/*
Listen Blocks Section
=====================

Manages HAProxy listen blocks - combined frontend+backend
definitions for stats dashboards, TCP proxying, database
load balancing, and direct services.
*/


/* Global list of all listen blocks, populated by loadListenBlocks() */
let allListenBlocks = [];

/* Current filter query for listen blocks search */
let listenFilter = '';

/* Fetches all listen blocks from the API and renders the card grid */
async function loadListenBlocks() {
    try {
        const d = await api('/api/listen-blocks');
        allListenBlocks = d.items || d;
        renderListenBlocks(allListenBlocks);
    } catch (err) { toast(err.message, 'error'); }
}

/* Filters listen blocks by search query across name, mode, binds, balance, and comment */
function filterListenBlocks() {
    listenFilter = (document.getElementById('listen-search').value || '').toLowerCase();
    renderListenBlocks(allListenBlocks.filter(l => {
        const hay = [l.name, l.mode, ...(l.binds || []).map(b => b.bind_line), l.balance, l.comment].filter(Boolean).join(' ').toLowerCase();
        return hay.includes(listenFilter);
    }));
}

/* Renders listen block cards with feature badges, bind addresses, detail grids, and directives */
function renderListenBlocks(list) {
    const grid = document.getElementById('listen-grid');
    const empty = document.getElementById('listen-empty');
    if (!list.length) { grid.innerHTML = ''; grid.style.display = 'none'; empty.style.display = 'block'; return; }
    grid.style.display = 'grid'; grid.style.gridTemplateColumns = 'repeat(auto-fill,minmax(420px,1fr))'; empty.style.display = 'none';

    const IC = {
        mode: icon('globe-simple', 11, 2.5),
        balance: icon('smile', 11, 2.5),
        bind: icon('link', 11, 2.5),
        timeout: icon('clock', 11, 2.5),
        maxconn: icon('users', 11, 2.5),
        server: icon('server', 11, 2.5),
        log: icon('file', 11, 2.5),
        fwd: icon('arrow-right', 11, 2.5),
        stats: icon('bar-chart', 11, 2.5),
    };

    grid.innerHTML = list.map(l => {
        const mode = l.mode || 'http';
        const contentLines = (l.content || '').split('\n').filter(Boolean);
        const hasStats = contentLines.some(line => line.trim().toLowerCase().startsWith('stats '));
        const binds = l.binds || [];

        const features = [];
        features.push(`<span class="ln-feat ln-feat-mode">${IC.mode} ${escHtml(mode.toUpperCase())}</span>`);
        if (l.balance) features.push(`<span class="ln-feat ln-feat-balance">${IC.balance} ${escHtml(l.balance)}</span>`);
        if (hasStats) features.push(`<span class="ln-feat ln-feat-stats">${IC.stats} STATS</span>`);
        if (l.option_httplog) features.push(`<span class="ln-feat ln-feat-log">${IC.log} HTTP LOG</span>`);
        if (l.option_tcplog) features.push(`<span class="ln-feat ln-feat-log">${IC.log} TCP LOG</span>`);
        if (l.option_forwardfor) features.push(`<span class="ln-feat ln-feat-fwd">${IC.fwd} X-FWD-FOR</span>`);

        const bindsHtml = `<div class="ln-bind-section">
            <div class="ln-bind-head"><span>${IC.bind} Bind Addresses <span class="ln-bind-count">${binds.length}</span></span>
                <button class="btn-icon" onclick='openListenBindModal(${l.id})'>${SVG.plus}</button></div>
            <div class="ln-bind-grid">${binds.length ? binds.map(b => {
            const hasSSL = /\bssl\b/i.test(b.bind_line);
            const ports = (b.bind_line.match(/:(\d+)/g) || []).map(m => m.replace(':', ''));
            return `<div class="ln-bind-card">
                    <div class="ln-bind-indicator${hasSSL ? ' ln-bind-ssl' : ''}"></div>
                    <div class="ln-bind-body">
                        <div class="ln-bind-addr">${escHtml(b.bind_line)}</div>
                    </div>
                    <div class="ln-bind-badges">
                        ${ports.map(p => '<span class="badge badge-muted">:' + escHtml(p) + '</span>').join('')}
                        ${hasSSL ? '<span class="badge badge-info">ssl</span>' : ''}
                    </div>
                    <div class="ln-bind-actions">
                        <button class="btn-icon" onclick='openListenBindModal(${l.id}, ${escJsonAttr(b)})'>${SVG.editSm}</button>
                        <button class="btn-icon danger" onclick="deleteListenBind(${l.id},${b.id})">${SVG.delSm}</button>
                    </div>
                </div>`;
        }).join('') : '<div class="ln-bind-empty">${IC.bind} No binds configured</div>'}</div>
        </div>`;

        const detailRows = [];
        if (l.maxconn != null) detailRows.push(['maxconn', 'Max Connections', String(l.maxconn)]);
        if (l.timeout_client) detailRows.push(['timeout', 'Client Timeout', l.timeout_client]);
        if (l.timeout_server) detailRows.push(['timeout', 'Server Timeout', l.timeout_server]);
        if (l.timeout_connect) detailRows.push(['timeout', 'Connect Timeout', l.timeout_connect]);
        if (l.default_server_params) detailRows.push(['server', 'Default Server', l.default_server_params]);

        const detailHtml = detailRows.length ? `<div class="ln-detail-section">
            <div class="ln-detail-grid">${detailRows.map(([icon, label, val]) =>
            `<div class="ln-detail-item">
                    <span class="ln-detail-icon">${IC[icon] || ''}</span>
                    <span class="ln-detail-label">${escHtml(label)}</span>
                    <span class="ln-detail-value">${escHtml(val)}</span>
                </div>`
        ).join('')}</div>
        </div>` : '';

        const contentHtml = contentLines.length ? `<div class="ln-content-section">
            <div class="ln-content-head"><span>${IC.server} Directives <span class="ln-dir-count">${contentLines.length}</span></span></div>
            <div class="ln-content-lines">${contentLines.map(line =>
            `<div class="ln-content-line">${escHtml(line)}</div>`
        ).join('')}</div>
        </div>` : '';

        const commentHtml = l.comment ? `<div class="ln-custom-opts"><span class="ln-custom-label">Comment</span>${escHtml(l.comment)}</div>` : '';

        return `<div class="item-card ln-card">
            <div class="item-header"><h3>${escHtml(l.name)}</h3>
                <div><button class="btn-icon" onclick='openListenModal(${escJsonAttr(l)})'>${SVG.edit}</button>
                <button class="btn-icon danger" onclick="deleteListenBlock(${l.id})">${SVG.del}</button></div>
            </div>
            <div class="ln-features">${features.join('')}</div>
            ${bindsHtml}
            ${detailHtml}
            ${contentHtml}
            ${commentHtml}
        </div>`;
    }).join('');
}

/* Preset listen block templates for common use cases (stats, MySQL, Redis, PostgreSQL, SMTP, Prometheus) */
const LISTEN_PRESETS = [
    { name: 'HAProxy Stats Dashboard', mode: 'http', content: 'stats enable\nstats uri /stats\nstats refresh 10s\nstats admin if LOCALHOST', comment: 'Statistics reporting dashboard' },
    { name: 'MySQL Proxy', mode: 'tcp', balance: 'roundrobin', timeout_client: '30s', timeout_server: '30s', timeout_connect: '5s', content: 'option mysql-check user haproxy', comment: 'MySQL load balancer' },
    { name: 'Redis Sentinel', mode: 'tcp', balance: 'roundrobin', timeout_client: '30s', timeout_server: '30s', content: 'option tcp-check\ntcp-check send PING\\r\\n\ntcp-check expect string +PONG', comment: 'Redis with TCP health check' },
    { name: 'PostgreSQL', mode: 'tcp', balance: 'roundrobin', timeout_client: '30s', timeout_server: '30s', timeout_connect: '5s', content: 'option pgsql-check user haproxy', comment: 'PostgreSQL load balancer' },
    { name: 'SMTP Relay', mode: 'tcp', balance: 'roundrobin', content: 'option smtpchk HELO localhost', comment: 'SMTP mail relay' },
    { name: 'Prometheus Exporter', mode: 'http', content: 'http-request use-service prometheus-exporter if { path /metrics }', comment: 'Prometheus metrics endpoint' },
];

/* Opens the listen block create/edit modal with presets, timeouts, options, and custom directives */
function openListenModal(existing = null) {
    const l = existing || {};

    const SEC = {
        core: icon('settings', 15),
        timeout: icon('clock', 15),
        opts: icon('terminal', 15),
        advanced: icon('edit-pen', 15),
    };

    const presets = !l.id ? `<label>Preset</label><select onchange="if(this.value)applyListenPreset(this.value)">
        <option value="">Custom</option>${LISTEN_PRESETS.map((p, i) => `<option value="${i}">${escHtml(p.name)}</option>`).join('')}</select>
        <div class="form-help">Quick-start templates for common listen block configurations</div>` : '';

    openModal(`
        <h3>${l.id ? 'Edit' : 'New'} Listen Block</h3>
        <p class="modal-subtitle">Combined frontend+backend block for stats dashboards, TCP proxying, and direct services.</p>
        ${presets}

        <div class="form-row"><div><label>Name</label><input id="m-name" value="${escHtml(l.name || '')}" placeholder="my-listen-block">
            <div class="form-help">Unique identifier for this listen block</div></div>
        <div><label>Mode</label><select id="m-mode"><option value="http" ${l.mode === 'http' || !l.mode ? 'selected' : ''}>HTTP</option>
            <option value="tcp" ${l.mode === 'tcp' ? 'selected' : ''}>TCP</option></select>
            <div class="form-help">Protocol mode (Layer 7 HTTP or Layer 4 TCP)</div></div></div>
        <div class="form-row"><div><label>Balance Algorithm</label><select id="m-balance"><option value="">None</option>
            ${['roundrobin', 'leastconn', 'source', 'uri', 'first', 'hdr', 'random'].map(v => `<option ${l.balance === v ? 'selected' : ''}>${v}</option>`).join('')}</select>
            <div class="form-help">Load balancing strategy (optional for stats)</div></div>
        <div><label>Max Connections</label><input type="number" id="m-maxconn" value="${l.maxconn != null ? l.maxconn : ''}" placeholder="1000" min="0">
            <div class="form-help">Maximum concurrent connections</div></div></div>
        <div><label>Comment</label><input id="m-comment" value="${escHtml(l.comment || '')}" placeholder="Optional description..." style="width:100%">
            <div class="form-help">Internal note for documentation</div></div>

        <hr class="form-divider">
        <div class="form-section-title">${SEC.timeout} Timeouts</div>
        <div class="form-row-3">
            <div><label>Client Timeout</label><input id="m-timeout-client" value="${escHtml(l.timeout_client || '')}" placeholder="30s">
                <div class="form-help">Max inactivity on client side</div></div>
            <div><label>Server Timeout</label><input id="m-timeout-server" value="${escHtml(l.timeout_server || '')}" placeholder="30s">
                <div class="form-help">Max inactivity on server side</div></div>
            <div><label>Connect Timeout</label><input id="m-timeout-connect" value="${escHtml(l.timeout_connect || '')}" placeholder="5s">
                <div class="form-help">Max time to connect to server</div></div>
        </div>

        <div class="form-collapsible" style="margin-top:1rem">
            <div class="form-collapsible-head" onclick="toggleCollapsible(this)">${SEC.opts} Options &amp; Behavior ${SVG.chevron}</div>
            <div class="form-collapsible-body">
                <div class="form-row"><div>
                    <label class="toggle-wrap" style="margin-top:.5rem">
                        <input type="checkbox" id="m-forwardfor" ${l.option_forwardfor ? 'checked' : ''}>
                        X-Forwarded-For
                    </label>
                    <div class="form-help">Pass client IP to backend via header</div>
                </div><div>
                    <label class="toggle-wrap" style="margin-top:.5rem">
                        <input type="checkbox" id="m-httplog" ${l.option_httplog ? 'checked' : ''}>
                        HTTP Log
                    </label>
                    <div class="form-help">Enable detailed HTTP request logging</div>
                </div></div>
                <div class="form-row"><div>
                    <label class="toggle-wrap" style="margin-top:.5rem">
                        <input type="checkbox" id="m-tcplog" ${l.option_tcplog ? 'checked' : ''}>
                        TCP Log
                    </label>
                    <div class="form-help">Enable TCP connection logging</div>
                </div><div></div></div>
                <label>Default Server Params</label><input id="m-def-srv" value="${escHtml(l.default_server_params || '')}" placeholder="inter 3s fall 3 rise 2 maxconn 256">
                <div class="form-help">Shared parameters for all servers (default-server directive)</div>
            </div>
        </div>

        <div class="form-collapsible" style="margin-top:.5rem">
            <div class="form-collapsible-head" onclick="toggleCollapsible(this)">${SEC.advanced} Custom Directives ${SVG.chevron}</div>
            <div class="form-collapsible-body">
                <label>Additional Directives</label><textarea id="m-content" rows="5" placeholder="stats enable&#10;stats uri /stats&#10;stats refresh 10s&#10;server web1 192.168.1.10:80 check">${escHtml(l.content || '')}</textarea>
                <div class="form-help">Additional HAProxy directives, one per line (servers, stats, health checks, etc.)</div>
            </div>
        </div>

        <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="saveListenBlock(${l.id || 'null'})">Save</button></div>
    `, { wide: true });
}

/* Fills the listen block modal fields from a selected preset template */
function applyListenPreset(idx) {
    const p = LISTEN_PRESETS[idx];
    if (!p) return;
    document.getElementById('m-name').value = p.name;
    document.getElementById('m-mode').value = p.mode;
    document.getElementById('m-balance').value = p.balance || '';
    document.getElementById('m-maxconn').value = p.maxconn != null ? p.maxconn : '';
    document.getElementById('m-timeout-client').value = p.timeout_client || '';
    document.getElementById('m-timeout-server').value = p.timeout_server || '';
    document.getElementById('m-timeout-connect').value = p.timeout_connect || '';
    document.getElementById('m-def-srv').value = p.default_server_params || '';
    document.getElementById('m-forwardfor').checked = !!p.option_forwardfor;
    document.getElementById('m-httplog').checked = !!p.option_httplog;
    document.getElementById('m-tcplog').checked = !!p.option_tcplog;
    document.getElementById('m-content').value = p.content || '';
    document.getElementById('m-comment').value = p.comment || '';
}

/* Saves a new or updated listen block with all configuration fields */
async function saveListenBlock(id) {
    const body = {
        name: document.getElementById('m-name').value,
        mode: document.getElementById('m-mode').value,
        balance: document.getElementById('m-balance').value || null,
        maxconn: parseInt(document.getElementById('m-maxconn').value) || null,
        timeout_client: document.getElementById('m-timeout-client').value || null,
        timeout_server: document.getElementById('m-timeout-server').value || null,
        timeout_connect: document.getElementById('m-timeout-connect').value || null,
        default_server_params: document.getElementById('m-def-srv').value || null,
        option_forwardfor: document.getElementById('m-forwardfor').checked,
        option_httplog: document.getElementById('m-httplog').checked,
        option_tcplog: document.getElementById('m-tcplog').checked,
        content: document.getElementById('m-content').value || null,
        comment: document.getElementById('m-comment').value || null
    };
    try {
        if (id) await api(`/api/listen-blocks/${id}`, { method: 'PUT', body: JSON.stringify(body) });
        else await api('/api/listen-blocks', { method: 'POST', body: JSON.stringify(body) });
        closeModal(); toast(id ? 'Updated' : 'Created'); loadListenBlocks();
    } catch (err) { toast(err.message, 'error'); }
}

/* Opens the listen block bind create/edit modal with BIND_PRESETS templates */
function openListenBindModal(listenBlockId, existing = null) {
    const b = existing || {};
    const cats = [...new Set(BIND_PRESETS.map(p => p.cat))];

    const BMI = {
        templates: icon('grid', 15),
        bind: icon('link', 15),
        opts: icon('settings', 15),
    };

    const presetsHtml = !b.id ? `
        <div class="form-section-title">${BMI.templates} Templates <span class="stab-count">${BIND_PRESETS.length}</span></div>
        <div class="stabs" style="margin-bottom:.5rem">
            <button class="stab active" onclick="filterLnBindPresets('all')">All</button>
            ${cats.map(c => `<button class="stab" onclick="filterLnBindPresets('${c}')">${c}</button>`).join('')}
        </div>
        <div class="preset-search-wrap">
            ${icon('search')}
            <input id="ln-bind-preset-filter" placeholder="Search templates..." oninput="filterLnBindPresetSearch()">
        </div>
        <div class="dir-grid" id="lnBindPresetGrid">
            ${BIND_PRESETS.map(p => `
                <div class="dir-card" data-bcat="${escHtml(p.cat)}" data-search-text="${escHtml((p.line + ' ' + p.h).toLowerCase())}"
                     onclick="document.getElementById('m-ln-bind-line').value='${escHtml(p.line).replace(/'/g, "\\'")}'">
                    <div class="dir-card-name">${escHtml(p.line)}</div>
                    <div class="dir-card-desc">${escHtml(p.h)}</div>
                </div>`).join('')}
        </div>
        <hr class="form-divider">` : '';

    openModal(`
        <h3>${b.id ? 'Edit' : 'Add'} Bind Address</h3>
        <p class="modal-subtitle">Configure a bind address for this listen block.</p>
        ${presetsHtml}
        <div class="form-section-title">${BMI.bind} Bind Configuration</div>
        <label>Bind Line</label>
        <input id="m-ln-bind-line" value="${escHtml(b.bind_line || '')}" placeholder="*:8404 or 0.0.0.0:3306 ssl crt /path">
        <div class="form-help">Full HAProxy bind directive value (address, port, SSL options, etc.)</div>

        <hr class="form-divider">
        <div class="form-collapsible-head" onclick="toggleCollapsible(this)">
            ${BMI.opts} Options ${SVG.chevron}
        </div>
        <div class="form-collapsible-body">
            <label>Sort Order</label>
            <input type="number" id="m-ln-sort" value="${b.sort_order || 0}" min="0">
            <div class="form-help">Order of this bind in the configuration output</div>
        </div>

        <div class="modal-actions">
            <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="saveListenBind(${listenBlockId},${b.id || 'null'})">Save</button>
        </div>
    `, { wide: !b.id });
}

/* Filters listen bind preset cards by category tab */
function filterLnBindPresets(cat) {
    filterPresetGrid('lnBindPresetGrid', 'ln-bind-preset-filter', 'bcat', cat);
}

/* Filters listen bind preset cards by search text */
function filterLnBindPresetSearch() {
    searchPresetGrid('lnBindPresetGrid', 'ln-bind-preset-filter', 'bcat');
}

/* Saves a new or updated listen block bind address */
async function saveListenBind(listenBlockId, bindId) {
    const body = {
        bind_line: document.getElementById('m-ln-bind-line').value,
        sort_order: parseInt(document.getElementById('m-ln-sort').value) || 0
    };
    try {
        if (bindId) await api(`/api/listen-blocks/${listenBlockId}/binds/${bindId}`, { method: 'PUT', body: JSON.stringify(body) });
        else await api(`/api/listen-blocks/${listenBlockId}/binds`, { method: 'POST', body: JSON.stringify(body) });
        closeModal(); toast('Saved'); loadListenBlocks();
    } catch (err) { toast(err.message, 'error'); }
}

/* Deletes a bind address from a listen block after confirmation */
async function deleteListenBind(listenBlockId, bindId) {
    await crudDelete(`/api/listen-blocks/${listenBlockId}/binds/${bindId}`, 'Delete this bind?', loadListenBlocks);
}

/* Deletes a listen block after confirmation */
async function deleteListenBlock(id) {
    await crudDelete(`/api/listen-blocks/${id}`, 'Delete this listen block?', loadListenBlocks);
}
