/*
API
===

Handles all HTTP requests, authentication headers, and toast
notifications for user feedback throughout the application.
*/

/* Base API path prefix (empty = same origin) */
const API = '';

/* JWT token persisted in localStorage */
let TOKEN = localStorage.getItem('pm_token') || null;

/* Builds the standard request headers with optional JSON content-type */
function headers(json = true) {
    const h = {};
    if (TOKEN) h['Authorization'] = `Bearer ${TOKEN}`;
    if (json) h['Content-Type'] = 'application/json';
    return h;
}

/* Performs an authenticated API request and handles 401 auto-logout */
async function api(path, opts = {}) {
    const res = await fetch(API + path, { headers: headers(opts.json !== false), ...opts });
    if (res.status === 401) { logout(); throw new Error('Unauthorized'); }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
    return data;
}

/* Shows a temporary toast notification at the bottom of the screen */
function toast(msg, type = 'success') {
    const c = document.getElementById('toast-container');
    const t = document.createElement('div');
    t.className = `toast toast-${type}`;
    t.textContent = msg;
    c.appendChild(t);
    setTimeout(() => { t.classList.add('fade-out'); setTimeout(() => t.remove(), 350); }, 3500);
}
