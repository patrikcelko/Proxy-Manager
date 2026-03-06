/*
Resolvers Section
=================

Manages HAProxy DNS resolver sections for dynamic server
name resolution and service discovery with nameserver entries.
*/

/* Global list of all resolvers, populated by loadResolvers() */
let allResolvers = [];

/* Renders resolver cards with nameserver entries, feature badges, and detail grids */
function renderResolversGrid(items) {
    {
        const grid = document.getElementById('resolvers-grid');
        const empty = document.getElementById('resolvers-empty');
        if (!items.length) { grid.innerHTML = ''; grid.style.display = 'none'; empty.style.display = 'block'; return; }
        grid.style.display = 'grid'; grid.style.gridTemplateColumns = 'repeat(auto-fill,minmax(380px,1fr))'; empty.style.display = 'none';
        /* Icon set for resolver cards */
        const RIC = {
            dns: icon('globe', 12),
            ns: icon('server', 12),
            clock: icon('clock', 12),
            hold: icon('shield', 12),
            payload: icon('package', 12),
            resolv: icon('file', 12),
            dot: icon('chevron-right', 10),
        };

        grid.innerHTML = items.map(r => {
            const ns = (r.nameservers || []).sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));

            /* Feature badges */
            const feats = [];
            feats.push(`<span class="rs-feat rs-feat-dns">${RIC.dns} DNS Resolver</span>`);
            feats.push(`<span class="rs-feat rs-feat-count">${RIC.ns} ${ns.length} nameserver${ns.length !== 1 ? 's' : ''}</span>`);
            if (r.timeout_resolve || r.timeout_retry) {
                const t = r.timeout_resolve ? `resolve: ${r.timeout_resolve}` : '';
                const t2 = r.timeout_retry ? `retry: ${r.timeout_retry}` : '';
                feats.push(`<span class="rs-feat rs-feat-timeout">${RIC.clock} ${[t, t2].filter(Boolean).join(', ')}</span>`);
            }
            const holdCount = ['hold_valid', 'hold_other', 'hold_refused', 'hold_timeout', 'hold_obsolete', 'hold_nx', 'hold_aa'].filter(h => r[h]).length;
            if (holdCount) feats.push(`<span class="rs-feat rs-feat-hold">${RIC.hold} ${holdCount} hold timer${holdCount > 1 ? 's' : ''}</span>`);
            if (r.accepted_payload_size) feats.push(`<span class="rs-feat rs-feat-payload">${RIC.payload} payload: ${r.accepted_payload_size}</span>`);
            if (r.parse_resolv_conf) feats.push(`<span class="rs-feat rs-feat-resolv">${RIC.resolv} resolv.conf</span>`);

            /* Detail grid */
            const details = [];
            if (r.resolve_retries != null) details.push({ l: 'Retries', v: r.resolve_retries });
            if (r.timeout_resolve) details.push({ l: 'Timeout Resolve', v: r.timeout_resolve });
            if (r.timeout_retry) details.push({ l: 'Timeout Retry', v: r.timeout_retry });
            if (r.accepted_payload_size) details.push({ l: 'Payload Size', v: `${r.accepted_payload_size} bytes` });
            ['valid', 'other', 'refused', 'timeout', 'obsolete', 'nx', 'aa'].forEach(h => {
                if (r[`hold_${h}`]) details.push({ l: `Hold ${h}`, v: r[`hold_${h}`] });
            });
            if (r.parse_resolv_conf) details.push({ l: 'resolv.conf', v: 'Enabled' });

            const detailHtml = details.length ? `<div class="rs-detail-section"><div class="rs-detail-grid">${details.map(d =>
                `<div class="rs-detail-item"><div class="rs-detail-icon">${RIC.dot}</div><span class="rs-detail-label">${d.l}</span><span class="rs-detail-value">${escHtml(String(d.v))}</span></div>`
            ).join('')}</div></div>` : '';

            /* Nameserver entries */
            const nsHtml = ns.length ? ns.map(n =>
                `<div class="rs-entry-card">
                    <div class="rs-entry-dot"></div>
                    <div class="rs-entry-body">
                        <div class="rs-entry-name">${escHtml(n.name)}</div>
                        <div class="rs-entry-addr">${escHtml(n.address)}<span class="rs-entry-port">:${n.port}</span></div>
                    </div>
                    <div class="rs-entry-actions">
                        <button class="btn-icon" onclick='openNameserverModal(${r.id},${escJsonAttr(n)})'>${SVG.editSm}</button>
                        <button class="btn-icon danger" onclick="deleteNameserver(${r.id},${n.id})">${SVG.delSm}</button>
                    </div>
                </div>`
            ).join('') : `<div class="rs-entry-empty">${RIC.ns} No nameservers configured</div>`;

            const extraHtml = r.extra_options ? `<div class="rs-custom-opts"><span class="rs-custom-label">Extra:</span>${escHtml(r.extra_options).replace(/\n/g, '; ')}</div>` : '';

            return `<div class="item-card rs-card">
                <div class="item-header"><h3>${escHtml(r.name)}</h3>
                    <div><button class="btn-icon" onclick='openResolverModal(${escJsonAttr(r)})'>${SVG.edit}</button>
                    <button class="btn-icon danger" onclick="deleteResolver(${r.id})">${SVG.del}</button></div>
                </div>
                ${r.comment ? `<p class="item-comment" style="padding:0 .65rem .25rem;margin:0;font-size:.78rem;color:var(--text-muted)">${escHtml(r.comment)}</p>` : ''}
                <div class="rs-features">${feats.join('')}</div>
                ${detailHtml}
                <div class="rs-entries-section">
                    <div class="rs-entries-head"><span>${RIC.ns} Nameservers <span class="rs-entry-count">${ns.length}</span></span>
                        <button class="btn-icon" onclick="openNameserverModal(${r.id})">${SVG.plus}</button></div>
                    <div class="rs-entries-grid">${nsHtml}</div>
                </div>
                ${extraHtml}
            </div>`;
        }).join('');
    }
}

