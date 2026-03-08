/**
 * Mailers section
 * ===============
 *
 * Manages HAProxy mailer sections for SMTP email alerts
 * on server state changes, with SMTP auth and TLS support.
 */

import { api, toast } from "../core/api";
import { icon, SVG } from "../core/icons";
import { openModal, closeModal } from "../core/ui";
import { escHtml, escJsonAttr, crudDelete } from "../core/utils";
import { state } from "../state";
import type { Mailer, MailerEntry } from "../types";

/** Renders mailer section cards with entry sub-cards showing AUTH/TLS/STARTTLS badges. */
function renderMailersGrid(items: Mailer[]): void {
    const grid = document.getElementById("mailers-grid") as HTMLElement;
    const empty = document.getElementById("mailers-empty") as HTMLElement;
    if (!items.length) {
        grid.innerHTML = "";
        grid.style.display = "none";
        empty.style.display = "block";
        return;
    }
    grid.style.display = "grid";
    grid.style.gridTemplateColumns = "repeat(auto-fill,minmax(380px,1fr))";
    empty.style.display = "none";

    const MIC = {
        mail: icon("mail", 11, 2.5),
        server: icon("server", 11, 2.5),
        clock: icon("clock", 11, 2.5),
    };

    grid.innerHTML = items
        .map((m) => {
            const entries = m.entries || [];
            const features: string[] = [];
            features.push(`<span class="ma-feat ma-feat-mail">${MIC.mail} Mail Section</span>`);
            features.push(`<span class="ma-feat ma-feat-count">${MIC.server} ${entries.length} Mailer${entries.length !== 1 ? "s" : ""}</span>`);
            if (m.timeout_mail) features.push(`<span class="ma-feat ma-feat-timeout">${MIC.clock} ${escHtml(m.timeout_mail)}</span>`);
            if (m.extra_options) features.push(`<span class="ma-feat ma-feat-timeout">${MIC.clock} Extra Opts</span>`);

            const entryCards = entries
                .map((e) => {
                    const badges: string[] = [];
                    if (e.smtp_auth) badges.push('<span class="ma-entry-badge ma-badge-auth">AUTH</span>');
                    if (e.use_tls) badges.push('<span class="ma-entry-badge ma-badge-tls">TLS</span>');
                    if (e.use_starttls) badges.push('<span class="ma-entry-badge ma-badge-tls">STARTTLS</span>');
                    return `<div class="ma-entry-card">
                    <div class="ma-entry-dot${e.smtp_auth ? " ma-dot-auth" : ""}"></div>
                    <div class="ma-entry-body">
                        <div class="ma-entry-name">${escHtml(e.name)}${badges.length ? " " + badges.join(" ") : ""}</div>
                        <div class="ma-entry-addr">${escHtml(e.address)}:<span class="ma-entry-port">${e.port}</span>${e.smtp_user ? " &middot; " + escHtml(e.smtp_user) : ""}</div>
                    </div>
                    <div class="ma-entry-actions">
                        <button class="btn-icon" onclick='openMailerEntryModal(${m.id},${escJsonAttr(e)})'>${SVG.editSm}</button>
                        <button class="btn-icon danger" onclick="deleteMailerEntry(${m.id},${e.id})">${SVG.delSm}</button>
                    </div>
                </div>`;
                })
                .join("");

            return `<div class="item-card ma-card" data-entity-name="${escHtml(m.name)}">
                <div class="item-header"><h3>${escHtml(m.name)}</h3>
                    <div><button class="btn-icon" onclick='openMailerModal(${escJsonAttr(m)})'>${SVG.edit}</button>
                    <button class="btn-icon danger" onclick="deleteMailer(${m.id})">${SVG.del}</button></div>
                </div>
                <div class="ma-features">${features.join("")}</div>
                ${m.comment ? `<div class="ma-custom-opts"><span class="ma-custom-label">Comment</span><span>${escHtml(m.comment)}</span></div>` : ""}
                <div class="ma-entries-section">
                    <div class="ma-entries-head"><span>${MIC.server} Mailer Entries <span class="ma-entry-count">${entries.length}</span></span>
                        <button class="btn-icon" onclick="openMailerEntryModal(${m.id})">${SVG.plus}</button></div>
                    <div class="ma-entries-grid">${entryCards || `<div class="ma-entry-empty">${MIC.mail} No mailer entries configured</div>`}</div>
                </div>
                ${m.extra_options ? `<div class="ma-custom-opts"><span class="ma-custom-label">Extra</span><span class="mono">${escHtml(m.extra_options).substring(0, 300)}</span></div>` : ""}
            </div>`;
        })
        .join("");
}

