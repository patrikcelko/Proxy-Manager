/*
SSL Certificates Section
========================

Manages SSL/TLS certificate records with Let's Encrypt (Certbot)
integration, ACL domain picking, alt domains (SANs), auto-renewal
tracking, and certbot command generation.
*/

/* Global list of all SSL certificates, populated by loadSslCertificates() */
let allSslCertificates = [];

/* Inline SVG icons for SSL certificate card badges and detail items */
const SC_IC = {
    lock: icon('lock', 11, 2.5),
    shield: icon('shield', 11, 2.5),
    globe: icon('globe', 11, 2.5),
    refresh: icon('refresh', 11, 2.5),
    calendar: icon('calendar', 11, 2.5),
    mail: icon('mail', 11, 2.5),
    file: icon('file', 11, 2.5),
    alert: icon('alert-triangle', 11, 2.5),
    star: icon('star', 11, 2.5),
    dns: icon('server', 11, 2.5),
};

/* Formats an ISO date string into a readable short date */
function _formatDate(iso) {
    if (!iso) return '\u2014';
    try { return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }); }
    catch { return iso; }
}

/* Calculates number of days until a certificate expires from an ISO date */
function _daysUntilExpiry(iso) {
    if (!iso) return null;
    try {
        const diff = new Date(iso) - new Date();
        return Math.ceil(diff / (1000 * 60 * 60 * 24));
    } catch { return null; }
}

/* Fetches all SSL certificates from the API and renders the card grid */
async function loadSslCertificates() {
    try {
        const d = await api('/api/ssl-certificates');
        allSslCertificates = d.items || d;
        renderSslCertificates(allSslCertificates);
    } catch (err) { toast(err.message, 'error'); }
}

/* Filters SSL certificates by domain, email, provider, status, challenge, and comment */
function filterSslCertificates() {
    const q = (document.getElementById('ssl-search').value || '').toLowerCase();
    renderSslCertificates(allSslCertificates.filter(c => {
        const hay = [c.domain, c.alt_domains, c.email, c.provider, c.status, c.challenge_type, c.comment, c.dns_plugin].filter(Boolean).join(' ').toLowerCase();
        return hay.includes(q);
    }));
}

