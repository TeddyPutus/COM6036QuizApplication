// js/api.js
const API_BASE = '/api/v1';

// Shared application state
let currentUser = null;
let currentAttempt = null;
let timerInterval = null;

/**
 * Standard fetch wrapper that automatically appends JWT Bearer tokens
 * and intercepts 401 Unauthorized responses.
 */
async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem('access_token');
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });

  if (res.status === 401 && !endpoint.includes('/auth/login')) {
    handleLogout();
    throw new Error('Session expired. Please log in again.');
  }

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || 'An unexpected error occurred.');
  }

  return res.status === 204 ? null : res.json();
}

/**
 * Global notification banner.
 */
function showAlert(msg, isError = false) {
  const box = document.getElementById('alertBox');
  box.className = `p-4 rounded-lg text-sm font-medium ${
    isError ? 'bg-rose-100 text-rose-800' : 'bg-emerald-100 text-emerald-800'
  }`;
  box.textContent = msg;
  box.classList.remove('hidden');
  setTimeout(() => box.classList.add('hidden'), 5000);
}