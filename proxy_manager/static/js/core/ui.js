/*
User Interface
==============

Section switching with navigation highlighting, modal dialogs,
collapsible panels, and entity card expand/collapse behavior.
*/

/* Human-readable titles displayed in the top bar for each section */
const _sectionTitles = {
    overview: 'Dashboard',
    global: 'Global Settings',
    defaults: 'Defaults',
    frontends: 'Frontends',
    backends: 'Backends',
    acl: 'ACL Routing',
    listen: 'Listen / Stats',
    userlists: 'User Lists',
    'ssl-certificates': 'SSL / TLS Certificates',
    resolvers: 'DNS Resolvers',
    peers: 'Peers',
    mailers: 'Mailers',
    'http-errors': 'HTTP Errors',
    caches: 'Cache',
    config: 'Config Import/Export',
};

/* Switches the active SPA section, updates nav highlighting, and triggers data loading */
function switchSection(name) {
    document.querySelectorAll('.nav-item').forEach(i => i.classList.toggle('active', i.dataset.section === name));
    document.querySelectorAll('.section').forEach(s => s.classList.toggle('active', s.id === `sec-${name}`));
    const titleEl = document.getElementById('top-bar-page-title');
    if (titleEl) titleEl.textContent = _sectionTitles[name] || name;
    // Close sidebar on mobile after navigation
    document.getElementById('sidebar')?.classList.remove('open');
    document.getElementById('sidebar-backdrop')?.classList.remove('open');
    const loaders = {
        overview: loadOverview,
        global: () => loadSettings('global'),
        defaults: () => loadSettings('defaults'),
        frontends: loadFrontends,
        backends: loadBackends,
        acl: loadAclRules,
        listen: loadListenBlocks,
        userlists: loadUserlists,
        resolvers: loadResolvers,
        peers: loadPeers,
        mailers: loadMailers,
        'http-errors': loadHttpErrors,
        caches: loadCaches,
        'ssl-certificates': loadSslCertificates,
    };
    if (loaders[name]) loaders[name]();
}

/* Opens a centered modal dialog with the given HTML content */
function openModal(html, opts = {}) {
    const m = document.getElementById('modal-content');
    m.innerHTML = html;
    m.classList.toggle('modal-wide', !!opts.wide);
    document.getElementById('modal-overlay').classList.add('show');
}

/* Closes the currently open modal dialog */
function closeModal() {
    document.getElementById('modal-overlay').classList.remove('show');
}

/* Close modal on Escape key */
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

/* Close modal when clicking the backdrop outside the modal content */
document.getElementById('modal-overlay').addEventListener('click', e => {
    if (e.target === document.getElementById('modal-overlay')) closeModal();
});

/* Toggles a collapsible form section open/closed */
function toggleCollapsible(el) {
    el.classList.toggle('open');
    el.nextElementSibling.classList.toggle('open');
}

/* Toggles an entity card (backend server, bind entry, etc.) expanded/collapsed */
function toggleEntityCard(el) {
    el.closest('.entity-card').classList.toggle('open');
}