/* Renders SSL certificate cards with status strips, feature badges, detail grids, SAN domains, paths, and errors */
function renderSslCertificates(list) {
    const grid = document.getElementById('ssl-certificates-grid');
    const empty = document.getElementById('ssl-certificates-empty');
    if (!list.length) { grid.innerHTML = ''; grid.style.display = 'none'; empty.style.display = 'block'; return; }
    grid.style.display = 'grid'; grid.style.gridTemplateColumns = 'repeat(auto-fill,minmax(420px,1fr))'; empty.style.display = 'none';

    grid.innerHTML = list.map(c => {
        const altDomains = c.alt_domains ? c.alt_domains.split(',').map(d => d.trim()).filter(d => d) : [];
        const isWild = c.domain && c.domain.startsWith('*.');
        const daysLeft = _daysUntilExpiry(c.expires_at);
        const expiryWarn = daysLeft !== null && daysLeft <= 30 && c.status === 'active';

        /* Feature badges */
        const feats = [];
        feats.push(`<span class="sc-feat sc-feat-${c.status}">${SC_IC.shield} ${c.status}</span>`);
        feats.push(`<span class="sc-feat sc-feat-provider">${SC_IC.lock} ${c.provider}</span>`);
        feats.push(`<span class="sc-feat sc-feat-challenge">${c.challenge_type === 'dns-01' ? SC_IC.dns : SC_IC.globe} ${c.challenge_type}</span>`);
        if (isWild) feats.push(`<span class="sc-feat sc-feat-wildcard">${SC_IC.star} wildcard</span>`);
        if (c.auto_renew) feats.push(`<span class="sc-feat sc-feat-autorenew">${SC_IC.refresh} auto-renew</span>`);
        else feats.push(`<span class="sc-feat sc-feat-norenew">${SC_IC.refresh} no renew</span>`);
        if (c.dns_plugin) feats.push(`<span class="sc-feat sc-feat-dns">${SC_IC.dns} ${escHtml(c.dns_plugin)}</span>`);
        if (expiryWarn) feats.push(`<span class="sc-feat sc-feat-expired">${SC_IC.alert} ${daysLeft}d left</span>`);

        /* Detail items */
        const details = [];
        details.push(`<div class="sc-detail-item"><span class="sc-detail-icon">${SC_IC.mail}</span><span class="sc-detail-label">Email</span><span class="sc-detail-value${!c.email ? ' muted' : ''}">${c.email ? escHtml(c.email) : 'not set'}</span></div>`);
        details.push(`<div class="sc-detail-item"><span class="sc-detail-icon">${SC_IC.calendar}</span><span class="sc-detail-label">Issued</span><span class="sc-detail-value${!c.issued_at ? ' muted' : ''}">${_formatDate(c.issued_at)}</span></div>`);
        details.push(`<div class="sc-detail-item"><span class="sc-detail-icon">${SC_IC.calendar}</span><span class="sc-detail-label">Expires</span><span class="sc-detail-value" style="${c.status === 'expired' || expiryWarn ? 'color:var(--danger)' : ''}">${_formatDate(c.expires_at)}${daysLeft !== null ? ` (${daysLeft}d)` : ''}</span></div>`);
        if (c.last_renewal_at) details.push(`<div class="sc-detail-item"><span class="sc-detail-icon">${SC_IC.refresh}</span><span class="sc-detail-label">Renewed</span><span class="sc-detail-value">${_formatDate(c.last_renewal_at)}</span></div>`);

        /* Paths section */
        let pathsHtml = '';
        if (c.cert_path || c.key_path || c.fullchain_path) {
            pathsHtml = `<div class="sc-paths-section">
                <div class="sc-paths-label">${SC_IC.file} Certificate Paths</div>
                ${c.cert_path ? `<div class="sc-path-item">cert: ${escHtml(c.cert_path)}</div>` : ''}
                ${c.key_path ? `<div class="sc-path-item">key: ${escHtml(c.key_path)}</div>` : ''}
                ${c.fullchain_path ? `<div class="sc-path-item">fullchain: ${escHtml(c.fullchain_path)}</div>` : ''}
            </div>`;
        }

        /* Alt domains section */
        let domainsHtml = '';
        if (altDomains.length) {
            domainsHtml = `<div class="sc-domains-section">
                <div class="sc-domains-head">${SC_IC.globe} SAN Domains <span class="sc-domain-count">${altDomains.length}</span></div>
                <div class="sc-domain-chips">${altDomains.map(d => `<span class="sc-domain-chip">${SC_IC.globe} ${escHtml(d)}</span>`).join('')}</div>
            </div>`;
        }

        /* Error section */
        let errorHtml = '';
        if (c.last_error) {
            errorHtml = `<div class="sc-error-section">
                <div class="sc-error-label">${SC_IC.alert} Last Error</div>
                <div class="sc-error-text">${escHtml(c.last_error)}</div>
            </div>`;
        }

        /* Comment section */
        let commentHtml = '';
        if (c.comment) {
            commentHtml = `<div class="sc-comment"><span class="sc-comment-label">Note:</span>${escHtml(c.comment)}</div>`;
        }

        return `<div class="item-card sc-card">
            <div class="sc-status-strip ${c.status}"></div>
            <div class="item-header">
                <h3>${SVG.lock} ${escHtml(c.domain)}</h3>
                <div>
                    <button class="btn-icon" title="Certbot Commands" onclick="showCertbotCommand(${c.id})">${SVG.code}</button>
                    <button class="btn-icon" onclick='openSslCertificateModal(${escJsonAttr(c)})'>${SVG.edit}</button>
                    <button class="btn-icon danger" onclick="deleteSslCertificate(${c.id})">${SVG.del}</button>
                </div>
            </div>
            <div class="sc-features">${feats.join('')}</div>
            <div class="sc-detail-section"><div class="sc-detail-grid">${details.join('')}</div></div>
            ${domainsHtml}
            ${pathsHtml}
            ${errorHtml}
            ${commentHtml}
        </div>`;
    }).join('');
}

