/**
 * Authentication
 * ==============
 *
 * Login, registration, logout flow, session management,
 * user profile display, sidebar toggle, and user settings modal.
 */

import { api, toast, TOKEN, setToken } from "./api";
import { openModal, closeModal } from "./ui";
import { loadOverview } from "../sections/overview";
import { escHtml } from "./utils";
import { state } from "../state";

/** Switches between the Login and Register tabs on the auth overlay. */
export function switchAuthTab(tab: string): void {
    document.querySelectorAll(".auth-tab").forEach((t, i) => {
        t.classList.toggle("active", tab === "login" ? i === 0 : i === 1);
    });
    document.getElementById("auth-login")?.classList.toggle("active", tab === "login");
    document.getElementById("auth-register")?.classList.toggle("active", tab === "register");
}

/** Handles the login form submission, stores JWT token on success. */
export async function handleLogin(e: Event): Promise<void> {
    e.preventDefault();
    try {
        const data = await api("/auth/login", {
            method: "POST",
            body: JSON.stringify({
                email: (document.getElementById("login-email") as HTMLInputElement).value,
                password: (document.getElementById("login-password") as HTMLInputElement).value,
            }),
        });
        setToken(data.access_token);
        localStorage.setItem("pm_token", TOKEN!);
        showApp();
        toast("Logged in successfully");
    } catch (err) {
        toast((err as Error).message, "error");
    }
}

/** Handles the registration form submission, switches to login tab on success. */
export async function handleRegister(e: Event): Promise<void> {
    e.preventDefault();
    try {
        await api("/auth/register", {
            method: "POST",
            body: JSON.stringify({
                name: (document.getElementById("register-name") as HTMLInputElement).value,
                email: (document.getElementById("register-email") as HTMLInputElement).value,
                password: (document.getElementById("register-password") as HTMLInputElement).value,
            }),
        });
        toast("Account created! You can now log in.");
        switchAuthTab("login");
    } catch (err) {
        toast((err as Error).message, "error");
    }
}

/** Clears the JWT token and returns to the auth overlay. */
export function logout(): void {
    setToken(null);
    localStorage.removeItem("pm_token");
    document.getElementById("auth-overlay")!.style.display = "flex";
    document.getElementById("app-layout")!.style.display = "none";
    document.getElementById("app-footer")!.style.display = "none";
    closeUserMenu();
}

/** Shows the main application layout and loads initial data. */
export function showApp(): void {
    document.getElementById("auth-overlay")!.style.display = "none";
    document.getElementById("app-layout")!.style.display = "flex";
    document.getElementById("app-footer")!.style.display = "block";
    restoreSidebarState();
    loadUserInfo();
    loadOverview();
}

/** Updates the UI elements (avatar, name, email) from the current user object. */
function _updateUserUI(): void {
    if (!state.currentUser) return;
    const displayName = state.currentUser.name || state.currentUser.email.split("@")[0];
    const initials = displayName
        .split(" ")
        .map((w) => w[0])
        .join("")
        .toUpperCase()
        .slice(0, 2);
    const userName = document.getElementById("user-name");
    const ddName = document.getElementById("dropdown-user-name");
    const ddEmail = document.getElementById("dropdown-user-email");
    const avatar = document.getElementById("user-avatar");
    if (userName) userName.textContent = displayName;
    if (ddName) ddName.textContent = displayName;
    if (ddEmail) ddEmail.textContent = state.currentUser.email;
    if (avatar) avatar.textContent = initials;
}

/** Fetches the logged-in user's profile and updates the UI (avatar, name, email). */
export async function loadUserInfo(): Promise<void> {
    try {
        state.currentUser = await api("/auth/me");
        _updateUserUI();
    } catch {
        /* silently fail - user info is cosmetic */
    }
}

/** Toggles the mobile sidebar open/closed. */
export function toggleSidebar(): void {
    document.getElementById("sidebar")?.classList.toggle("open");
    document.getElementById("sidebar-backdrop")?.classList.toggle("open");
}

/** Toggles the desktop sidebar between full and icon-only (collapsed) mode. */
export function toggleSidebarCollapse(): void {
    if (window.innerWidth <= 900) return;
    const sidebar = document.getElementById("sidebar");
    if (!sidebar) return;
    const collapsed = sidebar.classList.toggle("collapsed");
    const w = collapsed ? "56px" : "240px";
    document.documentElement.style.setProperty("--sidebar-w", w);
    const btn = document.getElementById("sidebar-collapse-btn");
    if (btn) {
        btn.title = collapsed ? "Expand sidebar" : "Collapse sidebar";
        const svg = btn.querySelector<SVGElement>("svg");
        if (svg) svg.style.transform = collapsed ? "rotate(180deg)" : "";
    }
    localStorage.setItem("pm_sidebar_collapsed", collapsed ? "1" : "0");
}

