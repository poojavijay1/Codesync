// Get semester from URL parameter
const urlParams = new URLSearchParams(window.location.search);
const semester = urlParams.get('semester');

// Update the semester display
document.getElementById('currentSemester').textContent = semester || 'Unknown';

// Retrieve experiments from localStorage
function getExperiments() {
  const experimentsData = localStorage.getItem('experimentsBySemester');
  return experimentsData ? JSON.parse(experimentsData) : {
    S1: [], S2: [], S3: [], S4: [], S5: [], S6: [], S7: [], S8: []
  };
}

// Function to get status badge color class
function getStatusBadgeClass(status) {
  return `status-badge ${status}`;
}

// Function to view code
function viewCode(id) {
  const experiments = getExperiments();
  const experiment = experiments[semester].find(exp => exp.id === id);
  if (experiment) {
    alert(`Code for ${experiment.experimentName}:\n\n${experiment.code}`);
  }
}

// Function to render experiments
function renderExperiments() {
  const experiments = getExperiments();
  const semesterExperiments = experiments[semester] || [];
  const tbody = document.getElementById('experimentsTable');
  const experimentCount = document.querySelector('.experiment-count');
  
  // Update experiment count
  experimentCount.textContent = `Total Experiments: ${semesterExperiments.length}`;
  
  // Clear existing rows
  tbody.innerHTML = '';
  
  // Add experiment rows
  semesterExperiments.forEach((experiment, index) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${index + 1}</td>
      <td>${experiment.labName}</td>
      <td>${experiment.experimentName}</td>
      <td>
        <span class="${getStatusBadgeClass(experiment.status)}">
          ${experiment.status}
        </span>
      </td>
      <td>${experiment.date}</td>
      <td>
        <button class="view-code-btn" onclick="viewCode('${experiment.id}')">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
          View Code
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Initial render
renderExperiments();

// Set up real-time updates
window.addEventListener('storage', function(e) {
  if (e.key === 'experimentsBySemester') {
    renderExperiments();
  }
});