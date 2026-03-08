/**
 * Application entry point
 * =======================
 *
 * Bootstraps the SPA: checks the JWT token, pre-fetches
 * core data into shared state, reveals the UI, and exposes
 * all onclick-handler functions on the global `window` object
 * so that inline HTML event attributes work after esbuild
 * bundles everything into a single IIFE.
 */

import { api, toast, TOKEN } from "./core/api";
import { state } from "./state";

/* Core  */
import { switchSection, openModal, closeModal, initModalListeners, toggleCollapsible, toggleEntityCard } from "./core/ui";
import {
    switchAuthTab,
    handleLogin,
    handleRegister,
    logout,
    showApp,
    checkFirstRun,
    toggleSidebar,
    toggleSidebarCollapse,
    initSidebarListeners,
    toggleUserMenu,
    closeUserMenu,
    initUserMenuListeners,
    openUserSettings,
    saveUserSettings,
} from "./core/auth";

/* Sections  */
import { loadOverview, renderFlowCanvas, drawFlowConnections } from "./sections/overview";
import {
    loadSettings,
    renderSettingsTable,
    reorderSetting,
    switchSettingsTab,
    filterSettingsCat,
    filterSettings,
    openGlobalQuickAdd,
    openDefaultsQuickAdd,
    openSettingsAddModal,
    filterSettingsPresets,
    searchSettPresets,
    applySettingPreset,
    openSettingModal,
    saveSetting,
    deleteSetting,
} from "./sections/settings";
import {
    loadFrontends,
    filterFrontends,
    renderFrontends,
    filterFeOpts,
    searchFeOpts,
    openFrontendModal,
    saveFrontend,
    deleteFrontend,
    openBindModal,
    filterBindPresets,
    filterBindPresetSearch,
    saveBind,
    deleteBind,
    openOptionModal,
    applyOptPreset,
    filterOptPresets,
    filterOptPresetSearch,
    saveOption,
    deleteOption,
} from "./sections/frontends";
import { loadBackends, filterBackends, renderBackends, openBackendModal, saveBackend, deleteBackend, openServerModal, saveServer, deleteServer } from "./sections/backends";
import { loadAclRules, filterAclTable, renderAclTable, openAclModal, toggleAclRedirect, saveAclRule, deleteAclRule, reorderAclRule } from "./sections/acl";
import {
    loadListenBlocks,
    filterListenBlocks,
    renderListenBlocks,
    openListenModal,
    applyListenPreset,
    saveListenBlock,
    openListenBindModal,
    filterLnBindPresets,
    filterLnBindPresetSearch,
    saveListenBind,
    deleteListenBind,
    deleteListenBlock,
} from "./sections/listen";
import {
    loadUserlists,
    filterUserlists,
    renderUserlists,
    openUserlistModal,
    openEntryModal,
    openChangePasswordModal,
    togglePwVis,
    saveEntry,
    savePasswordChange,
    deleteEntry,
    saveUserlist,
    deleteUserlist,
} from "./sections/userlists";
import { loadResolvers, filterResolvers, openResolverModal, openResolverQuickAdd, filterResolverPresets, searchResolverPresets, applyResolverPreset, openNameserverModal, saveResolver, deleteResolver, saveNameserver, deleteNameserver } from "./sections/resolvers";
import { loadPeers, filterPeers, openPeerModal, openPeerEntryModal, savePeer, deletePeer, savePeerEntry, deletePeerEntry } from "./sections/peers";
import { loadMailers, filterMailers, openMailerModal, openMailerEntryModal, saveMailer, deleteMailer, saveMailerEntry, deleteMailerEntry } from "./sections/mailers";
import {
    loadHttpErrors,
    filterHttpErrors,
    openHttpErrorsModal,
    openHttpErrorEntryModal,
    saveHttpErrors,
    deleteHttpErrors,
    saveHttpErrorEntry,
    deleteHttpErrorEntry,
} from "./sections/http-errors";
import { loadCaches, filterCaches, openCacheModal, saveCache, deleteCache } from "./sections/caches";
import {
    loadSslCertificates,
    filterSslCertificates,
    openSslCertificateModal,
    switchDomainTab,
    selectAclDomain,
    filterAclDomains,
    addAltDomain,
    removeAltDomain,
    showAltDomainAclPicker,
    pickAltAclDomain,
    onProviderChange,
    autofillCertPaths,
    toggleDnsPlugin,
    saveSslCertificate,
    deleteSslCertificate,
    showCertbotCommand,
} from "./sections/ssl";
import { exportConfig, copyExport, loadManualEdit, saveManualEdit, discardManualEdit } from "./sections/config";
import { initEmpty, initImport, showSetup } from "./sections/setup";
import { loadHistory, toggleHistoryDiff, rollbackVersion, switchDiffTab } from "./sections/history";
import { loadUsers, filterUsers, openAddUserModal, saveNewUser, deleteUserById, openUserPasswordModal, saveUserPassword } from "./sections/users";
import { checkVersionStatus, refreshPendingBadges, openSaveVersionModal, saveVersion, discardChanges, revertSection, viewSectionChanges } from "./sections/versions";

