/*
Authentication
==============

Login, registration, logout flow, session management,
user profile display, sidebar toggle, and user settings modal.
*/

/* Switches between the Login and Register tabs on the auth overlay */
function switchAuthTab(tab) {
    document.querySelectorAll('.auth-tab').forEach((t, i) => {
        t.classList.toggle('active', (tab === 'login' ? i === 0 : i === 1));
    });
    document.getElementById('auth-login').classList.toggle('active', tab === 'login');
    document.getElementById('auth-register').classList.toggle('active', tab === 'register');
}

/* Handles the login form submission, stores JWT token on success */
async function handleLogin(e) {
    e.preventDefault();
    try {
        const data = await api('/auth/login', {
            method: 'POST',
            body: JSON.stringify({
                email: document.getElementById('login-email').value,
                password: document.getElementById('login-password').value
            })
        });
        TOKEN = data.access_token;
        localStorage.setItem('pm_token', TOKEN);
        showApp();
        toast('Logged in successfully');
    } catch (err) { toast(err.message, 'error'); }
}

/* Handles the registration form submission, switches to login tab on success */
async function handleRegister(e) {
    e.preventDefault();
    try {
        await api('/auth/register', {
            method: 'POST',
            body: JSON.stringify({
                name: document.getElementById('register-name').value,
                email: document.getElementById('register-email').value,
                password: document.getElementById('register-password').value
            })
        });
        toast('Account created! You can now log in.');
        switchAuthTab('login');
    } catch (err) { toast(err.message, 'error'); }
}

/* Clears the JWT token and returns to the auth overlay */
function logout() {
    TOKEN = null;
    localStorage.removeItem('pm_token');
    document.getElementById('auth-overlay').style.display = 'flex';
    document.getElementById('app-layout').style.display = 'none';
    document.getElementById('app-footer').style.display = 'none';
    closeUserMenu();
}

/* Shows the main application layout and loads initial data */
function showApp() {
    document.getElementById('auth-overlay').style.display = 'none';
    document.getElementById('app-layout').style.display = 'flex';
    document.getElementById('app-footer').style.display = 'block';
    restoreSidebarState();
    loadUserInfo();
    loadOverview();
}

/* Cached current user object for profile updates */
let _currentUser = null;

/* Updates the UI elements (avatar, name, email) from the current user object */
function _updateUserUI() {
    const displayName = _currentUser.name || _currentUser.email.split('@')[0];
    const initials = displayName.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
    document.getElementById('user-name').textContent = displayName;
    document.getElementById('dropdown-user-name').textContent = displayName;
    document.getElementById('dropdown-user-email').textContent = _currentUser.email;
    document.getElementById('user-avatar').textContent = initials;
}

/* Fetches the logged-in user's profile and updates the UI (avatar, name, email) */
async function loadUserInfo() {
    try {
        _currentUser = await api('/auth/me');
        _updateUserUI();
    } catch { /* silently fail - user info is cosmetic */ }
}

/* Toggles the mobile sidebar open/closed */
function toggleSidebar() {
    document.getElementById('sidebar')?.classList.toggle('open');
    document.getElementById('sidebar-backdrop')?.classList.toggle('open');
}

/* Toggles the desktop sidebar between full and icon-only (collapsed) mode */
function toggleSidebarCollapse() {
    if (window.innerWidth <= 900) return;
    const sidebar = document.getElementById('sidebar');
    const collapsed = sidebar.classList.toggle('collapsed');
    const w = collapsed ? '56px' : '240px';
    document.documentElement.style.setProperty('--sidebar-w', w);
    const btn = document.getElementById('sidebar-collapse-btn');
    if (btn) {
        btn.title = collapsed ? 'Expand sidebar' : 'Collapse sidebar';
        const svg = btn.querySelector('svg');
        if (svg) svg.style.transform = collapsed ? 'rotate(180deg)' : '';
    }
    localStorage.setItem('pm_sidebar_collapsed', collapsed ? '1' : '0');
}

/* Restores sidebar collapsed state from localStorage (called on app load) */
function restoreSidebarState() {
    if (window.innerWidth <= 900) return;
    if (localStorage.getItem('pm_sidebar_collapsed') === '1') {
        const sidebar = document.getElementById('sidebar');
        sidebar.classList.add('collapsed');
        document.documentElement.style.setProperty('--sidebar-w', '56px');
        const btn = document.getElementById('sidebar-collapse-btn');
        if (btn) {
            btn.title = 'Expand sidebar';
            const svg = btn.querySelector('svg');
            if (svg) svg.style.transform = 'rotate(180deg)';
        }
    }
}

/* Reset collapsed state when resizing to mobile */
window.addEventListener('resize', () => {
    if (window.innerWidth <= 900) {
        document.getElementById('sidebar')?.classList.remove('collapsed');
        document.documentElement.style.removeProperty('--sidebar-w');
    } else {
        restoreSidebarState();
    }
});

/* Toggles the user dropdown menu open/closed */
function toggleUserMenu(e) {
    e.stopPropagation();
    const dd = document.getElementById('user-dropdown');
    const btn = document.getElementById('top-bar-user');
    const isOpen = dd.classList.contains('open');
    dd.classList.toggle('open', !isOpen);
    btn.classList.toggle('open', !isOpen);
}

/* Closes the user dropdown menu */
function closeUserMenu() {
    const dd = document.getElementById('user-dropdown');
    const btn = document.getElementById('top-bar-user');
    if (dd) dd.classList.remove('open');
    if (btn) btn.classList.remove('open');
}

/* Close user dropdown when clicking outside */
document.addEventListener('click', (e) => {
    const dd = document.getElementById('user-dropdown');
    if (dd && dd.classList.contains('open') && !e.target.closest('.top-bar-right')) {
        closeUserMenu();
    }
});

/* Opens the user settings modal with name, email, and password change fields */
function openUserSettings() {
    closeUserMenu();
    if (!_currentUser) return;
    const html = `
        <h3>User Settings</h3>
        <form onsubmit="saveUserSettings(event)">
            <div class="form-row">
                <div class="form-group">
                    <label>Name</label>
                    <input id="us-name" value="${escHtml(_currentUser.name)}" placeholder="Your name">
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" id="us-email" value="${escHtml(_currentUser.email)}" placeholder="Email address">
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

/* Saves the user settings (name, email, password) via PATCH to the profile endpoint */
async function saveUserSettings(e) {
    e.preventDefault();
    const body = {};
    const name = document.getElementById('us-name').value.trim();
    const email = document.getElementById('us-email').value.trim();
    const curPass = document.getElementById('us-cur-pass').value;
    const newPass = document.getElementById('us-new-pass').value;
    if (name && name !== _currentUser.name) body.name = name;
    if (email && email !== _currentUser.email) body.email = email;
    if (newPass) {
        if (!curPass) { toast('Current password required to change password', 'error'); return; }
        body.current_password = curPass;
        body.new_password = newPass;
    }
    if (Object.keys(body).length === 0) { toast('No changes to save'); closeModal(); return; }
    try {
        _currentUser = await api('/auth/profile', { method: 'PATCH', body: JSON.stringify(body) });
        _updateUserUI();
        toast('Profile updated');
        closeModal();
    } catch (err) { toast(err.message, 'error'); }
}
