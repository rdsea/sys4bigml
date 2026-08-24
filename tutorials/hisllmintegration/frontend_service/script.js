const AGENT_API = "http://localhost:8001";

async function callAgent(path, options, outEl, btn) {
  const out = document.getElementById(outEl);
  const button = document.getElementById(btn);
  out.hidden = false;
  out.textContent = "… waiting for the agent (watch the trace grow in Jaeger)";
  button.disabled = true;
  try {
    const resp = await fetch(`${AGENT_API}${path}`, options);
    const body = await resp.json();
    out.textContent = JSON.stringify(body, null, 2);
    if (!resp.ok) out.textContent = `HTTP ${resp.status}\n` + out.textContent;
  } catch (err) {
    out.textContent = `request failed: ${err}\nIs the stack up? (docker compose -f docker-compose.his.yml up)`;
  } finally {
    button.disabled = false;
  }
}

document.getElementById("greet-btn").addEventListener("click", () =>
  callAgent("/greet", { method: "GET" }, "greet-out", "greet-btn"));

document.getElementById("triage-btn").addEventListener("click", () =>
  callAgent("/triage", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ report: document.getElementById("report-input").value }),
  }, "triage-out", "triage-btn"));

document.getElementById("mission-btn").addEventListener("click", () =>
  callAgent("/mission", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      summary_mode: document.getElementById("mission-mode").value,
    }),
  }, "mission-out", "mission-btn"));
