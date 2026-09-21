// js/attempts.js

async function startQuiz(quizId) {
  try {
    const attempt = await apiRequest('/attempts/start', {
      method: 'POST',
      body: JSON.stringify({ quiz_id: quizId }),
    });
    currentAttempt = attempt;

    const quizDetails = await apiRequest(`/quizzes/${quizId}/take`);

    document.getElementById('runnerQuizTitle').textContent = quizDetails.title;
    const container = document.getElementById('questionsContainer');
    container.innerHTML = quizDetails.questions
      .map(
        (q, idx) => `
      <div class="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3">
        <p class="font-semibold text-sm">${idx + 1}. ${q.prompt} <span class="text-xs text-slate-400 font-normal">(${q.points} pt)</span></p>
        <div class="space-y-2">
          ${q.options
            .map(
              (opt) => `
            <label class="flex items-center space-x-3 p-2 rounded hover:bg-white cursor-pointer transition border border-transparent hover:border-slate-200 text-sm">
              <input type="radio" name="question_${q.id}" value="${opt.id}" required class="text-indigo-600">
              <span>${opt.text}</span>
            </label>
          `
            )
            .join('')}
        </div>
      </div>
    `
      )
      .join('');

    document.getElementById('viewDashboard').classList.add('hidden');
    document.getElementById('viewTestRunner').classList.remove('hidden');

    startCountdown(new Date(attempt.expires_at).getTime());
  } catch (err) {
    showAlert(err.message, true);
  }
}

function startCountdown(expirationMs) {
  clearInterval(timerInterval);
  const timerEl = document.getElementById('countdownTimer');

  timerInterval = setInterval(() => {
    const remaining = expirationMs - new Date().getTime();
    if (remaining <= 0) {
      clearInterval(timerInterval);
      timerEl.textContent = 'EXPIRED';
      alert('Time limit reached! Submitting your assessment.');
      document.getElementById('formTestSession').requestSubmit();
      return;
    }
    const m = Math.floor(remaining / 60000);
    const s = Math.floor((remaining % 60000) / 1000);
    timerEl.textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }, 1000);
}

async function handleAttemptSubmit(e) {
  e.preventDefault();
  clearInterval(timerInterval);

  const formData = new FormData(e.target);
  const answers = [];
  for (const [key, value] of formData.entries()) {
    if (key.startsWith('question_')) {
      answers.push({ question_id: key.replace('question_', ''), selected_option_id: value });
    }
  }

  try {
    const result = await apiRequest(`/attempts/${currentAttempt.attempt_id}/submit`, {
      method: 'POST',
      body: JSON.stringify({ answers }),
    });
    displayResult(result);
  } catch (err) {
    showAlert(err.message, true);
  }
}

function displayResult(result) {
  document.getElementById('viewDashboard').classList.add('hidden');
  document.getElementById('viewTestRunner').classList.add('hidden');
  document.getElementById('viewResults').classList.remove('hidden');

  const badge = document.getElementById('resultStatusBadge');
  badge.className = `inline-block px-4 py-1.5 rounded-full text-sm font-bold uppercase tracking-wider ${
    result.passed ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
  }`;
  badge.textContent = result.passed ? 'Passed' : 'Failed';

  document.getElementById('resultScore').textContent = `${result.score}%`;
  document.getElementById('resultPointTally').textContent = `Earned ${result.earned_points} / ${result.total_points} total points`;

  const container = document.getElementById('resultBreakdown');
  container.innerHTML = result.breakdown
    .map(
      (item) => `
    <div class="p-4 rounded-lg border ${
      item.is_correct ? 'border-emerald-200 bg-emerald-50/50' : 'border-rose-200 bg-rose-50/50'
    } space-y-2">
      <p class="text-sm font-bold">${item.prompt}</p>
      <div class="text-xs space-y-1">
        <p><span class="font-semibold">Your Pick:</span> ${item.selected_option_text || item.selected_option_id || '<span class="text-slate-400 italic">No answer provided</span>'}</p>
        ${!item.is_correct ? `<p class="text-emerald-700 font-semibold"><span class="font-semibold">Correct Answer:</span> ${item.correct_option_text || item.correct_option_id}</p>` : ''}
        ${item.explanation ? `<p class="text-slate-500 italic mt-1">Note: ${item.explanation}</p>` : ''}
      </div>
    </div>
  `
    )
    .join('');
}

function returnToDashboard() {
  document.getElementById('viewResults').classList.add('hidden');
  document.getElementById('viewDashboard').classList.remove('hidden');
  if (currentUser.role === 'student') loadStudentMetrics();
  loadCatalog();
}