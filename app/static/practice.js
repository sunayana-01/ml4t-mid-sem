// Drag-and-drop + click-to-classify True/False bucket logic for the practice page.
// Single source of truth: each .statement-card's data-status attribute
// ("unsorted" | "true" | "false"). Moving a card between DOM containers
// always goes through setStatus() so buttons, drag/drop, and reset stay in sync.

function moveCardsIntoTray() {
  const source = document.getElementById('statement-source');
  const tray = document.querySelector('#tray .card-slot');
  [...source.children].forEach(card => tray.appendChild(card));
}

// Wipe any "Check Answer" coloring/explanation off a single card, putting it
// back into its pre-check look. Used both on reset and whenever a card is
// moved again after a check, so stale green/red highlights can't linger.
function clearCheckStyle(card) {
  card.classList.remove('border-emerald-500', 'border-rose-500', 'border-amber-400',
                         'bg-emerald-50', 'bg-rose-50', 'bg-amber-50',
                         'dark:bg-emerald-950', 'dark:bg-rose-950', 'dark:bg-amber-950');
  card.classList.add('border-slate-200', 'dark:border-slate-600');
  card.querySelector('.explanation').classList.add('hidden');
  card.querySelector('.status-buttons').classList.remove('hidden');
}

function setStatus(card, status) {
  card.dataset.status = status;
  clearCheckStyle(card);
  document.getElementById('result-summary').textContent = '';
  const target = document.querySelector(`#${status === 'unsorted' ? 'tray' : 'bucket-' + status} .card-slot`);
  target.appendChild(card);
}

function initCards() {
  document.querySelectorAll('.statement-card').forEach(card => {
    card.dataset.status = 'unsorted';

    card.addEventListener('dragstart', (e) => {
      e.dataTransfer.setData('text/plain', card.dataset.letter);
      e.dataTransfer.effectAllowed = 'move';
      card.classList.add('opacity-50');
    });
    card.addEventListener('dragend', () => card.classList.remove('opacity-50'));

    card.querySelector('.btn-true').addEventListener('click', () => setStatus(card, 'true'));
    card.querySelector('.btn-false').addEventListener('click', () => setStatus(card, 'false'));
  });

  document.querySelectorAll('.bucket').forEach(bucket => {
    bucket.addEventListener('dragover', (e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; });
    bucket.addEventListener('dragenter', () => bucket.classList.add('ring-2', 'ring-indigo-400'));
    bucket.addEventListener('dragleave', () => bucket.classList.remove('ring-2', 'ring-indigo-400'));
    bucket.addEventListener('drop', (e) => {
      e.preventDefault();
      bucket.classList.remove('ring-2', 'ring-indigo-400');
      const letter = e.dataTransfer.getData('text/plain');
      const card = document.querySelector(`.statement-card[data-letter="${letter}"]`);
      if (card) setStatus(card, bucket.dataset.status);
    });
  });
}

function resetCards() {
  document.querySelectorAll('.statement-card').forEach(card => setStatus(card, 'unsorted'));
  document.getElementById('result-summary').textContent = '';
}

function checkAnswers() {
  const cards = document.querySelectorAll('.statement-card');
  let correctCount = 0;
  cards.forEach(card => {
    const userAnswer = card.dataset.status;          // 'true' | 'false' | 'unsorted'
    const correct = card.dataset.correct;             // 'true' | 'false'
    const isCorrect = userAnswer === correct;
    if (isCorrect) correctCount += 1;

    card.classList.remove('border-slate-200', 'dark:border-slate-600');
    if (userAnswer === 'unsorted') {
      card.classList.add('border-amber-400', 'bg-amber-50', 'dark:bg-amber-950');
    } else if (isCorrect) {
      card.classList.add('border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-950');
    } else {
      card.classList.add('border-rose-500', 'bg-rose-50', 'dark:bg-rose-950');
    }
    card.querySelector('.explanation').classList.remove('hidden');
    card.querySelector('.status-buttons').classList.add('hidden');
  });

  const summary = document.getElementById('result-summary');
  summary.textContent = `${correctCount} / ${cards.length} statements correct`;
  summary.className = 'text-sm font-semibold ' + (correctCount === cards.length ? 'text-emerald-600' : 'text-rose-600');
}

moveCardsIntoTray();
initCards();
