/**
 * Users Management
 * ================
 *
 * List, add, and remove application users.
 * Only authenticated users can access this section.
 */

import { api, toast } from "../core/api";
import { openModal, closeModal, confirmPopup } from "../core/ui";
import { escHtml } from "../core/utils";
import { state } from "../state";
import type { UserProfile } from "../types";

/** Cached user list for filtering. */
let _users: UserProfile[] = [];

/** Loads and renders the user list. */
export async function loadUsers(): Promise<void> {
    try {
        _users = await api<UserProfile[]>("/auth/users");
    } catch {
        _users = [];
    }
    renderUsers();
}

/** Filters the user grid by search text. */
export function filterUsers(): void {
    const q = (document.getElementById("users-search") as HTMLInputElement)?.value.toLowerCase() ?? "";
    const cards = document.querySelectorAll<HTMLElement>("#users-grid .user-card");
    let visible = 0;
    cards.forEach((c) => {
        const match = !q || (c.dataset.userName || "").toLowerCase().includes(q) || (c.dataset.userEmail || "").toLowerCase().includes(q);
        c.style.display = match ? "" : "none";
        if (match) visible++;
    });
    const empty = document.getElementById("users-empty");
    if (empty) empty.style.display = visible === 0 ? "flex" : "none";
}

/** Renders user cards into the grid. */
function renderUsers(): void {
    const grid = document.getElementById("users-grid");
    const empty = document.getElementById("users-empty");
    if (!grid) return;

    if (_users.length === 0) {
        grid.innerHTML = "";
        if (empty) empty.style.display = "flex";
        return;
    }
    if (empty) empty.style.display = "none";

    const currentId = state.currentUser?.id;
    grid.innerHTML = _users
        .map((u) => {
            const initials = (u.name || u.email.split("@")[0])
                .split(" ")
                .map((w) => w[0])
                .join("")
                .toUpperCase()
                .slice(0, 2);
            const isMe = u.id === currentId;
            const created = u.created_at
                ? new Date(u.created_at).toLocaleDateString("en-US", {
                    year: "numeric",
                    month: "short",
                    day: "numeric",
                })
                : "Unknown";
            return `<div class="user-card" data-user-name="${escHtml(u.name)}" data-user-email="${escHtml(u.email)}">
                <div class="user-card-avatar">${initials}</div>
                <div class="user-card-info">
                    <div class="user-card-name">${escHtml(u.name)}${isMe ? ' <span class="user-badge-you">You</span>' : ""}</div>
                    <div class="user-card-email">${escHtml(u.email)}</div>
                    <div class="user-card-meta">Joined ${created}</div>
                </div>
                <div class="user-card-actions">
                    ${isMe ? "" : `<button class="btn-icon" title="Change password" onclick="openUserPasswordModal(${u.id}, '${escHtml(u.name)}')"><svg width="14" height="14" stroke-width="2"><use href="#i-key"/></svg></button><button class="btn-icon danger" title="Remove user" onclick="deleteUserById(${u.id})"><svg width="14" height="14" stroke-width="2"><use href="#i-trash"/></svg></button>`}
                </div>
            </div>`;
        })
        .join("");
}

/** Opens the modal to add a new user. */
export function openAddUserModal(): void {
    const html = `
    <h3>Add New User</h3>
    <p class="modal-subtitle">Create a new account. The user will be able to log in with their email and password.</p>
    <form onsubmit="saveNewUser(event)">
      <div class="form-row"><div class="form-group">
        <label>Name <span class="required">*</span></label>
        <input id="nu-name" required placeholder="Full name" autofocus>
      </div><div class="form-group">
        <label>Email <span class="required">*</span></label>
        <input type="email" id="nu-email" required placeholder="user@example.com">
      </div></div>
      <div class="form-row"><div class="form-group">
        <label>Password <span class="required">*</span></label>
        <input type="password" id="nu-password" required minlength="6" placeholder="Min 6 characters">
      </div><div class="form-group">
        <label>Confirm Password <span class="required">*</span></label>
        <input type="password" id="nu-password-confirm" required minlength="6" placeholder="Re-enter password">
      </div></div>
      <div class="modal-actions">
        <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn">Create User</button>
      </div>
    </form>`;
    openModal(html);
    setTimeout(() => (document.getElementById("nu-name") as HTMLInputElement)?.focus(), 100);
}

/** Saves a new user via the register endpoint (authenticated). */
export async function saveNewUser(e: Event): Promise<void> {
    e.preventDefault();
    const name = (document.getElementById("nu-name") as HTMLInputElement).value.trim();
    const email = (document.getElementById("nu-email") as HTMLInputElement).value.trim();
    const password = (document.getElementById("nu-password") as HTMLInputElement).value;
    const passwordConfirm = (document.getElementById("nu-password-confirm") as HTMLInputElement).value;

    if (!name || !email || !password || !passwordConfirm) {
        toast("All fields are required", "error");
        return;
    }

    if (password !== passwordConfirm) {
        toast("Passwords do not match", "error");
        return;
    }

    try {
        await api("/auth/register", {
            method: "POST",
            body: JSON.stringify({ name, email, password }),
        });
        toast("User created successfully");
        closeModal();
        loadUsers();
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Deletes a user by ID after confirmation. */
export async function deleteUserById(userId: number): Promise<void> {
    if (!(await confirmPopup("Remove this user? They will no longer be able to log in.", "Remove User"))) return;

    try {
        await api(`/auth/users/${userId}`, { method: "DELETE" });
        toast("User removed");
        loadUsers();
    } catch (err: any) {
        toast(err.message, "error");
    }
}

/** Opens a modal to reset another user's password. */
export function openUserPasswordModal(userId: number, userName: string): void {
    const html = `
    <h3>Change Password</h3>
    <p class="modal-subtitle">Set a new password for <strong>${escHtml(userName)}</strong>.</p>
    <form onsubmit="saveUserPassword(event, ${userId})">
      <div class="form-row"><div class="form-group">
        <label>New Password <span class="required">*</span></label>
        <input type="password" id="cp-password" required minlength="6" placeholder="Min 6 characters" autofocus>
      </div><div class="form-group">
        <label>Confirm Password <span class="required">*</span></label>
        <input type="password" id="cp-password-confirm" required minlength="6" placeholder="Re-enter password">
      </div></div>
      <div class="modal-actions">
        <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn">
          <svg width="14" height="14" stroke-width="2"><use href="#i-key"/></svg>
          Update Password
        </button>
      </div>
    </form>`;
    openModal(html);
    setTimeout(() => (document.getElementById("cp-password") as HTMLInputElement)?.focus(), 100);
}

/** Resets another user's password via the admin endpoint. */
export async function saveUserPassword(e: Event, userId: number): Promise<void> {
    e.preventDefault();
    const pw = (document.getElementById("cp-password") as HTMLInputElement).value;
    const pwConfirm = (document.getElementById("cp-password-confirm") as HTMLInputElement).value;

    if (!pw || !pwConfirm) {
        toast("Both fields are required", "error");
        return;
    }
    if (pw !== pwConfirm) {
        toast("Passwords do not match", "error");
        return;
    }

    try {
        await api(`/auth/users/${userId}/password`, {
            method: "PATCH",
            body: JSON.stringify({ new_password: pw }),
        });
        toast("Password updated");
        closeModal();
    } catch (err: any) {
        toast(err.message, "error");
    }
}
