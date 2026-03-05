/*
Application Initializer
=======================
*/

/* Self-executing init - runs once all scripts are loaded */
(async function init() {
    if (!TOKEN) { logout(); return; }
    try {
        const [fe, be, acl, ul] = await Promise.all([
            api('/api/frontends').catch(() => ({ items: [] })),
            api('/api/backends').catch(() => ({ items: [] })),
            api('/api/acl-rules').catch(() => ({ items: [] })),
            api('/api/userlists').catch(() => ({ items: [] })),
        ]);
        allFrontends = fe.items || fe;
        allBackends = be.items || be;
        allAclRules = acl.items || acl;
        window._cachedUserlists = ul.items || ul;
        showApp();
    } catch { logout(); }
})();