/** Fetches all mailer sections from the API and renders cards. */
export async function loadMailers(): Promise<void> {
    try {
        const d: { items: Mailer[] } = await api("/api/mailers");
        state.allMailers = d.items || d;
        renderMailersGrid(state.allMailers);
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Filters mailer sections by name, comment, or entry name/address. */
export function filterMailers(): void {
    const q = ((document.getElementById("mailer-search") as HTMLInputElement).value || "").toLowerCase();
    if (!q) {
        renderMailersGrid(state.allMailers);
        return;
    }
    renderMailersGrid(
        state.allMailers.filter(
            (m) =>
                m.name.toLowerCase().includes(q) ||
                (m.comment || "").toLowerCase().includes(q) ||
                (m.entries || []).some((e) => (e.name || "").toLowerCase().includes(q) || (e.address || "").toLowerCase().includes(q)),
        ),
    );
}

/** Opens mailer section create/edit modal with identification and timeout settings. */
export function openMailerModal(existing: Partial<Mailer> | null = null): void {
    const m = existing || {};
    const SEC = {
        mail: icon("mail", 15),
        timeout: icon("clock", 15),
    };
    openModal(
        `
        <h3>${m.id ? "Edit" : "New"} Mailer Section</h3>
        <p class="modal-subtitle">Configure an SMTP mailer section for sending email alerts on server state changes via email-alert directives.</p>

        <div class="form-section-title">${SEC.mail} Identification</div>
        <div class="form-row"><div>
            <label>Section Name</label><input id="m-name" value="${escHtml(m.name || "")}" placeholder="mymailers">
            <div class="form-help">Unique name referenced by email-alert mailers directive</div>
        </div><div>
            <label>Comment</label><input id="m-comment" value="${escHtml(m.comment || "")}" placeholder="Optional description...">
            <div class="form-help">Internal note for documentation purposes</div>
        </div></div>

        <hr class="form-divider">
        <div class="form-section-title">${SEC.timeout} Timeout</div>
        <div class="form-row"><div>
            <label>Timeout Mail</label><input id="m-timeout-mail" value="${escHtml(m.timeout_mail || "")}" placeholder="10s">
            <div class="form-help">Maximum time to send an email (e.g. 10s, 30s, 1m)</div>
        </div><div>
            <label>&nbsp;</label>
            <div class="form-help" style="margin-top:.5rem">If not set, HAProxy uses a default timeout. Recommended: 10-30 seconds for reliable SMTP delivery.</div>
        </div></div>

        <div class="form-collapsible" style="margin-top:1rem">
            <div class="form-collapsible-head" onclick="toggleCollapsible(this)">${SEC.timeout} Advanced Options ${SVG.chevron}</div>
            <div class="form-collapsible-body">
                <label>Extra Options</label>
                <textarea id="m-extra" rows="4" placeholder="One directive per line">${escHtml(m.extra_options || "")}</textarea>
                <div class="form-help">Additional HAProxy directives for this mailers section (one per line)</div>
            </div>
        </div>

        <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="saveMailer(${m.id || "null"})">${m.id ? "Update" : "Create"} Mailer Section</button></div>
    `,
        { wide: true },
    );
}

/** Opens mailer entry create/edit modal with SMTP server, auth, and TLS settings. */
export function openMailerEntryModal(mailerId: number, existing: Partial<MailerEntry> | null = null): void {
    const e = existing || {};
    const SEC = {
        server: icon("server", 15),
        network: icon("arrow-right", 15),
        lock: icon("lock", 15),
        shield: icon("shield", 15),
    };
    openModal(
        `
        <h3>${e.id ? "Edit" : "New"} Mailer Entry</h3>
        <p class="modal-subtitle">Define an SMTP server endpoint for sending email alerts.</p>

        <div class="form-section-title">${SEC.server} SMTP Server</div>
        <div class="form-row"><div>
            <label>Mailer Name</label><input id="m-name" value="${escHtml(e.name || "")}" placeholder="smtp1">
            <div class="form-help">Logical name for this SMTP server</div>
        </div><div>
            <label>Sort Order</label><input type="number" id="m-sort" value="${e.sort_order || 0}" min="0">
            <div class="form-help">Display/config order (lower = first)</div>
        </div></div>

        <hr class="form-divider">
        <div class="form-section-title">${SEC.network} Connection</div>
        <div class="form-row"><div>
            <label>SMTP Address</label><input id="m-address" value="${escHtml(e.address || "")}" placeholder="smtp.example.com">
            <div class="form-help">Hostname or IP of the SMTP relay server</div>
        </div><div>
            <label>Port</label><input type="number" id="m-port" value="${e.port || 25}" min="1" max="65535">
            <div class="form-help">25 (SMTP), 465 (SMTPS), 587 (Submission)</div>
        </div></div>

        <hr class="form-divider">
        <div class="form-section-title">${SEC.lock} Authentication</div>
        <div class="form-row"><div>
            <label class="toggle-wrap"><input type="checkbox" id="m-smtp-auth" ${e.smtp_auth ? "checked" : ""} onchange="document.getElementById('smtp-auth-fields').style.display=this.checked?'':'none'"> Enable SMTP Authentication</label>
            <div class="form-help">Authenticate with username &amp; password before sending</div>
        </div><div></div></div>
        <div id="smtp-auth-fields" style="display:${e.smtp_auth ? "" : "none"}">
            <div class="form-row"><div>
                <label>Username</label><input id="m-smtp-user" value="${escHtml(e.smtp_user || "")}" placeholder="user@example.com" autocomplete="off">
                <div class="form-help">SMTP login username</div>
            </div><div>
                <label>Password</label><input type="password" id="m-smtp-password" value="" placeholder="${e.has_smtp_password ? "••• (leave empty to keep)" : "Enter password"}" autocomplete="new-password">
                <div class="form-help">SMTP login password (stored encrypted)</div>
            </div></div>
        </div>

        <hr class="form-divider">
        <div class="form-section-title">${SEC.shield} Transport Security</div>
        <div class="form-row"><div>
            <label class="toggle-wrap"><input type="checkbox" id="m-use-tls" ${e.use_tls ? "checked" : ""}> Use TLS (implicit)</label>
            <div class="form-help">Connect with TLS from the start (port 465)</div>
        </div><div>
            <label class="toggle-wrap"><input type="checkbox" id="m-use-starttls" ${e.use_starttls ? "checked" : ""}> Use STARTTLS</label>
            <div class="form-help">Upgrade plain connection to TLS (port 587)</div>
        </div></div>

        <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="saveMailerEntry(${mailerId},${e.id || "null"})">${e.id ? "Update" : "Add"} Mailer Entry</button></div>
    `,
        { wide: true },
    );
}

/** Saves a new or updated mailer section with name, timeout, and extra options. */
export async function saveMailer(id: number | null): Promise<void> {
    const body = {
        name: (document.getElementById("m-name") as HTMLInputElement).value,
        timeout_mail: (document.getElementById("m-timeout-mail") as HTMLInputElement).value || null,
        comment: (document.getElementById("m-comment") as HTMLInputElement).value || null,
        extra_options: (document.getElementById("m-extra") as HTMLTextAreaElement).value || null,
    };
    try {
        if (id) await api(`/api/mailers/${id}`, { method: "PUT", body: JSON.stringify(body) });
        else await api("/api/mailers", { method: "POST", body: JSON.stringify(body) });
        closeModal();
        toast(id ? "Updated" : "Created");
        loadMailers();
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Deletes a mailer section after confirmation. */
export async function deleteMailer(id: number): Promise<void> {
    await crudDelete(`/api/mailers/${id}`, "Delete this mailer section?", loadMailers);
}

/** Saves a new or updated mailer entry with SMTP auth, TLS, and STARTTLS settings. */
export async function saveMailerEntry(mailerId: number, entryId: number | null): Promise<void> {
    const smtpAuth = (document.getElementById("m-smtp-auth") as HTMLInputElement).checked;
    const smtpPassword = smtpAuth ? (document.getElementById("m-smtp-password") as HTMLInputElement).value || null : null;
    const body: Record<string, unknown> = {
        name: (document.getElementById("m-name") as HTMLInputElement).value,
        address: (document.getElementById("m-address") as HTMLInputElement).value,
        port: parseInt((document.getElementById("m-port") as HTMLInputElement).value) || 25,
        sort_order: parseInt((document.getElementById("m-sort") as HTMLInputElement).value) || 0,
        smtp_auth: smtpAuth,
        smtp_user: smtpAuth ? (document.getElementById("m-smtp-user") as HTMLInputElement).value || null : null,
        use_tls: (document.getElementById("m-use-tls") as HTMLInputElement).checked,
        use_starttls: (document.getElementById("m-use-starttls") as HTMLInputElement).checked,
    };
    // Only include smtp_password when provided to avoid clearing existing passwords on update
    if (smtpPassword) body.smtp_password = smtpPassword;
    try {
        if (entryId) await api(`/api/mailers/${mailerId}/entries/${entryId}`, { method: "PUT", body: JSON.stringify(body) });
        else await api(`/api/mailers/${mailerId}/entries`, { method: "POST", body: JSON.stringify(body) });
        closeModal();
        toast("Saved");
        loadMailers();
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Deletes a mailer entry after confirmation. */
export async function deleteMailerEntry(mailerId: number, entryId: number): Promise<void> {
    await crudDelete(`/api/mailers/${mailerId}/entries/${entryId}`, "Delete this mailer entry?", loadMailers);
}