/* Opens the SSL certificate create/edit modal with 3-step form: domain, provider/challenge, paths/dates */
async function openSslCertificateModal(existing = null) {
    const c = existing || {};
    const isNew = !c.id;

    /* Fetch ACL domains for picker */
    let aclDomains = [];
    try { aclDomains = await api('/api/ssl-certificates/acl-domains'); } catch { }

    const altDomainsArr = c.alt_domains ? c.alt_domains.split(',').map(d => d.trim()).filter(d => d) : [];
    const prov = c.provider || 'certbot';
    const isCertbot = prov === 'certbot';

    openModal(`
        <h3>${SVG.lock} ${c.id ? 'Edit' : 'New'} SSL Certificate</h3>

        <div class="form-section-title">${SC_IC.globe} Step 1 - Domain</div>
        <div class="form-divider"></div>

        <div class="sc-domain-picker">
            ${aclDomains.length ? `<div class="sc-domain-picker-tabs" id="sc-domain-tabs">
                <button class="sc-domain-picker-tab${!isNew ? ' active' : ''}" onclick="switchDomainTab('custom')">Custom Domain</button>
                <button class="sc-domain-picker-tab${isNew ? ' active' : ''}" onclick="switchDomainTab('acl')">From ACL Rules <span style="opacity:.7;font-weight:400">(${aclDomains.length})</span></button>
            </div>` : '<label>Primary Domain *</label>'}
            <div id="sc-domain-custom" style="display:${!isNew || !aclDomains.length ? 'block' : 'none'}">
                ${!aclDomains.length ? '' : '<label style="margin-top:.35rem">Primary Domain *</label>'}
                <input id="m-domain" value="${escHtml(c.domain || '')}" placeholder="example.com, *.example.com">
            </div>
            ${aclDomains.length ? `<div id="sc-domain-acl" style="display:${isNew ? 'block' : 'none'}">
                <input class="sc-acl-domain-search" placeholder="Search ${aclDomains.length} ACL domains..." oninput="filterAclDomains(this.value)">
                <div class="sc-acl-domain-grid" id="sc-acl-grid">
                    ${aclDomains.map(d => `<div class="sc-acl-domain-item${c.domain === d ? ' selected' : ''}" onclick="selectAclDomain(this, '${escHtml(d)}')">${SC_IC.globe} ${escHtml(d)}</div>`).join('')}
                </div>
            </div>` : ''}
        </div>

        <div class="form-collapsible-head${altDomainsArr.length ? ' open' : ''}" onclick="toggleCollapsible(this)">
            ${SC_IC.globe} Alternative Domains (SANs)
            ${icon('chevron-down', 14, 2, 'chevron')}
        </div>
        <div class="form-collapsible-body${altDomainsArr.length ? ' open' : ''}">
            <div style="display:flex;gap:8px;align-items:center">
                <input id="m-alt-domain-input" placeholder="Add domain and press Enter" style="flex:1" onkeydown="if(event.key==='Enter'){event.preventDefault();addAltDomain()}">
                <button class="btn btn-secondary" type="button" onclick="addAltDomain()" style="white-space:nowrap;padding:.35rem .65rem">+ Add</button>
                ${aclDomains.length ? `<button class="btn btn-secondary" type="button" onclick="showAltDomainAclPicker()" style="white-space:nowrap;padding:.35rem .65rem;font-size:.7rem" title="Pick from ACL Domains">${SC_IC.globe} ACL</button>` : ''}
            </div>
            <div class="sc-alt-domains-list" id="sc-alt-domains-list">
                ${altDomainsArr.map(d => `<span class="sc-alt-domain-tag">${escHtml(d)}<span class="remove-tag" onclick="removeAltDomain(this)">&times;</span></span>`).join('')}
            </div>
        </div>

        <div class="form-section-title" style="margin-top:.75rem">${SC_IC.shield} Step 2 - Provider &amp; Challenge</div>
        <div class="form-divider"></div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0 16px">
            <div><label>Provider *</label>
            <select id="m-provider" onchange="onProviderChange()">
                <option value="certbot" ${prov === 'certbot' ? 'selected' : ''}>Certbot (Let\u2019s Encrypt)</option>
                <option value="manual" ${prov === 'manual' ? 'selected' : ''}>Manual Upload</option>
                <option value="self-signed" ${prov === 'self-signed' ? 'selected' : ''}>Self-Signed</option>
            </select></div>
            <div><label>Status</label>
            <select id="m-status">
                <option value="pending" ${(c.status || 'pending') === 'pending' ? 'selected' : ''}>Pending</option>
                <option value="active" ${c.status === 'active' ? 'selected' : ''}>Active</option>
                <option value="expired" ${c.status === 'expired' ? 'selected' : ''}>Expired</option>
                <option value="revoked" ${c.status === 'revoked' ? 'selected' : ''}>Revoked</option>
                <option value="error" ${c.status === 'error' ? 'selected' : ''}>Error</option>
            </select></div>
        </div>

        <div id="sc-certbot-options" style="display:${isCertbot ? 'block' : 'none'}">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:0 16px">
                <div><label>Challenge Type</label>
                <select id="m-challenge-type" onchange="toggleDnsPlugin()">
                    <option value="http-01" ${(c.challenge_type || 'http-01') === 'http-01' ? 'selected' : ''}>HTTP-01 (Webroot)</option>
                    <option value="dns-01" ${c.challenge_type === 'dns-01' ? 'selected' : ''}>DNS-01 (DNS Plugin)</option>
                    <option value="standalone" ${c.challenge_type === 'standalone' ? 'selected' : ''}>Standalone</option>
                </select></div>
                <div><label>Email (Let\u2019s Encrypt registration)</label>
                <input id="m-email" value="${escHtml(c.email || '')}" placeholder="admin@example.com"></div>
            </div>
            <div id="dns-plugin-wrap" style="display:${c.challenge_type === 'dns-01' ? 'block' : 'none'}">
                <label>DNS Plugin</label>
                <input id="m-dns-plugin" value="${escHtml(c.dns_plugin || '')}" placeholder="cloudflare, route53, digitalocean, google...">
                <div style="font-size:.68rem;color:var(--text-dim);margin-top:.15rem">Plugin used by certbot for DNS-01 challenge validation</div>
            </div>
            <div style="padding:.5rem .65rem;margin-top:.35rem;background:var(--bg-input);border-radius:6px;border:1px solid var(--border);font-size:.72rem;color:var(--text-dim)">
                ${SC_IC.shield} After saving, use the <strong>Certbot Commands</strong> button ${SVG.code} on the certificate card to get the exact commands for obtaining, renewing, and revoking this certificate.
            </div>
        </div>

        <div id="sc-manual-options" style="display:${!isCertbot ? 'block' : 'none'}">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:0 16px">
                <div><label>Challenge Type</label>
                <select id="m-challenge-type-manual" disabled>
                    <option value="http-01" selected>N/A (Manual)</option>
                </select></div>
                <div><label>Email</label>
                <input id="m-email-manual" value="${escHtml(c.email || '')}" placeholder="(optional)"></div>
            </div>
        </div>

        <div class="form-collapsible-head${c.cert_path || c.key_path || c.fullchain_path || c.issued_at || c.expires_at || !isCertbot ? ' open' : ''}" onclick="toggleCollapsible(this)" style="margin-top:.75rem">
            ${SC_IC.file} Step 3 - Certificate Paths &amp; Dates
            ${icon('chevron-down', 14, 2, 'chevron')}
        </div>
        <div class="form-collapsible-body${c.cert_path || c.key_path || c.fullchain_path || c.issued_at || c.expires_at || !isCertbot ? ' open' : ''}">
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0 16px">
                <div><label>Certificate Path</label><input id="m-cert-path" value="${escHtml(c.cert_path || '')}" placeholder="/etc/letsencrypt/live/domain/cert.pem"></div>
                <div><label>Private Key Path</label><input id="m-key-path" value="${escHtml(c.key_path || '')}" placeholder="/etc/letsencrypt/live/domain/privkey.pem"></div>
                <div><label>Fullchain Path</label><input id="m-fullchain-path" value="${escHtml(c.fullchain_path || '')}" placeholder="/etc/letsencrypt/live/domain/fullchain.pem"></div>
            </div>
            ${isCertbot && isNew ? `<button class="btn btn-secondary" type="button" onclick="autofillCertPaths()" style="margin-top:.35rem;font-size:.7rem;padding:.2rem .5rem">${SC_IC.file} Auto-fill from domain</button>` : ''}
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:0 16px;margin-top:.35rem">
                <div><label>Issued At</label><input type="date" id="m-issued-at" value="${c.issued_at ? c.issued_at.split('T')[0] : ''}"></div>
                <div><label>Expires At</label><input type="date" id="m-expires-at" value="${c.expires_at ? c.expires_at.split('T')[0] : ''}"></div>
            </div>
        </div>

        <div class="form-section-title" style="margin-top:.75rem">${SC_IC.refresh} Options</div>
        <div class="form-divider"></div>

        <label class="toggle-wrap" style="margin:.5rem 0">
            <input type="checkbox" id="m-auto-renew" ${c.auto_renew !== false ? 'checked' : ''}> Auto-Renew
            <span style="font-size:.7rem;color:var(--text-dim);margin-left:.5rem">(background check marks expired certs automatically)</span>
        </label>
        <label>Comment / Notes</label>
        <input id="m-comment" value="${escHtml(c.comment || '')}" placeholder="Optional notes about this certificate">

        <div class="modal-actions">
            <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="saveSslCertificate(${c.id || 'null'})">${c.id ? 'Update' : 'Create'} Certificate</button>
        </div>
    `, { wide: true });

    /* Initialize provider-dependent section visibility */
    onProviderChange();
}

