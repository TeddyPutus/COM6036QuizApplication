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

// Add to frontend/js/history.js

async function viewQuizAnalytics(quizId, quizTitle) {
  try {
    document.getElementById('analyticsModalTitle').textContent = `${quizTitle} - Analytics`;

    // Fetch metrics and attempt lists in parallel
    const [metrics, attempts] = await Promise.all([
      apiRequest(`/attempts/quiz/${quizId}/metrics`),
      apiRequest(`/attempts/quiz/${quizId}`),
    ]);

    // Render KPI Cards
    const metricsContainer = document.getElementById('instructorMetricsCards');
    metricsContainer.innerHTML = `
      <div class="bg-slate-50 p-3 rounded-lg border border-slate-200 text-center">
        <span class="block text-[10px] font-bold uppercase text-slate-400">Attempts</span>
        <span class="text-xl font-black text-slate-800">${metrics.total_attempts}</span>
      </div>
      <div class="bg-slate-50 p-3 rounded-lg border border-slate-200 text-center">
        <span class="block text-[10px] font-bold uppercase text-slate-400">Average</span>
        <span class="text-xl font-black text-indigo-600">${metrics.average_score}%</span>
      </div>
      <div class="bg-slate-50 p-3 rounded-lg border border-slate-200 text-center">
        <span class="block text-[10px] font-bold uppercase text-slate-400">Pass Rate</span>
        <span class="text-xl font-black text-emerald-600">${metrics.pass_rate_percentage}%</span>
      </div>
      <div class="bg-slate-50 p-3 rounded-lg border border-slate-200 text-center">
        <span class="block text-[10px] font-bold uppercase text-slate-400">High Score</span>
        <span class="text-xl font-black text-emerald-700">${metrics.highest_score}%</span>
      </div>
      <div class="bg-slate-50 p-3 rounded-lg border border-slate-200 text-center">
        <span class="block text-[10px] font-bold uppercase text-slate-400">Low Score</span>
        <span class="text-xl font-black text-rose-600">${metrics.lowest_score}%</span>
      </div>
    `;

    // Render Student Attempt Table Rows
    const tableBody = document.getElementById('instructorAttemptsTableBody');
    if (attempts.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="6" class="px-4 py-6 text-center text-slate-400">No attempts have been submitted for this quiz yet.</td></tr>`;
    } else {
      tableBody.innerHTML = attempts
        .map(
          (a) => `
          <tr class="hover:bg-slate-50">
            <td class="px-4 py-3">
              <span class="font-bold text-slate-800">${a.user_name}</span>
              <span class="block text-[10px] text-slate-400">${a.user_email}</span>
            </td>
            <td class="px-4 py-3 font-semibold text-slate-800">${a.score}%</td>
            <td class="px-4 py-3 text-slate-500">${a.earned_points} / ${a.total_points}</td>
            <td class="px-4 py-3">
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                a.passed ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
              }">
                ${a.passed ? 'Passed' : 'Failed'}
              </span>
            </td>
            <td class="px-4 py-3 text-slate-400">${new Date(a.completed_at).toLocaleString()}</td>
            <td class="px-4 py-3 text-right">
              <button onclick="inspectStudentAttempt('${a.attempt_id}')" class="text-indigo-600 hover:text-indigo-900 font-semibold">
                Inspect Breakdown
              </button>
            </td>
          </tr>
        `
        )
        .join('');
    }

    document.getElementById('modalInstructorAnalytics').classList.remove('hidden');
  } catch (err) {
    showAlert(err.message, true);
  }
}

function closeQuizAnalyticsModal() {
  document.getElementById('modalInstructorAnalytics').classList.add('hidden');
}

async function inspectStudentAttempt(attemptId) {
  try {
    const result = await apiRequest(`/attempts/${attemptId}`);
    closeQuizAnalyticsModal();
    displayResult(result);
  } catch (err) {
    showAlert(err.message, true);
  }
}