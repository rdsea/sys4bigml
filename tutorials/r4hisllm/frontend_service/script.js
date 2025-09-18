const AGENT_URL = "http://localhost:8001"; // agent_service API

// Fetch greeting from agent_service
fetch(`${AGENT_URL}/greet`)
  .then(response => response.json())
  .then(data => {
    document.getElementById('greeting').textContent = data.message;
  })
  .catch(err => {
    document.getElementById('greeting').textContent = "Welcome!";
    console.error("Error fetching greeting:", err);
  });

// Handle query form submission
document.getElementById('queryForm').addEventListener('submit', function(e) {
  e.preventDefault();
  const query = document.getElementById('queryInput').value;

  fetch(`${AGENT_URL}/plan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  })
    .then(response => response.json())
    .then(data => {
      // Show LLM suggestion
      const suggestionContainer = document.getElementById('suggestionContainer');
      const suggestionEl = document.getElementById('suggestion');
      if (data.llm_suggestion) {
        suggestionEl.textContent = data.llm_suggestion;
        suggestionContainer.classList.remove('hidden');
      } else {
        suggestionContainer.classList.add('hidden');
      }

      // Show expert votes
      const votesContainer = document.getElementById('votesContainer');
      const votesList = document.getElementById('votesList');
      votesList.innerHTML = "";
      if (data.expert_review && data.expert_review.votes) {
        data.expert_review.votes.forEach(v => {
          const li = document.createElement('li');
          li.textContent = `${v.expert}: ${v.vote} (${v.comment})`;
          votesList.appendChild(li);
        });
        votesContainer.classList.remove('hidden');
      } else {
        votesContainer.classList.add('hidden');
      }

      // Show final_result (detailed explanation)
      const finalResultContainer = document.getElementById('finalResultContainer');
      const finalResultEl = document.getElementById('finalResult');
      if (data.final_result) {
        finalResultEl.textContent = data.final_result;
        finalResultContainer.classList.remove('hidden');
      } else {
        finalResultContainer.classList.add('hidden');
      }

      // Show finalDecision (simple verdict)
      const finalDecisionContainer = document.getElementById('finalDecisionContainer');
      const finalDecisionEl = document.getElementById('finalDecision');
      if (data.finalDecision) {
        finalDecisionEl.textContent = data.finalDecision;
        finalDecisionContainer.classList.remove('hidden');
      } else {
        finalDecisionContainer.classList.add('hidden');
      }

      document.getElementById('queryInput').value = "";
    })
    .catch(err => {
      console.error("Error fetching plan:", err);
      alert("Error communicating with agent.");
    });
});
