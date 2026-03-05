/*
HTTP Errors Section
===================

Manages HAProxy http-errors sections with custom error
responses (errorfile, errorloc, errorloc302, errorloc303).
*/

/* Global list of all HTTP error groups, populated by loadHttpErrors() */
let allHttpErrors = [];

/* Renders HTTP error group cards with entry sub-cards showing status codes and types */
function renderHttpErrorsGrid(items) {
    const grid = document.getElementById('http-errors-grid');
    const empty = document.getElementById('http-errors-empty');
    if (!items.length) { grid.innerHTML = ''; grid.style.display = 'none'; empty.style.display = 'block'; return; }
    grid.style.display = 'grid'; grid.style.gridTemplateColumns = 'repeat(auto-fill,minmax(380px,1fr))'; empty.style.display = 'none';

        const HIC = {
            warning: icon('alert-triangle', 11, 2.5),
            file: icon('file', 11, 2.5),
            redirect: icon('redirect', 11, 2.5),
            hash: icon('hash', 11, 2.5),
        };

        grid.innerHTML = items.map(s => {
            const entries = (s.entries || []);
            const errorfileCount = entries.filter(e => e.type === 'errorfile').length;
            const errorlocCount = entries.filter(e => e.type !== 'errorfile').length;
            const features = [];
            if (errorfileCount) features.push(`<span class="he-feat he-feat-errorfile">${HIC.file} ${errorfileCount} errorfile${errorfileCount !== 1 ? 's' : ''}</span>`);
            if (errorlocCount) features.push(`<span class="he-feat he-feat-errorloc">${HIC.redirect} ${errorlocCount} errorloc</span>`);
            features.push(`<span class="he-feat he-feat-count">${HIC.hash} ${entries.length} total</span>`);

            const entryCards = entries.map(e => {
                const codeClass = e.status_code >= 500 ? 'he-entry-code-5xx' : (e.status_code >= 400 ? 'he-entry-code-4xx' : '');
                return `<div class="he-entry-card">
                    <div class="he-entry-code ${codeClass}">${e.status_code}</div>
                    <div class="he-entry-body">
                        <div class="he-entry-type">${escHtml(e.type)}</div>
                        <div class="he-entry-value">${escHtml(e.value)}</div>
                    </div>
                    <div class="he-entry-actions">
                        <button class="btn-icon" onclick='openHttpErrorEntryModal(${s.id},${escJsonAttr(e)})'>${SVG.editSm}</button>
                        <button class="btn-icon danger" onclick="deleteHttpErrorEntry(${s.id},${e.id})">${SVG.delSm}</button>
                    </div>
                </div>`;
            }).join('');

            return `<div class="item-card he-card">
                <div class="item-header"><h3>${escHtml(s.name)}</h3>
                    <div><button class="btn-icon" onclick='openHttpErrorsModal(${escJsonAttr(s)})'>${SVG.edit}</button>
                    <button class="btn-icon danger" onclick="deleteHttpErrors(${s.id})">${SVG.del}</button></div>
                </div>
                <div class="he-features">${features.join('')}</div>
                ${s.comment ? `<div class="he-custom-opts"><span class="he-custom-label">Comment</span><span>${escHtml(s.comment)}</span></div>` : ''}
                <div class="he-entries-section">
                    <div class="he-entries-head"><span>${HIC.warning} Error Entries <span class="he-entry-count">${entries.length}</span></span>
                        <button class="btn-icon" onclick="openHttpErrorEntryModal(${s.id})">${SVG.plus}</button></div>
                    <div class="he-entries-grid">${entryCards || `<div class="he-entry-empty">${HIC.warning} No error entries configured</div>`}</div>
                </div>
                ${s.extra_options ? `<div class="he-custom-opts"><span class="he-custom-label">Extra</span><span class="mono">${escHtml(s.extra_options).substring(0, 300)}</span></div>` : ''}
            </div>`;
        }).join('');
}

/* Fetches all HTTP error groups from the API and renders cards */
async function loadHttpErrors() {
    try {
        const d = await api('/api/http-errors');
        allHttpErrors = d.items || d;
        renderHttpErrorsGrid(allHttpErrors);
    } catch (err) { toast(err.message, 'error'); }
}

/* Filters HTTP error groups by name, comment, status code, type, or value */
function filterHttpErrors() {
    const q = (document.getElementById('http-error-search').value || '').toLowerCase();
    if (!q) { renderHttpErrorsGrid(allHttpErrors); return; }
    renderHttpErrorsGrid(allHttpErrors.filter(s =>
        s.name.toLowerCase().includes(q) ||
        (s.comment || '').toLowerCase().includes(q) ||
        (s.entries || []).some(e => String(e.status_code).includes(q) || (e.type || '').toLowerCase().includes(q) || (e.value || '').toLowerCase().includes(q))
    ));
}

