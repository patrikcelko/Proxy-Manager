/**
 * Userlists section
 * =================
 *
 * Manages HAProxy user lists with username/password entries
 * for HTTP Basic Authentication on backends.
 */

import { api, toast } from "../core/api";
import { icon, SVG } from "../core/icons";
import { openModal, closeModal } from "../core/ui";
import { escHtml, escJsonAttr, crudDelete } from "../core/utils";
import { state } from "../state";
import type { Userlist, UserlistEntry } from "../types";

/** Current filter query for userlists search. */
let userlistFilter = "";

/** Fetches all userlists from the API and renders the card grid. */
export async function loadUserlists(): Promise<void> {
    try {
        const d: { items: Userlist[] } = await api("/api/userlists");
        state.allUserlists = d.items || d;
        state.cachedUserlists = null; // Invalidate cache used by backend auth dropdown
        renderUserlists(state.allUserlists);
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Filters userlists by search query across list name and usernames. */
export function filterUserlists(): void {
    userlistFilter = ((document.getElementById("userlist-search") as HTMLInputElement).value || "").toLowerCase();
    renderUserlists(
        state.allUserlists.filter((u) => {
            const entries = u.entries || [];
            const hay = [u.name, ...entries.map((e) => e.username)].filter(Boolean).join(" ").toLowerCase();
            return hay.includes(userlistFilter);
        }),
    );
}

/** Renders userlist cards with user entry sub-cards showing credentials and actions. */
export function renderUserlists(list: Userlist[]): void {
    const grid = document.getElementById("userlists-grid") as HTMLElement;
    const empty = document.getElementById("userlists-empty") as HTMLElement;
    if (!list.length) {
        grid.innerHTML = "";
        grid.style.display = "none";
        empty.style.display = "block";
        return;
    }
    grid.style.display = "grid";
    grid.style.gridTemplateColumns = "repeat(auto-fill,minmax(380px,1fr))";
    empty.style.display = "none";

    const IC = {
        user: icon("user", 13),
        lock: icon("lock", 13),
        shield: icon("shield", 13),
        key: icon("key", 13),
    };

    grid.innerHTML = list
        .map((u) => {
            const entries = u.entries || [];
            const ec = entries.length;

            const userRows = entries
                .map(
                    (e) => `<div class="ul-user-card">
                <div class="ul-user-indicator"></div>
                <div class="ul-user-body">
                    <div class="ul-user-name">${IC.user} ${escHtml(e.username)}</div>
                    <div class="ul-user-pw">${IC.lock} <span class="ul-pw-mask">••••••••</span></div>
                </div>
                <div class="ul-user-badges">
                    ${e.has_password ? '<span class="badge badge-ok">secured</span>' : '<span class="badge badge-warn">no password</span>'}
                    <span class="badge badge-muted">#${e.sort_order}</span>
                </div>
                <div class="ul-user-actions">
                    <button class="btn-icon" onclick="openEntryModal(${u.id},${e.id})" title="Edit user">${SVG.editSm}</button>
                    <button class="btn-icon" onclick="openChangePasswordModal(${u.id},${e.id})" title="Change password">${IC.key}</button>
                    <button class="btn-icon danger" onclick="deleteEntry(${u.id},${e.id})" title="Delete user">${SVG.delSm}</button>
                </div>
            </div>`,
                )
                .join("");

            const features: string[] = [];
            features.push(`<span class="ul-feat ul-feat-shield">${IC.shield} Auth List</span>`);
            features.push(`<span class="ul-feat ul-feat-users">${IC.user} ${ec} user${ec !== 1 ? "s" : ""}</span>`);

            return `<div class="item-card ul-card" data-entity-name="${escHtml(u.name)}">
            <div class="item-header"><h3>${escHtml(u.name)}</h3>
                <div><button class="btn-icon" onclick='openUserlistModal(${escJsonAttr(u)})'>${SVG.edit}</button>
                <button class="btn-icon danger" onclick="deleteUserlist(${u.id})">${SVG.del}</button></div>
            </div>
            <div class="ul-features">${features.join("")}</div>
            <div class="ul-users-section">
                <div class="ul-users-head"><span>${IC.user} Users <span class="ul-user-count">${ec}</span></span>
                    <button class="btn-icon" onclick="openEntryModal(${u.id})" title="Add user">${SVG.plus}</button></div>
                <div class="ul-users-grid">${userRows || '<div class="ul-user-empty">No users configured</div>'}</div>
            </div>
        </div>`;
        })
        .join("");
}

/** Opens the userlist create/edit modal for naming the list. */
export function openUserlistModal(existing: Partial<Userlist> | null = null): void {
    const u = existing || {};
    openModal(`
        <h3>${u.id ? "Edit" : "New"} Auth List</h3>
        <div class="form-section">
            <div class="form-section-title">General</div>
            <div class="form-row">
                <div class="form-group" style="flex:1">
                    <label>List Name</label>
                    <input id="m-name" value="${escHtml(u.name || "")}" placeholder="e.g. myusers">
                    <div class="form-help">Unique name referenced in backend <code>auth_userlist</code> directive.</div>
                </div>
            </div>
        </div>
        <div class="modal-actions">
            <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="saveUserlist(${u.id || "null"})">${u.id ? "Update" : "Create"}</button>
        </div>
    `);
}

/** Opens the user entry create/edit modal with username, password, and sort order. */
export function openEntryModal(userlistId: number, entryId?: number): void {
    let e: Partial<UserlistEntry> = {};
    if (entryId) {
        for (const ul of state.allUserlists) {
            const found = (ul.entries || []).find((x) => x.id === entryId);
            if (found) {
                e = found;
                break;
            }
        }
    }
    const isEdit = !!e.id;
    openModal(`
        <h3>${isEdit ? "Edit" : "New"} User Entry</h3>
        <div class="form-section">
            <div class="form-section-title">Credentials</div>
            <div class="form-row">
                <div class="form-group" style="flex:1">
                    <label>Username</label>
                    <input id="m-username" value="${escHtml(e.username || "")}" placeholder="e.g. admin" ${isEdit ? "" : "autofocus"}>
                </div>
            </div>
            ${isEdit
            ? ""
            : `<div class="form-row">
                <div class="form-group" style="flex:1">
                    <label>Password</label>
                    <div class="pw-input-wrap">
                        <input type="password" id="m-password" placeholder="Enter password" autocomplete="new-password">
                        <button type="button" class="btn-icon pw-toggle" onclick="togglePwVis('m-password',this)" title="Toggle visibility">
                            ${icon("eye")}
                        </button>
                    </div>
                    <div class="form-help">Password will be securely hashed with bcrypt before storage.</div>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group" style="flex:1">
                    <label>Confirm Password</label>
                    <div class="pw-input-wrap">
                        <input type="password" id="m-password-confirm" placeholder="Confirm password" autocomplete="new-password">
                        <button type="button" class="btn-icon pw-toggle" onclick="togglePwVis('m-password-confirm',this)" title="Toggle visibility">
                            ${icon("eye")}
                        </button>
                    </div>
                </div>
            </div>`
        }
        </div>
        <div class="form-section">
            <div class="form-section-title">Options</div>
            <div class="form-row">
                <div class="form-group" style="flex:0 0 120px">
                    <label>Sort Order</label>
                    <input type="number" id="m-sort" value="${e.sort_order || 0}">
                </div>
            </div>
        </div>
        <div class="modal-actions">
            <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="saveEntry(${userlistId},${e.id || "null"})">${isEdit ? "Update" : "Create"}</button>
        </div>
    `);
}

/** Opens the change password modal for an existing user entry. */
export function openChangePasswordModal(userlistId: number, entryId: number): void {
    openModal(`
        <h3>Change Password</h3>
        <div class="form-section">
            <div class="form-section-title">New Password</div>
            <div class="form-row">
                <div class="form-group" style="flex:1">
                    <label>New Password</label>
                    <div class="pw-input-wrap">
                        <input type="password" id="m-new-pw" placeholder="Enter new password" autocomplete="new-password" autofocus>
                        <button type="button" class="btn-icon pw-toggle" onclick="togglePwVis('m-new-pw',this)" title="Toggle visibility">
                            ${icon("eye")}
                        </button>
                    </div>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group" style="flex:1">
                    <label>Confirm New Password</label>
                    <div class="pw-input-wrap">
                        <input type="password" id="m-new-pw-confirm" placeholder="Confirm new password" autocomplete="new-password">
                        <button type="button" class="btn-icon pw-toggle" onclick="togglePwVis('m-new-pw-confirm',this)" title="Toggle visibility">
                            ${icon("eye")}
                        </button>
                    </div>
                    <div class="form-help">Password will be securely hashed with bcrypt. The old password cannot be recovered.</div>
                </div>
            </div>
        </div>
        <div class="modal-actions">
            <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="savePasswordChange(${userlistId},${entryId})">Change Password</button>
        </div>
    `);
}

/** Toggles password input field visibility between text and password type. */
export function togglePwVis(inputId: string, btn: HTMLButtonElement): void {
    const inp = document.getElementById(inputId) as HTMLInputElement | null;
    if (!inp) return;
    const isPw = inp.type === "password";
    inp.type = isPw ? "text" : "password";
    btn.innerHTML = isPw ? icon("eye-off") : icon("eye");
}

/** Saves a new or updated user entry with username, password, and sort order. */
export async function saveEntry(userlistId: number, entryId: number | null): Promise<void> {
    const username = (document.getElementById("m-username") as HTMLInputElement).value.trim();
    if (!username) {
        toast("Username is required", "error");
        return;
    }

    const body: Record<string, unknown> = { username, sort_order: parseInt((document.getElementById("m-sort") as HTMLInputElement).value) || 0 };

    if (!entryId) {
        const pw = (document.getElementById("m-password") as HTMLInputElement).value;
        const pwc = (document.getElementById("m-password-confirm") as HTMLInputElement).value;
        if (!pw) {
            toast("Password is required", "error");
            return;
        }
        if (pw.length < 4) {
            toast("Password must be at least 4 characters", "error");
            return;
        }
        if (pw !== pwc) {
            toast("Passwords do not match", "error");
            return;
        }
        body.password = pw;
    }

    try {
        if (entryId) await api(`/api/userlists/${userlistId}/entries/${entryId}`, { method: "PUT", body: JSON.stringify(body) });
        else await api(`/api/userlists/${userlistId}/entries`, { method: "POST", body: JSON.stringify(body) });
        closeModal();
        toast(entryId ? "User updated" : "User created");
        loadUserlists();
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Changes a user entry password after validation. */
export async function savePasswordChange(userlistId: number, entryId: number): Promise<void> {
    const pw = (document.getElementById("m-new-pw") as HTMLInputElement).value;
    const pwc = (document.getElementById("m-new-pw-confirm") as HTMLInputElement).value;
    if (!pw) {
        toast("Password is required", "error");
        return;
    }
    if (pw.length < 4) {
        toast("Password must be at least 4 characters", "error");
        return;
    }
    if (pw !== pwc) {
        toast("Passwords do not match", "error");
        return;
    }
    try {
        await api(`/api/userlists/${userlistId}/entries/${entryId}`, {
            method: "PUT",
            body: JSON.stringify({ password: pw }),
        });
        closeModal();
        toast("Password changed successfully");
        loadUserlists();
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Deletes a user entry from a userlist after confirmation. */
export async function deleteEntry(userlistId: number, entryId: number): Promise<void> {
    await crudDelete(`/api/userlists/${userlistId}/entries/${entryId}`, "Delete this user entry?", loadUserlists);
}

/** Saves a new or updated userlist name. */
export async function saveUserlist(id: number | null): Promise<void> {
    const name = (document.getElementById("m-name") as HTMLInputElement).value.trim();
    if (!name) {
        toast("Name is required", "error");
        return;
    }
    const body = { name };
    try {
        if (id) await api(`/api/userlists/${id}`, { method: "PUT", body: JSON.stringify(body) });
        else await api("/api/userlists", { method: "POST", body: JSON.stringify(body) });
        closeModal();
        toast(id ? "Auth list updated" : "Auth list created");
        loadUserlists();
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Deletes a userlist and all its entries after confirmation. */
export async function deleteUserlist(id: number): Promise<void> {
    await crudDelete(`/api/userlists/${id}`, "Delete this auth list and all its entries?", loadUserlists);
}
