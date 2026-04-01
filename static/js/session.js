const root = document.getElementById('sessionApp');
if (root) {
  const qs = JSON.parse(root.dataset.questions || '[]');
  let idx = 0;
  let recording = false;
  const questionText = document.getElementById('questionText');
  const hintBox = document.getElementById('hintBox');
  const answerInput = document.getElementById('answerInput');
  const feedbackBox = document.getElementById('feedbackBox');
  const progress = document.getElementById('sessionProgress');

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
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({question_index: idx, answer: answerInput.value})
    });
    const data = await res.json();
    if (data.ok) {
      const f = data.feedback;
      document.getElementById('liveScore').textContent = f.overall_score + '%';
      document.getElementById('confidenceScore').textContent = f.confidence + '%';
      feedbackBox.innerHTML = `<div class="alert alert-info"><strong>Mock Feedback:</strong> Overall ${f.overall_score}% · Keyword coverage ${f.keyword_coverage}%</div>`;
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
