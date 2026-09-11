// js/history.js

async function loadStudentMetrics() {
  try {
    const m = await apiRequest('/attempts/metrics');
    const container = document.getElementById('metricsPanel');
    container.innerHTML = `
      <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm"><span class="block text-xs font-bold uppercase text-slate-400">Total Attempts</span><span class="text-2xl font-black">${m.total_attempts}</span></div>
      <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm"><span class="block text-xs font-bold uppercase text-slate-400">Passed</span><span class="text-2xl font-black text-emerald-600">${m.passed_attempts}</span></div>
      <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm"><span class="block text-xs font-bold uppercase text-slate-400">Avg Score</span><span class="text-2xl font-black text-indigo-600">${m.average_score}%</span></div>
      <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm"><span class="block text-xs font-bold uppercase text-slate-400">Success Rate</span><span class="text-2xl font-black">${m.pass_rate_percentage}%</span></div>
    `;
  } catch (err) {
    /* Instructors or students without attempts omit this view */
  }
}

async function loadHistory() {
  try {
    const history = await apiRequest('/attempts/history');
    const container = document.getElementById('historyList');
    const section = document.getElementById('historySection');
    section.classList.remove('hidden');

    if (history.length === 0) {
      container.innerHTML = `<p class="text-sm text-slate-500 py-4">No completed assessments recorded.</p>`;
      return;
    }

    container.innerHTML = history
      .map(
        (h) => `
      <div class="py-3 flex justify-between items-center text-sm">
        <div>
          <p class="font-bold">Quiz ID: ${h.quiz_id.substring(0, 8)}...</p>
          <p class="text-xs text-slate-400">${new Date(h.completed_at).toLocaleString()}</p>
        </div>
        <div class="text-right">
          <span class="font-bold ${h.passed ? 'text-emerald-600' : 'text-rose-600'}">${h.score}%</span>
          <span class="block text-[11px] text-slate-400">${h.earned_points}/${h.total_points} pts</span>
        </div>
      </div>
    `
      )
      .join('');
  } catch (err) {
    showAlert(err.message, true);
  }
}