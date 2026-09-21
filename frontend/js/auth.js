// js/auth.js

// Bootstrap application on page load
document.addEventListener('DOMContentLoaded', async () => {
  const token = localStorage.getItem('access_token');
  if (token) {
    await verifyAndLoadUser();
  } else {
    renderAuthNav();
  }
});

function renderAuthNav() {
  const nav = document.getElementById('authNav');
  if (!currentUser) {
    nav.innerHTML = `<span class="text-xs text-indigo-200">Not Authenticated</span>`;
  } else {
    nav.innerHTML = `
      <div class="text-right">
        <span class="block text-sm font-semibold">${currentUser.full_name}</span>
        <span class="block text-[10px] uppercase font-bold tracking-widest text-indigo-200">${currentUser.role}</span>
      </div>
      <button onclick="handleLogout()" class="bg-indigo-700 hover:bg-indigo-800 text-xs px-3 py-1.5 rounded transition">Logout</button>
    `;
  }
}

function switchAuthTab(tab) {
  document.getElementById('formLogin').classList.toggle('hidden', tab !== 'login');
  document.getElementById('formRegister').classList.toggle('hidden', tab !== 'register');
  document.getElementById('tabLogin').className =
    tab === 'login'
      ? 'flex-1 pb-3 text-center font-semibold border-b-2 border-indigo-600 text-indigo-600'
      : 'flex-1 pb-3 text-center font-medium text-slate-500';
  document.getElementById('tabRegister').className =
    tab === 'register'
      ? 'flex-1 pb-3 text-center font-semibold border-b-2 border-indigo-600 text-indigo-600'
      : 'flex-1 pb-3 text-center font-medium text-slate-500';
}

async function handleLogin(e) {
  e.preventDefault();
  try {
    const payload = {
      email: document.getElementById('loginEmail').value,
      password: document.getElementById('loginPassword').value,
    };
    const data = await apiRequest('/auth/login', { method: 'POST', body: JSON.stringify(payload) });
    localStorage.setItem('access_token', data.access_token);
    await verifyAndLoadUser();
  } catch (err) {
    showAlert(err.message, true);
  }
}

async function handleRegister(e) {
  e.preventDefault();
  try {
    const payload = {
      full_name: document.getElementById('regName').value,
      email: document.getElementById('regEmail').value,
      password: document.getElementById('regPassword').value,
      role: document.getElementById('regRole').value,
    };
    await apiRequest('/auth/register', { method: 'POST', body: JSON.stringify(payload) });
    showAlert('Registration successful! Please log in.');
    switchAuthTab('login');
  } catch (err) {
    showAlert(err.message, true);
  }
}

async function verifyAndLoadUser() {
  try {
    currentUser = await apiRequest('/auth/me');
    renderAuthNav();
    document.getElementById('viewAuth').classList.add('hidden');
    document.getElementById('viewDashboard').classList.remove('hidden');

    if (currentUser.role === 'instructor' || currentUser.role === 'admin') {
      document.getElementById('btnOpenCreator').classList.remove('hidden');
      document.getElementById("pastAttemptsBtn").classList.add('hidden');
    } else {
      loadStudentMetrics();
    }
    loadCatalog();
  } catch (err) {
    handleLogout();
  }
}

function handleLogout() {
  localStorage.removeItem('access_token');
  currentUser = null;
  if (typeof timerInterval !== 'undefined') clearInterval(timerInterval);
  renderAuthNav();
  document.getElementById('viewAuth').classList.remove('hidden');
  document.getElementById('viewDashboard').classList.add('hidden');
  document.getElementById('viewTestRunner').classList.add('hidden');
  document.getElementById('viewResults').classList.add('hidden');
}