/* Opens HTTP errors group create/edit modal with name, comment, and advanced options */
function openHttpErrorsModal(existing = null) {
    const s = existing || {};
    const SEC = {
        warning: icon('alert-triangle', 15),
        opts: icon('terminal', 15),
    };
    openModal(`
        <h3>${s.id ? 'Edit' : 'New'} HTTP Errors Group</h3>
        <p class="modal-subtitle">Define a named group of custom error responses. Reference via errorfiles directive in frontends/backends.</p>

        <div class="form-section-title">${SEC.warning} Identification</div>
        <div class="form-row"><div>
            <label>Group Name</label><input id="m-name" value="${escHtml(s.name||'')}" placeholder="custom-errors">
            <div class="form-help">Unique name referenced by errorfiles &lt;name&gt; directive</div>
        </div><div>
            <label>Comment</label><input id="m-comment" value="${escHtml(s.comment||'')}" placeholder="Optional description...">
            <div class="form-help">Internal note for documentation purposes</div>
        </div></div>

        <div class="form-collapsible" style="margin-top:1rem">
            <div class="form-collapsible-head" onclick="toggleCollapsible(this)">${SEC.opts} Advanced Options ${SVG.chevron}</div>
            <div class="form-collapsible-body">
                <label>Extra Options</label>
                <textarea id="m-extra" rows="4" placeholder="One directive per line">${escHtml(s.extra_options||'')}</textarea>
                <div class="form-help">Additional HAProxy directives for this http-errors section (one per line)</div>
            </div>
        </div>

        <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="saveHttpErrors(${s.id||'null'})">${s.id ? 'Update' : 'Create'} Error Group</button></div>
    `, { wide: true });
}

/* Opens error entry create/edit modal with status code, response type, and value */
function openHttpErrorEntryModal(sectionId, existing = null) {
    const e = existing || {};
    const SEC = {
        file: icon('file', 15),
        redirect: icon('redirect', 15),
        hash: icon('hash', 15),
    };
    openModal(`
        <h3>${e.id ? 'Edit' : 'New'} Error Entry</h3>
        <p class="modal-subtitle">Map an HTTP status code to a custom error file on disk or a redirect URL.</p>

        <div class="form-section-title">${SEC.hash} Status Code</div>
        <div class="form-row"><div>
            <label>HTTP Status Code</label><input type="number" id="m-status-code" value="${e.status_code||''}" placeholder="503" min="100" max="599">
            <div class="form-help">HTTP error code to intercept (e.g. 400, 403, 500, 502, 503)</div>
        </div><div>
            <label>Sort Order</label><input type="number" id="m-sort" value="${e.sort_order||0}" min="0">
            <div class="form-help">Display/config order (lower = first)</div>
        </div></div>

        <hr class="form-divider">
        <div class="form-section-title">${SEC.file} Response Type</div>
        <div class="form-row"><div>
            <label>Type</label>
            <select id="m-type">
                <option value="errorfile" ${(e.type||'errorfile')==='errorfile'?'selected':''}>errorfile - local file path</option>
                <option value="errorloc" ${e.type==='errorloc'?'selected':''}>errorloc - redirect (same method)</option>
                <option value="errorloc302" ${e.type==='errorloc302'?'selected':''}>errorloc302 - redirect (302 Found)</option>
                <option value="errorloc303" ${e.type==='errorloc303'?'selected':''}>errorloc303 - redirect (303 See Other)</option>
            </select>
            <div class="form-help">errorfile = serve local file; errorloc = redirect client to URL</div>
        </div><div>
            <label>Value (path or URL)</label><input id="m-value" value="${escHtml(e.value||'')}" placeholder="/etc/haproxy/errors/503.http">
            <div class="form-help">File path for errorfile, or URL for errorloc redirects</div>
        </div></div>

        <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="saveHttpErrorEntry(${sectionId},${e.id||'null'})">${e.id ? 'Update' : 'Add'} Error Entry</button></div>
    `, { wide: true });
}

/* Saves a new or updated HTTP errors group with name, comment, and extra options */
async function saveHttpErrors(id) {
    const body = {
        name: document.getElementById('m-name').value,
        comment: document.getElementById('m-comment').value || null,
        extra_options: document.getElementById('m-extra').value || null,
    };
    try {
        if (id) await api(`/api/http-errors/${id}`, { method: 'PUT', body: JSON.stringify(body) });
        else await api('/api/http-errors', { method: 'POST', body: JSON.stringify(body) });
        closeModal(); toast(id ? 'Updated' : 'Created'); loadHttpErrors();
    } catch (err) { toast(err.message, 'error'); }
}

/* Deletes an HTTP errors group after confirmation */
async function deleteHttpErrors(id) {
    await crudDelete(`/api/http-errors/${id}`, 'Delete this HTTP errors group?', loadHttpErrors);
}

/* Saves a new or updated error entry with status code, type, and value */
async function saveHttpErrorEntry(sectionId, entryId) {
    const body = {
        status_code: safeInt(document.getElementById('m-status-code').value),
        type: document.getElementById('m-type').value,
        value: document.getElementById('m-value').value,
        sort_order: parseInt(document.getElementById('m-sort').value) || 0,
    };
    try {
        if (entryId) await api(`/api/http-errors/${sectionId}/entries/${entryId}`, { method: 'PUT', body: JSON.stringify(body) });
        else await api(`/api/http-errors/${sectionId}/entries`, { method: 'POST', body: JSON.stringify(body) });
        closeModal(); toast('Saved'); loadHttpErrors();
    } catch (err) { toast(err.message, 'error'); }
}

/* Deletes an error entry after confirmation */
async function deleteHttpErrorEntry(sectionId, entryId) {
    await crudDelete(`/api/http-errors/${sectionId}/entries/${entryId}`, 'Delete this error entry?', loadHttpErrors);
}