/* Fetches all resolvers from the API and renders cards */
async function loadResolvers() {
    try {
        const d = await api('/api/resolvers');
        allResolvers = d.items || d;
        renderResolversGrid(allResolvers);
    } catch (err) { toast(err.message, 'error'); }
}

/* Filters resolvers by name, comment, or nameserver name/address */
function filterResolvers() {
    const q = (document.getElementById('resolver-search').value || '').toLowerCase();
    if (!q) { renderResolversGrid(allResolvers); return; }
    renderResolversGrid(allResolvers.filter(r =>
        r.name.toLowerCase().includes(q) ||
        (r.comment || '').toLowerCase().includes(q) ||
        (r.nameservers || []).some(n => (n.name || '').toLowerCase().includes(q) || (n.address || '').toLowerCase().includes(q))
    ));
}

/* Opens the resolver create/edit modal with identification, resolution settings, hold timers, and advanced options */
function openResolverModal(existing = null) {
    const r = existing || {};
    const SEC = {
        core: icon('globe', 15),
        timeout: icon('clock', 15),
        hold: icon('shield', 15),
        opts: icon('terminal', 15),
        advanced: icon('edit-pen', 15),
    };

    openModal(`
        <h3>${r.id ? 'Edit' : 'New'} DNS Resolver</h3>
        <p class="modal-subtitle">Configure a DNS resolver section for dynamic server name resolution and service discovery.</p>

        <div class="form-section-title">${SEC.core} Identification</div>
        <div class="form-row"><div>
            <label>Resolver Name</label><input id="m-name" value="${escHtml(r.name || '')}" placeholder="mydns">
            <div class="form-help">Unique name referenced by backend server resolvers directive</div>
        </div><div>
            <label>Comment</label><input id="m-comment" value="${escHtml(r.comment || '')}" placeholder="Optional description...">
            <div class="form-help">Internal note for documentation purposes</div>
        </div></div>

        <hr class="form-divider">
        <div class="form-section-title">${SEC.timeout} Resolution Settings</div>
        <div class="form-row-3"><div>
            <label>Resolve Retries</label><input type="number" id="m-resolve-retries" value="${r.resolve_retries != null ? r.resolve_retries : ''}" placeholder="3" min="0">
            <div class="form-help">Number of DNS query retries before giving up</div>
        </div><div>
            <label>Timeout Resolve</label><input id="m-timeout-resolve" value="${escHtml(r.timeout_resolve || '')}" placeholder="1s">
            <div class="form-help">Time to wait for DNS answer</div>
        </div><div>
            <label>Timeout Retry</label><input id="m-timeout-retry" value="${escHtml(r.timeout_retry || '')}" placeholder="1s">
            <div class="form-help">Delay between retries on failure</div>
        </div></div>

        <div class="form-row"><div>
            <label>Accepted Payload Size</label><input type="number" id="m-payload" value="${r.accepted_payload_size != null ? r.accepted_payload_size : ''}" placeholder="8192" min="512" max="65535">
            <div class="form-help">Max DNS response size in bytes (512-65535)</div>
        </div><div>
            <label class="toggle-wrap" style="margin-top:1.5rem">
                <input type="checkbox" id="m-parse-resolv-conf" ${r.parse_resolv_conf ? 'checked' : ''}>
                Parse /etc/resolv.conf
            </label>
            <div class="form-help">Auto-import nameservers from system resolv.conf</div>
        </div></div>

        <div class="form-collapsible" style="margin-top:1rem">
            <div class="form-collapsible-head" onclick="toggleCollapsible(this)">${SEC.hold} Hold Timers ${SVG.chevron}</div>
            <div class="form-collapsible-body">
                <p class="form-help" style="margin-bottom:.75rem">Duration to hold DNS resolution results in cache before re-querying. Use time suffixes (s, m, h).</p>
                <div class="form-row-3"><div>
                    <label>Hold Valid</label><input id="m-hold-valid" value="${escHtml(r.hold_valid || '')}" placeholder="10s">
                    <div class="form-help">Valid responses (NOERROR)</div>
                </div><div>
                    <label>Hold Obsolete</label><input id="m-hold-obsolete" value="${escHtml(r.hold_obsolete || '')}" placeholder="10s">
                    <div class="form-help">Expired results still usable</div>
                </div><div>
                    <label>Hold NX</label><input id="m-hold-nx" value="${escHtml(r.hold_nx || '')}" placeholder="30s">
                    <div class="form-help">NXDOMAIN results</div>
                </div></div>
                <div class="form-row-3"><div>
                    <label>Hold Timeout</label><input id="m-hold-timeout" value="${escHtml(r.hold_timeout || '')}" placeholder="30s">
                    <div class="form-help">Timeout (no answer)</div>
                </div><div>
                    <label>Hold Refused</label><input id="m-hold-refused" value="${escHtml(r.hold_refused || '')}" placeholder="30s">
                    <div class="form-help">REFUSED responses</div>
                </div><div>
                    <label>Hold Other</label><input id="m-hold-other" value="${escHtml(r.hold_other || '')}" placeholder="30s">
                    <div class="form-help">Other error types</div>
                </div></div>
                <div class="form-row"><div>
                    <label>Hold AA</label><input id="m-hold-aa" value="${escHtml(r.hold_aa || '')}" placeholder="10s">
                    <div class="form-help">Authoritative answer results</div>
                </div><div></div></div>
            </div>
        </div>

        <div class="form-collapsible" style="margin-top:.5rem">
            <div class="form-collapsible-head" onclick="toggleCollapsible(this)">${SEC.advanced} Advanced Options ${SVG.chevron}</div>
            <div class="form-collapsible-body">
                <label>Extra Options</label>
                <textarea id="m-extra" rows="4" placeholder="One directive per line">${escHtml(r.extra_options || '')}</textarea>
                <div class="form-help">Additional HAProxy directives for this resolver section (one per line)</div>
            </div>
        </div>

        <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="saveResolver(${r.id || 'null'})">${r.id ? 'Update' : 'Create'} DNS Resolver</button></div>
    `, { wide: true });
}

