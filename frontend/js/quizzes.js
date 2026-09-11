// js/quizzes.js

async function loadCatalog() {
  try {
    const quizzes = await apiRequest('/quizzes');
    const container = document.getElementById('quizList');

    if (quizzes.length === 0) {
      container.innerHTML = `<div class="col-span-3 text-center py-12 text-slate-400">No quizzes available at the moment.</div>`;
      return;
    }

    container.innerHTML = quizzes
      .map(
        (q) => `
      <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between space-y-4">
        <div>
          <div class="flex justify-between items-start">
            <span class="text-[11px] font-bold tracking-wider uppercase px-2 py-0.5 rounded bg-slate-100 text-slate-700">${q.subject}</span>
            <span class="text-xs text-slate-500">${q.time_limit_minutes} mins</span>
          </div>
          <h3 class="text-lg font-bold mt-2">${q.title}</h3>
          <p class="text-xs text-slate-600 mt-1 line-clamp-2">${q.description || 'No description provided.'}</p>
        </div>
        <div class="border-t pt-3 flex items-center justify-between">
          <span class="text-xs font-semibold text-slate-500">${q.total_questions} Questions</span>
          <div class="space-x-2">
            ${
              currentUser.role === 'student'
                ? `<button onclick="startQuiz('${q.id}')" class="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold px-3 py-1.5 rounded transition">Start Test</button>`
                : `<button onclick="deleteQuiz('${q.id}')" class="text-rose-600 hover:text-rose-800 text-xs font-bold px-2 py-1">Delete</button>`
            }
          </div>
        </div>
      </div>
    `
      )
      .join('');
  } catch (err) {
    showAlert(err.message, true);
  }
}

function showQuizCreatorModal() {
  document.getElementById('questionsBuilder').innerHTML = '';
  addQuestionField();
  document.getElementById('modalCreator').classList.remove('hidden');
}

function closeQuizCreatorModal() {
  document.getElementById('modalCreator').classList.add('hidden');
}

function addQuestionField() {
  const builder = document.getElementById('questionsBuilder');
  const idx = builder.children.length;
  const card = document.createElement('div');
  card.className = 'p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-2';
  card.innerHTML = `
    <div class="flex justify-between items-center">
      <span class="text-xs font-bold uppercase text-slate-500">Question ${idx + 1}</span>
      ${idx > 0 ? `<button type="button" onclick="this.parentElement.parentElement.remove()" class="text-xs text-rose-600 font-semibold">Remove</button>` : ''}
    </div>
    <input type="text" placeholder="Question prompt..." class="q-prompt w-full px-2 py-1 text-sm border rounded" required>
    <div class="grid grid-cols-2 gap-2 text-xs">
      <input type="number" placeholder="Points" value="1" min="1" class="q-points px-2 py-1 border rounded" required>
      <input type="text" placeholder="Optional explanation..." class="q-exp px-2 py-1 border rounded">
    </div>
    <div class="space-y-1 pt-1">
      <span class="text-[11px] font-semibold text-slate-600">Options (Select the correct answer):</span>
      ${[0, 1, 2, 3]
        .map(
          (optIdx) => `
        <div class="flex items-center space-x-2">
          <input type="radio" name="correct_${idx}" value="${optIdx}" ${optIdx === 0 ? 'checked' : ''}>
          <input type="text" placeholder="Option ${optIdx + 1}" class="q-opt-${optIdx} flex-1 px-2 py-1 text-xs border rounded" required>
        </div>
      `
        )
        .join('')}
    </div>
  `;
  builder.appendChild(card);
}

async function handleCreateQuiz(e) {
  e.preventDefault();
  const qCards = document.querySelectorAll('#questionsBuilder > div');
  const questions = [];

  qCards.forEach((card, idx) => {
    const correctRadio = card.querySelector(`input[name="correct_${idx}"]:checked`).value;
    const options = [0, 1, 2, 3].map((optIdx) => ({
      text: card.querySelector(`.q-opt-${optIdx}`).value,
      is_correct: parseInt(correctRadio) === optIdx,
    }));

    questions.push({
      prompt: card.querySelector('.q-prompt').value,
      points: parseInt(card.querySelector('.q-points').value),
      explanation: card.querySelector('.q-exp').value || null,
      options,
    });
  });

  const payload = {
    title: document.getElementById('qTitle').value,
    subject: document.getElementById('qSubject').value,
    description: document.getElementById('qDesc').value || null,
    time_limit_minutes: parseInt(document.getElementById('qTime').value),
    passing_score_percentage: parseFloat(document.getElementById('qPassScore').value),
    questions,
  };

  try {
    await apiRequest('/quizzes', { method: 'POST', body: JSON.stringify(payload) });
    showAlert('Quiz published successfully!');
    closeQuizCreatorModal();
    loadCatalog();
  } catch (err) {
    showAlert(err.message, true);
  }
}

async function deleteQuiz(id) {
  if (!confirm('Are you sure you want to delete this quiz?')) return;
  try {
    await apiRequest(`/quizzes/${id}`, { method: 'DELETE' });
    showAlert('Quiz removed.');
    loadCatalog();
  } catch (err) {
    showAlert(err.message, true);
  }
}