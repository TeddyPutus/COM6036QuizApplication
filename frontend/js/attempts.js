let currentQuestions = [];
let currentQuestionIndex = 0;
let attemptSessionKey = '';

async function startQuiz(quizId) {
  try {
    const attempt = await apiRequest('/attempts/start', {
      method: 'POST',
      body: JSON.stringify({ quiz_id: quizId }),
    });
    currentAttempt = attempt;
    attemptSessionKey = `quiz_${quizId}`;

    const quizDetails = await apiRequest(`/quizzes/${quizId}/take`);
    currentQuestions = quizDetails.questions;
    currentQuestionIndex = 0;

    document.getElementById('runnerQuizTitle').textContent = quizDetails.title;
    
    renderQuestionGrid();
    renderCurrentQuestion();

    document.getElementById('viewDashboard').classList.add('hidden');
    document.getElementById('viewTestRunner').classList.remove('hidden');

    startCountdown(new Date(attempt.expires_at).getTime());
  } catch (err) {
    showAlert(err.message, true);
  }
}

function saveAnswer(questionId, optionId) {
  const saved = JSON.parse(sessionStorage.getItem(attemptSessionKey)) || {};
  saved[`question_${questionId}`] = optionId;
  sessionStorage.setItem(attemptSessionKey, JSON.stringify(saved));
  renderQuestionGrid();
}

function renderCurrentQuestion() {
  const q = currentQuestions[currentQuestionIndex];
  const saved = JSON.parse(sessionStorage.getItem(attemptSessionKey)) || {};
  const selectedOptionId = saved[`question_${q.id}`];

  const container = document.getElementById('questionsContainer');
  container.innerHTML = `
    <div class="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3">
      <p class="font-semibold text-sm text-slate-500">Question ${currentQuestionIndex + 1} of ${currentQuestions.length}</p>
      <p class="font-semibold text-lg">${q.prompt} <span class="text-xs text-slate-400 font-normal">(${q.points} pt)</span></p>
      <div class="space-y-2 mt-4">
        ${q.options
          .map(
            (opt) => `
          <label class="flex items-center space-x-3 p-3 rounded hover:bg-white cursor-pointer transition border border-transparent hover:border-slate-200 text-sm">
            <input type="radio" name="question_${q.id}" value="${opt.id}" class="text-indigo-600" onchange="saveAnswer('${q.id}', '${opt.id}')" ${selectedOptionId === opt.id ? 'checked' : ''}>
            <span>${opt.text}</span>
          </label>
        `
          )
          .join('')}
      </div>
    </div>
    <div class="flex justify-between mt-4">
      <button type="button" class="bg-slate-200 hover:bg-slate-300 px-4 py-2 rounded text-sm font-semibold transition disabled:opacity-50" onclick="navigateQuestion(-1)" ${currentQuestionIndex === 0 ? 'disabled' : ''}>Previous</button>
      <button type="button" class="bg-slate-200 hover:bg-slate-300 px-4 py-2 rounded text-sm font-semibold transition disabled:opacity-50" onclick="navigateQuestion(1)" ${currentQuestionIndex === currentQuestions.length - 1 ? 'disabled' : ''}>Next</button>
    </div>
  `;
}

function navigateQuestion(direction) {
  currentQuestionIndex += direction;
  renderCurrentQuestion();
  renderQuestionGrid();
}

function renderQuestionGrid() {
  let gridEl = document.getElementById('questionGrid');
  if (!gridEl) {
    gridEl = document.createElement('div');
    gridEl.id = 'questionGrid';
    gridEl.className = 'flex flex-wrap gap-2 mb-6';
    const container = document.getElementById('questionsContainer');
    container.parentNode.insertBefore(gridEl, container);
  }
  
  const saved = JSON.parse(sessionStorage.getItem(attemptSessionKey)) || {};
  
  gridEl.innerHTML = currentQuestions.map((q, idx) => {
    const isAnswered = !!saved[`question_${q.id}`];
    const isCurrent = idx === currentQuestionIndex;
    let btnClass = 'px-3 py-1 rounded text-sm font-semibold border transition ';
    if (isCurrent) {
      btnClass += 'border-indigo-600 bg-indigo-100 text-indigo-700';
    } else if (isAnswered) {
      btnClass += 'border-emerald-500 bg-emerald-50 text-emerald-700';
    } else {
      btnClass += 'border-slate-300 bg-white text-slate-500 hover:bg-slate-50';
    }
    
    return `<button type="button" class="${btnClass}" onclick="currentQuestionIndex = ${idx}; renderCurrentQuestion(); renderQuestionGrid();">${idx + 1}</button>`;
  }).join('');
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
      submitAttemptDirectly();
      return;
    }
    const m = Math.floor(remaining / 60000);
    const s = Math.floor((remaining % 60000) / 1000);
    timerEl.textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }, 1000);
}

async function submitAttemptDirectly() {
  clearInterval(timerInterval);
  const saved = JSON.parse(sessionStorage.getItem(attemptSessionKey)) || {};
  
  const answers = [];
  currentQuestions.forEach((q) => {
    if (saved[`question_${q.id}`]) {
      answers.push({ question_id: q.id, selected_option_id: saved[`question_${q.id}`] });
    }
  });

  try {
    const result = await apiRequest(`/attempts/${currentAttempt.attempt_id}/submit`, {
      method: 'POST',
      body: JSON.stringify({ answers }),
    });
    sessionStorage.removeItem(attemptSessionKey);
    displayResult(result);
  } catch (err) {
    showAlert(err.message, true);
  }
}

async function handleAttemptSubmit(e) {
  e.preventDefault();
  await submitAttemptDirectly();
}

function displayResult(result) {
  document.getElementById('viewDashboard').classList.add('hidden');
  document.getElementById('viewTestRunner').classList.add('hidden');
  document.getElementById('viewResults').classList.remove('hidden');

  const gridEl = document.getElementById('questionGrid');
  if (gridEl) gridEl.remove();

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