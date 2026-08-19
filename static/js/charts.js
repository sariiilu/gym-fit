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
        borderColor: '#3f7659',
        backgroundColor: 'rgba(63,118,89,0.10)',
        borderWidth: 2.5,
        tension: 0.35,
        fill: true,
        pointRadius: 3,
        pointBackgroundColor: '#3f7659',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: false, grid: { color: '#ecefe8' }, ticks: { font: { family: 'JetBrains Mono', size: 11 } } },
        x: { grid: { display: false }, ticks: { font: { family: 'JetBrains Mono', size: 10 } } }
      }
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
        borderColor: '#c98a4b',
        backgroundColor: 'rgba(201,138,75,0.10)',
        borderWidth: 2.5,
        tension: 0.35,
        fill: true,
        pointRadius: 3,
        pointBackgroundColor: '#c98a4b',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: false, grid: { color: '#ecefe8' }, ticks: { font: { family: 'JetBrains Mono', size: 11 } } },
        x: { grid: { display: false }, ticks: { font: { family: 'JetBrains Mono', size: 10 } } }
      }
    }
  });
}