/* Switches between custom domain input and ACL domain picker tabs */
function switchDomainTab(tab) {
    document.querySelectorAll('.sc-domain-picker-tab').forEach(t => t.classList.remove('active'));
    const customDiv = document.getElementById('sc-domain-custom');
    const aclDiv = document.getElementById('sc-domain-acl');
    if (tab === 'acl' && aclDiv) {
        event.target.classList.add('active');
        customDiv.style.display = 'none';
        aclDiv.style.display = 'block';
    } else {
        document.querySelector('.sc-domain-picker-tab').classList.add('active');
        customDiv.style.display = 'block';
        if (aclDiv) aclDiv.style.display = 'none';
    }
}

/* Selects an ACL domain and sets it as the primary domain input value */
function selectAclDomain(el, domain) {
    document.querySelectorAll('.sc-acl-domain-item').forEach(i => i.classList.remove('selected'));
    el.classList.add('selected');
    document.getElementById('m-domain').value = domain;
    /* Switch to custom tab to show selected value */
    switchDomainTab('custom');
}

/* Filters ACL domain items in the picker grid by search query */
function filterAclDomains(q) {
    q = q.toLowerCase();
    document.querySelectorAll('.sc-acl-domain-item').forEach(el => {
        el.style.display = el.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
}

/* Adds an alternative domain (SAN) tag from the input field */
function addAltDomain() {
    const inp = document.getElementById('m-alt-domain-input');
    const val = inp.value.trim();
    if (!val) return;
    const list = document.getElementById('sc-alt-domains-list');
    /* Don't add duplicates */
    const existing = [...list.querySelectorAll('.sc-alt-domain-tag')].map(t => t.textContent.replace('\u00d7', '').trim());
    if (existing.includes(val)) { inp.value = ''; return; }
    list.insertAdjacentHTML('beforeend', `<span class="sc-alt-domain-tag">${escHtml(val)}<span class="remove-tag" onclick="removeAltDomain(this)">&times;</span></span>`);
    inp.value = '';
}

/* Removes an alternative domain tag from the list */
function removeAltDomain(el) { el.parentElement.remove(); }

/* Toggles a mini ACL domain picker for selecting alternative domains */
function showAltDomainAclPicker() {
    /* Toggle a mini picker for alt domains from ACL */
    const existing = document.getElementById('sc-alt-acl-picker');
    if (existing) { existing.remove(); return; }
    const list = document.getElementById('sc-alt-domains-list');
    api('/api/ssl-certificates/acl-domains').then(domains => {
        if (!domains.length) { toast('No ACL domains found'); return; }
        const picker = document.createElement('div');
        picker.id = 'sc-alt-acl-picker';
        picker.className = 'sc-acl-domain-grid';
        picker.style.marginTop = '.35rem';
        picker.innerHTML = domains.map(d => `<div class="sc-acl-domain-item" onclick="pickAltAclDomain(this, '${escHtml(d)}')">${SC_IC.globe} ${escHtml(d)}</div>`).join('');
        list.parentElement.appendChild(picker);
    }).catch(() => toast('Failed to load ACL domains', 'error'));
}

/* Picks an ACL domain and adds it as an alternative domain tag */
function pickAltAclDomain(el, domain) {
    const list = document.getElementById('sc-alt-domains-list');
    const existing = [...list.querySelectorAll('.sc-alt-domain-tag')].map(t => t.textContent.replace('\u00d7', '').trim());
    if (!existing.includes(domain)) {
        list.insertAdjacentHTML('beforeend', `<span class="sc-alt-domain-tag">${escHtml(domain)}<span class="remove-tag" onclick="removeAltDomain(this)">&times;</span></span>`);
    }
    el.classList.add('selected');
}

/* Toggles visibility of certbot vs manual provider options based on selected provider */
function onProviderChange() {
    const prov = document.getElementById('m-provider').value;
    const certbotOpts = document.getElementById('sc-certbot-options');
    const manualOpts = document.getElementById('sc-manual-options');
    if (certbotOpts) certbotOpts.style.display = prov === 'certbot' ? 'block' : 'none';
    if (manualOpts) manualOpts.style.display = prov !== 'certbot' ? 'block' : 'none';
}

/* Auto-fills certificate file paths based on the entered domain name */
function autofillCertPaths() {
    const domain = (document.getElementById('m-domain').value || '').trim();
    if (!domain) { toast('Enter a domain first', 'error'); return; }
    const clean = domain.replace(/^\*\./, ''); // Remove wildcard prefix
    const base = `/etc/letsencrypt/live/${clean}`;
    document.getElementById('m-cert-path').value = `${base}/cert.pem`;
    document.getElementById('m-key-path').value = `${base}/privkey.pem`;
    document.getElementById('m-fullchain-path').value = `${base}/fullchain.pem`;
    toast('Paths auto-filled');
}

/* Toggles DNS plugin input visibility based on challenge type selection */
function toggleDnsPlugin() {
    const ct = document.getElementById('m-challenge-type').value;
    document.getElementById('dns-plugin-wrap').style.display = ct === 'dns-01' ? 'block' : 'none';
}

/* Saves a new or updated SSL certificate with all fields from the 3-step form */
async function saveSslCertificate(id) {
    /* Collect alt domains from tags */
    const altTags = document.querySelectorAll('#sc-alt-domains-list .sc-alt-domain-tag');
    const altDomains = [...altTags].map(t => t.textContent.replace('\u00d7', '').trim()).filter(d => d).join(', ');

    const prov = document.getElementById('m-provider').value;
    const isCertbot = prov === 'certbot';

    const body = {
        domain: document.getElementById('m-domain').value,
        alt_domains: altDomains || null,
        email: document.getElementById(isCertbot ? 'm-email' : 'm-email-manual')?.value || null,
        provider: prov,
        status: document.getElementById('m-status').value,
        challenge_type: isCertbot
            ? (document.getElementById('m-challenge-type')?.value || 'http-01')
            : (document.getElementById('m-challenge-type-manual')?.value || 'http-01'),
        dns_plugin: document.getElementById('m-dns-plugin')?.value || null,
        cert_path: document.getElementById('m-cert-path')?.value || null,
        key_path: document.getElementById('m-key-path')?.value || null,
        fullchain_path: document.getElementById('m-fullchain-path')?.value || null,
        issued_at: document.getElementById('m-issued-at')?.value || null,
        expires_at: document.getElementById('m-expires-at')?.value || null,
        auto_renew: document.getElementById('m-auto-renew').checked,
        comment: document.getElementById('m-comment').value || null,
    };
    try {
        if (id) await api(`/api/ssl-certificates/${id}`, { method: 'PUT', body: JSON.stringify(body) });
        else await api('/api/ssl-certificates', { method: 'POST', body: JSON.stringify(body) });
        closeModal(); toast(id ? 'Updated' : 'Created'); loadSslCertificates();
    } catch (err) { toast(err.message, 'error'); }
}

/* Deletes an SSL certificate record after confirmation */
async function deleteSslCertificate(id) {
    await crudDelete(`/api/ssl-certificates/${id}`, 'Delete this SSL certificate record?', loadSslCertificates);
}

/* Shows a modal with certbot obtain, renew, and revoke commands for a certificate */
async function showCertbotCommand(certId) {
    try {
        const [obtain, renew, revoke] = await Promise.all([
            api(`/api/ssl-certificates/${certId}/certbot-command`),
            api(`/api/ssl-certificates/${certId}/renew-command`),
            api(`/api/ssl-certificates/${certId}/revoke-command`),
        ]);
        openModal(`
            <h3>${SVG.code} Certbot Commands</h3>
            <p style="font-size:.78rem;color:var(--text-dim);margin-bottom:1rem">Copy and run these commands on your server to manage the certificate with Let\u2019s Encrypt.</p>

            <div class="sc-cmd-section">
                <div class="sc-cmd-title">${SC_IC.shield} Obtain Certificate</div>
                <div class="sc-cmd-desc">${escHtml(obtain.description || 'Generate a new certificate')}</div>
                <div class="sc-cmd-block"><code id="cb-obtain">${escHtml(obtain.command)}</code><button class="sc-cmd-copy" onclick="navigator.clipboard.writeText(document.getElementById('cb-obtain').textContent);toast('Copied!')" title="Copy">${SVG.copy}</button></div>
            </div>

            <div class="sc-cmd-section">
                <div class="sc-cmd-title">${SC_IC.refresh} Renew Certificate</div>
                <div class="sc-cmd-desc">${escHtml(renew.description || 'Renew an existing certificate')}</div>
                <div class="sc-cmd-block"><code id="cb-renew">${escHtml(renew.command)}</code><button class="sc-cmd-copy" onclick="navigator.clipboard.writeText(document.getElementById('cb-renew').textContent);toast('Copied!')" title="Copy">${SVG.copy}</button></div>
            </div>

            <div class="sc-cmd-section">
                <div class="sc-cmd-title">${SC_IC.alert} Revoke Certificate</div>
                <div class="sc-cmd-desc">${escHtml(revoke.description || 'Revoke and delete a certificate')}</div>
                <div class="sc-cmd-block"><code id="cb-revoke">${escHtml(revoke.command)}</code><button class="sc-cmd-copy" onclick="navigator.clipboard.writeText(document.getElementById('cb-revoke').textContent);toast('Copied!')" title="Copy">${SVG.copy}</button></div>
            </div>

            <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Close</button></div>
        `, { wide: true });
    } catch (err) { toast(err.message, 'error'); }
}
