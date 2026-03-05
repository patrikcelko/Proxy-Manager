/*
Utilities
=========
*/

/* Escapes HTML special characters to prevent XSS in rendered templates */
function escHtml(s) {
    if (s == null) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

/* Encodes a JS object as an HTML-safe JSON string for use in onclick attributes */
function escJsonAttr(obj) {
    return JSON.stringify(obj).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

/* Parses a string to integer, returning fallback if not a number */
function safeInt(val, fallback = null) {
    const n = parseInt(val, 10);
    return isNaN(n) ? fallback : n;
}

/* Generic CRUD save: creates or updates an entity and reloads on success */
async function crudSave(baseUrl, body, entityId, reloadFn) {
    try {
        if (entityId) await api(`${baseUrl}/${entityId}`, { method: 'PUT', body: JSON.stringify(body) });
        else await api(baseUrl, { method: 'POST', body: JSON.stringify(body) });
        toast('Saved'); closeModal(); reloadFn();
    } catch (err) { toast(err.message, 'error'); }
}

/* Generic CRUD delete: confirms with user then deletes and reloads */
async function crudDelete(url, confirmMsg, reloadFn) {
    if (!confirm(confirmMsg)) return;
    try { await api(url, { method: 'DELETE' }); toast('Deleted'); reloadFn(); }
    catch (err) { toast(err.message, 'error'); }
}

/* Generic preset grid filter: shows/hides cards by category tab */
function filterPresetGrid(gridId, searchId, catAttr, cat) {
    const grid = document.getElementById(gridId);
    if (!grid) return;
    const searchInput = document.getElementById(searchId);
    if (searchInput) searchInput.value = '';
    const label = cat === 'all' ? 'All' : cat;
    grid.closest('.modal').querySelectorAll('.stabs .stab').forEach(t =>
        t.classList.toggle('active', t.textContent.trim() === label));
    grid.querySelectorAll('.dir-card').forEach(c =>
        c.style.display = (cat === 'all' || c.dataset[catAttr] === cat) ? '' : 'none');
}

/* Generic preset grid search: filters cards by free-text query */
function searchPresetGrid(gridId, searchId, catAttr, resetCat = 'all') {
    const q = (document.getElementById(searchId)?.value || '').toLowerCase().trim();
    const grid = document.getElementById(gridId);
    if (!grid) return;
    if (!q) { filterPresetGrid(gridId, searchId, catAttr, resetCat); return; }
    grid.closest('.modal').querySelectorAll('.stabs .stab').forEach(t => t.classList.remove('active'));
    grid.querySelectorAll('.dir-card').forEach(c =>
        c.style.display = (c.dataset.searchText || '').includes(q) ? '' : 'none');
}