/** Restores sidebar collapsed state from localStorage (called on app load). */
export function restoreSidebarState(): void {
    if (window.innerWidth <= 900) return;
    if (localStorage.getItem("pm_sidebar_collapsed") === "1") {
        const sidebar = document.getElementById("sidebar");
        if (!sidebar) return;
        sidebar.classList.add("collapsed");
        document.documentElement.style.setProperty("--sidebar-w", "56px");
        const btn = document.getElementById("sidebar-collapse-btn");
        if (btn) {
            btn.title = "Expand sidebar";
            const svg = btn.querySelector<SVGElement>("svg");
            if (svg) svg.style.transform = "rotate(180deg)";
        }
    }
}

/** Initialize resize listener for responsive sidebar. */
export function initSidebarListeners(): void {
    window.addEventListener("resize", () => {
        if (window.innerWidth <= 900) {
            document.getElementById("sidebar")?.classList.remove("collapsed");
            document.documentElement.style.removeProperty("--sidebar-w");
        } else {
            restoreSidebarState();
        }
    });
}

/** Toggles the user dropdown menu open/closed. */
export function toggleUserMenu(e: Event): void {
    e.stopPropagation();
    const dd = document.getElementById("user-dropdown");
    const btn = document.getElementById("top-bar-user");
    const isOpen = dd?.classList.contains("open");
    dd?.classList.toggle("open", !isOpen);
    btn?.classList.toggle("open", !isOpen);
}

/** Closes the user dropdown menu. */
export function closeUserMenu(): void {
    document.getElementById("user-dropdown")?.classList.remove("open");
    document.getElementById("top-bar-user")?.classList.remove("open");
}

/** Initialize click-outside listener for user dropdown. */
export function initUserMenuListeners(): void {
    document.addEventListener("click", (e) => {
        const dd = document.getElementById("user-dropdown");
        if (dd && dd.classList.contains("open") && !(e.target as HTMLElement).closest(".top-bar-right")) {
            closeUserMenu();
        }
    });
}

/** Opens the user settings modal with name, email, and password change fields. */
export function openUserSettings(): void {
    closeUserMenu();
    if (!state.currentUser) return;
    const html = `
    <h3>User Settings</h3>
    <form onsubmit="saveUserSettings(event)">
      <div class="form-row">
        <div class="form-group">
          <label>Name</label>
          <input id="us-name" value="${escHtml(state.currentUser.name)}" placeholder="Your name">
        </div>
        <div class="form-group">
          <label>Email</label>
          <input type="email" id="us-email" value="${escHtml(state.currentUser.email)}" placeholder="Email address">
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Current Password</label>
          <input type="password" id="us-cur-pass" placeholder="Required to change password">
        </div>
        <div class="form-group">
          <label>New Password</label>
          <input type="password" id="us-new-pass" placeholder="Leave blank to keep current" minlength="6">
        </div>
      </div>
      <div class="modal-actions">
        <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn">Save Changes</button>
      </div>
    </form>
  `;
    openModal(html);
}

/** Saves the user settings (name, email, password) via PATCH to the profile endpoint. */
export async function saveUserSettings(e: Event): Promise<void> {
    e.preventDefault();
    const body: Record<string, string> = {};
    const name = (document.getElementById("us-name") as HTMLInputElement).value.trim();
    const email = (document.getElementById("us-email") as HTMLInputElement).value.trim();
    const curPass = (document.getElementById("us-cur-pass") as HTMLInputElement).value;
    const newPass = (document.getElementById("us-new-pass") as HTMLInputElement).value;
    if (name && name !== state.currentUser?.name) body.name = name;
    if (email && email !== state.currentUser?.email) body.email = email;
    if (newPass) {
        if (!curPass) {
            toast("Current password required to change password", "error");
            return;
        }
        body.current_password = curPass;
        body.new_password = newPass;
    }
    if (Object.keys(body).length === 0) {
        toast("No changes to save");
        closeModal();
        return;
    }
    try {
        state.currentUser = await api("/auth/profile", { method: "PATCH", body: JSON.stringify(body) });
        _updateUserUI();
        toast("Profile updated");
        closeModal();
    } catch (err) {
        toast((err as Error).message, "error");
    }
}