/* Expose onclick handlers on window  */
Object.assign(window, {
    /* core / ui */
    switchSection,
    openModal,
    closeModal,
    toggleCollapsible,
    toggleEntityCard,
    toast,

    /* auth */
    switchAuthTab,
    handleLogin,
    handleRegister,
    logout,
    toggleSidebar,
    toggleSidebarCollapse,
    toggleUserMenu,
    closeUserMenu,
    openUserSettings,
    saveUserSettings,

    /* overview */
    loadOverview,
    renderFlowCanvas,
    drawFlowConnections,

    /* settings */
    loadSettings,
    renderSettingsTable,
    reorderSetting,
    switchSettingsTab,
    filterSettingsCat,
    filterSettings,
    openGlobalQuickAdd,
    openDefaultsQuickAdd,
    openSettingsAddModal,
    filterSettingsPresets,
    searchSettPresets,
    applySettingPreset,
    openSettingModal,
    saveSetting,
    deleteSetting,

    /* frontends */
    loadFrontends,
    filterFrontends,
    renderFrontends,
    filterFeOpts,
    searchFeOpts,
    openFrontendModal,
    saveFrontend,
    deleteFrontend,
    openBindModal,
    filterBindPresets,
    filterBindPresetSearch,
    saveBind,
    deleteBind,
    openOptionModal,
    applyOptPreset,
    filterOptPresets,
    filterOptPresetSearch,
    saveOption,
    deleteOption,

    /* backends */
    loadBackends,
    filterBackends,
    renderBackends,
    openBackendModal,
    saveBackend,
    deleteBackend,
    openServerModal,
    saveServer,
    deleteServer,

    /* acl */
    loadAclRules,
    filterAclTable,
    renderAclTable,
    openAclModal,
    toggleAclRedirect,
    saveAclRule,
    deleteAclRule,
    reorderAclRule,

    /* listen */
    loadListenBlocks,
    filterListenBlocks,
    renderListenBlocks,
    openListenModal,
    applyListenPreset,
    saveListenBlock,
    openListenBindModal,
    filterLnBindPresets,
    filterLnBindPresetSearch,
    saveListenBind,
    deleteListenBind,
    deleteListenBlock,

    /* userlists */
    loadUserlists,
    filterUserlists,
    renderUserlists,
    openUserlistModal,
    openEntryModal,
    openChangePasswordModal,
    togglePwVis,
    saveEntry,
    savePasswordChange,
    deleteEntry,
    saveUserlist,
    deleteUserlist,

    /* resolvers */
    loadResolvers,
    filterResolvers,
    openResolverModal,
    openResolverQuickAdd,
    filterResolverPresets,
    searchResolverPresets,
    applyResolverPreset,
    openNameserverModal,
    saveResolver,
    deleteResolver,
    saveNameserver,
    deleteNameserver,

    /* peers */
    loadPeers,
    filterPeers,
    openPeerModal,
    openPeerEntryModal,
    savePeer,
    deletePeer,
    savePeerEntry,
    deletePeerEntry,

    /* mailers */
    loadMailers,
    filterMailers,
    openMailerModal,
    openMailerEntryModal,
    saveMailer,
    deleteMailer,
    saveMailerEntry,
    deleteMailerEntry,

    /* http-errors */
    loadHttpErrors,
    filterHttpErrors,
    openHttpErrorsModal,
    openHttpErrorEntryModal,
    saveHttpErrors,
    deleteHttpErrors,
    saveHttpErrorEntry,
    deleteHttpErrorEntry,

    /* caches */
    loadCaches,
    filterCaches,
    openCacheModal,
    saveCache,
    deleteCache,

    /* ssl */
    loadSslCertificates,
    filterSslCertificates,
    openSslCertificateModal,
    switchDomainTab,
    selectAclDomain,
    filterAclDomains,
    addAltDomain,
    removeAltDomain,
    showAltDomainAclPicker,
    pickAltAclDomain,
    onProviderChange,
    autofillCertPaths,
    toggleDnsPlugin,
    saveSslCertificate,
    deleteSslCertificate,
    showCertbotCommand,

    /* config */
    exportConfig,
    copyExport,
    loadManualEdit,
    saveManualEdit,
    discardManualEdit,

    /* setup */
    initEmpty,
    initImport,
    showSetup,

    /* history */
    loadHistory,
    toggleHistoryDiff,
    rollbackVersion,
    switchDiffTab,

    /* users */
    loadUsers,
    filterUsers,
    openAddUserModal,
    saveNewUser,
    deleteUserById,
    openUserPasswordModal,
    saveUserPassword,

    /* versions */
    checkVersionStatus,
    refreshPendingBadges,
    openSaveVersionModal,
    saveVersion,
    discardChanges,
    revertSection,
    viewSectionChanges,
});

/* Init event listeners  */
initModalListeners();
initSidebarListeners();
initUserMenuListeners();

/* Auth form handlers  */
document.getElementById("form-login")?.addEventListener("submit", handleLogin);
document.getElementById("form-register")?.addEventListener("submit", handleRegister);

/* Bootstrap  */
(async function init(): Promise<void> {
    if (!TOKEN) {
        // Check if first-run (no users exist) - show register tab
        await checkFirstRun();
        logout();
        return;
    }
    try {
        const [fe, be, acl, ul] = await Promise.all([
            api("/api/frontends").catch(() => ({ items: [] })),
            api("/api/backends").catch(() => ({ items: [] })),
            api("/api/acl-rules").catch(() => ({ items: [] })),
            api("/api/userlists").catch(() => ({ items: [] })),
        ]);
        state.allFrontends = (fe as any).items || fe;
        state.allBackends = (be as any).items || be;
        state.allAclRules = (acl as any).items || acl;
        state.cachedUserlists = (ul as any).items || ul;

        // Check version status - show setup if not initialized
        const initialized = await checkVersionStatus();
        if (!initialized) {
            // Show auth overlay first, then setup
            document.getElementById("auth-overlay")!.style.display = "none";
            showSetup();
        } else {
            showApp();
        }
    } catch {
        logout();
    }
})();