/* Opens the nameserver create/edit modal with identity and connection fields */
function openNameserverModal(resolverId, existing = null) {
    const n = existing || {};
    const SEC = {
        server: icon('server', 15),
        network: icon('arrow-right', 15),
    };
    openModal(`
        <h3>${n.id ? 'Edit' : 'New'} Nameserver</h3>
        <p class="modal-subtitle">Define a DNS nameserver for this resolver to query for name resolution.</p>

        <div class="form-section-title">${SEC.server} Nameserver Identity</div>
        <div class="form-row"><div>
            <label>Nameserver Name</label><input id="m-name" value="${escHtml(n.name || '')}" placeholder="dns1">
            <div class="form-help">Unique identifier for this nameserver (e.g. google-dns, cloudflare)</div>
        </div><div>
            <label>Sort Order</label><input type="number" id="m-sort" value="${n.sort_order || 0}" min="0">
            <div class="form-help">Display/config order (lower = first)</div>
        </div></div>

        <hr class="form-divider">
        <div class="form-section-title">${SEC.network} Connection</div>
        <div class="form-row"><div>
            <label>IP Address / Hostname</label><input id="m-address" value="${escHtml(n.address || '')}" placeholder="8.8.8.8 or 2001:4860:4860::8888">
            <div class="form-help">IPv4 or IPv6 address of the DNS server</div>
        </div><div>
            <label>Port</label><input type="number" id="m-port" value="${n.port || 53}" min="1" max="65535">
            <div class="form-help">DNS port (default: 53, DoT: 853)</div>
        </div></div>

        <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="saveNameserver(${resolverId},${n.id || 'null'})">${n.id ? 'Update' : 'Add'} Nameserver</button></div>
    `, { wide: true });
}

