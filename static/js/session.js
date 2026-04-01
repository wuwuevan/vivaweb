const root = document.getElementById('sessionApp');
if (root) {
  const qs = JSON.parse(root.dataset.questions || '[]');
  let idx = 0;
  let recording = false;
  let totalSeconds = 12 * 60;

  const questionText = document.getElementById('questionText');
  const hintBox = document.getElementById('hintBox');
  const answerInput = document.getElementById('answerInput');
  const feedbackBox = document.getElementById('feedbackBox');
  const progress = document.getElementById('sessionProgress');
  const timer = document.getElementById('timer');

  const tick = () => {
    totalSeconds = Math.max(0, totalSeconds - 1);
    const mm = String(Math.floor(totalSeconds / 60)).padStart(2, '0');
    const ss = String(totalSeconds % 60).padStart(2, '0');
    timer.textContent = `${mm}:${ss}`;
  };
  setInterval(tick, 1000);

  const render = () => {
    questionText.textContent = qs[idx]?.question || 'No question available';
    hintBox.textContent = 'Hints: ' + (qs[idx]?.keywords || []).join(', ');
    progress.style.width = `${((idx + 1) / qs.length) * 100}%`;
  };

  document.getElementById('hintBtn').onclick = () => hintBox.classList.toggle('d-none');
  document.getElementById('recordBtn').onclick = (e) => {
    recording = !recording;
    e.target.textContent = recording ? 'Stop Recording' : 'Start Recording';
    e.target.classList.toggle('btn-danger', recording);
  };

  document.getElementById('submitAnswer').onclick = async () => {
    const res = await fetch('/api/session/answer', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question_index: idx, answer: answerInput.value })
    });
    const data = await res.json();
    if (data.ok) {
      const f = data.feedback;
      document.getElementById('liveScore').textContent = f.overall_score + '%';
      document.getElementById('confidenceScore').textContent = f.confidence + '%';
      document.getElementById('coachTip').textContent = f.coach_tip;
      feedbackBox.innerHTML = `
        <div class="card border-info border-1">
          <div class="card-body">
            <h6 class="mb-2">Mock AI Grading</h6>
            <div class="small mb-2">Overall <strong>${f.overall_score}%</strong> · Keyword coverage <strong>${f.keyword_coverage}%</strong></div>
            <div class="small">Concept ${f.conceptual_accuracy}% · Reasoning ${f.reasoning_quality}% · Clarity ${f.clarity}%</div>
          </div>
        </div>`;
    }
  };

  document.getElementById('nextQuestion').onclick = () => {
    if (idx < qs.length - 1) idx += 1;
    answerInput.value = '';
    feedbackBox.innerHTML = '';
    render();
  };

  render();
}
