async function loadWeightChart(canvasId) {
  const res = await fetch('/api/weight');
  const data = await res.json();
  const ctx = document.getElementById(canvasId);
  if (!ctx || data.length === 0) return;

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.map(d => d.date),
      datasets: [{
        label: 'Gewicht (kg)',
        data: data.map(d => d.weight_kg),
        borderColor: '#3c6e52',
        backgroundColor: 'rgba(60,110,82,0.1)',
        tension: 0.25,
        fill: true,
        pointRadius: 3,
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: false } }
    }
  });
}

async function loadExerciseNames(selectId, canvasId) {
  const res = await fetch('/api/exercise-names');
  const names = await res.json();
  const select = document.getElementById(selectId);
  if (!select) return;

  select.innerHTML = names.map(n => `<option value="${n}">${n}</option>`).join('');
  if (names.length > 0) {
    renderExerciseChart(canvasId, names[0]);
  }
  select.addEventListener('change', () => renderExerciseChart(canvasId, select.value));
}

let exerciseChartInstance = null;

async function renderExerciseChart(canvasId, exerciseName) {
  const res = await fetch(`/api/exercise-progress?name=${encodeURIComponent(exerciseName)}`);
  const data = await res.json();
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  if (exerciseChartInstance) exerciseChartInstance.destroy();

  exerciseChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.map(d => d.date),
      datasets: [{
        label: 'Gewicht (kg)',
        data: data.map(d => d.gewicht_kg),
        borderColor: '#2b4f3b',
        backgroundColor: 'rgba(43,79,59,0.1)',
        tension: 0.25,
        fill: true,
        pointRadius: 3,
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: false } }
    }
  });
}