/* Saves a new or updated resolver with all configuration fields including hold timers */
async function saveResolver(id) {
    const prc = document.getElementById('m-parse-resolv-conf');
    const body = {
        name: document.getElementById('m-name').value,
        resolve_retries: parseInt(document.getElementById('m-resolve-retries').value) || null,
        timeout_resolve: document.getElementById('m-timeout-resolve').value || null,
        timeout_retry: document.getElementById('m-timeout-retry').value || null,
        hold_valid: document.getElementById('m-hold-valid').value || null,
        hold_other: document.getElementById('m-hold-other').value || null,
        hold_refused: document.getElementById('m-hold-refused').value || null,
        hold_timeout: document.getElementById('m-hold-timeout').value || null,
        hold_obsolete: document.getElementById('m-hold-obsolete').value || null,
        hold_nx: document.getElementById('m-hold-nx').value || null,
        hold_aa: document.getElementById('m-hold-aa').value || null,
        accepted_payload_size: parseInt(document.getElementById('m-payload').value) || null,
        parse_resolv_conf: prc && prc.checked ? 1 : null,
        comment: document.getElementById('m-comment').value || null,
        extra_options: document.getElementById('m-extra').value || null,
    };
    try {
        if (id) await api(`/api/resolvers/${id}`, { method: 'PUT', body: JSON.stringify(body) });
        else await api('/api/resolvers', { method: 'POST', body: JSON.stringify(body) });
        closeModal(); toast(id ? 'Updated' : 'Created'); loadResolvers();
    } catch (err) { toast(err.message, 'error'); }
}

/* Deletes a resolver section after confirmation */
async function deleteResolver(id) {
    await crudDelete(`/api/resolvers/${id}`, 'Delete this resolver?', loadResolvers);
}

/* Saves a new or updated nameserver entry within a resolver */
async function saveNameserver(resolverId, nsId) {
    const body = {
        name: document.getElementById('m-name').value,
        address: document.getElementById('m-address').value,
        port: parseInt(document.getElementById('m-port').value) || 53,
        sort_order: parseInt(document.getElementById('m-sort').value) || 0,
    };
    try {
        if (nsId) await api(`/api/resolvers/${resolverId}/nameservers/${nsId}`, { method: 'PUT', body: JSON.stringify(body) });
        else await api(`/api/resolvers/${resolverId}/nameservers`, { method: 'POST', body: JSON.stringify(body) });
        closeModal(); toast('Saved'); loadResolvers();
    } catch (err) { toast(err.message, 'error'); }
}

/* Deletes a nameserver entry from a resolver after confirmation */
async function deleteNameserver(resolverId, nsId) {
    await crudDelete(`/api/resolvers/${resolverId}/nameservers/${nsId}`, 'Delete this nameserver?', loadResolvers);
}
