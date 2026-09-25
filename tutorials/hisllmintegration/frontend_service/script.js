// Thin UI: the pattern list, logic and scoring all live in agent_service.
// This file only renders what the API returns.
const AGENT_API = "http://localhost:8001";

let SPECS = [];                       // from GET /patterns
const state = {};                     // key -> bool
const history = new Map();            // pattern label -> last envelope

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// --- the ladder -------------------------------------------------------------

async function loadLadder() {
  const resp = await fetch(`${AGENT_API}/patterns`);
  const body = await resp.json();
  SPECS = body.patterns;
  SPECS.forEach((p) => { state[p.key] = true; });
  $("ladder").innerHTML = SPECS.map(renderPattern).join("");
  SPECS.forEach((p) => {
    $(`chk-${p.key}`).addEventListener("change", (e) => {
      state[p.key] = e.target.checked;
      syncLadder();
    });
    $(`cmp-${p.key}`).addEventListener("click", () => compare(p.key));
  });
  syncLadder();
}

function renderPattern(p) {
  const o = p.observe;
  return `
  <div class="pattern" id="row-${p.key}">
    <div class="pattern-head">
      <label class="switch">
        <input type="checkbox" id="chk-${p.key}" checked>
        <span class="pattern-number">${p.number}</span>
        <span class="pattern-title">${esc(p.title)}</span>
      </label>
      <span class="unused-note" id="unused-${p.key}" hidden></span>
      <button class="ghost small" id="cmp-${p.key}">Compare off vs on</button>
    </div>
    <div class="pattern-body">
      <p class="requirement"><span class="tag need">WHY</span>
        ${esc(p.requirement)}</p>
      <p><span class="tag on">ON</span> ${esc(p.on)}</p>
      <p><span class="tag off">OFF</span> ${esc(p.off)}</p>
      <p class="breaks"><span class="tag warn">IF OFF</span> ${esc(p.breaks)}</p>
      <details>
        <summary>Where to see it (traces, metrics, analytics)</summary>
        <dl class="observe">
          <dt>Jaeger</dt><dd>${esc(o.jaeger)}</dd>
          <dt>Prometheus</dt><dd>${esc(o.prometheus)}</dd>
          <dt>Analytics</dt><dd><code>${esc(o.analytics)}</code></dd>
        </dl>
      </details>
    </div>
  </div>`;
}

// Patterns the selected task never runs are locked: their flag has no effect,
// and /compare rejects them.
function syncLadder() {
  const task = $("task").value;
  SPECS.forEach((p) => {
    const used = p.tasks.includes(task);
    $(`chk-${p.key}`).checked = state[p.key];
    $(`chk-${p.key}`).disabled = !used;
    $(`cmp-${p.key}`).disabled = !used;
    $(`row-${p.key}`).classList.toggle("is-off", !state[p.key]);
    $(`row-${p.key}`).classList.toggle("not-used", !used);
    $(`unused-${p.key}`).hidden = used;
    $(`unused-${p.key}`).textContent = `not used by ${task}`;
  });
  const on = SPECS.filter((p) => state[p.key]).length;
  const used = SPECS.filter((p) => p.tasks.includes(task)).map((p) => p.key);
  $("count-readout").textContent =
    `${on} of ${SPECS.length} patterns on (${label()}) · ${task} uses: ${used.join(", ")}`;
}

function label() {
  const on = SPECS.filter((p) => state[p.key]).map((p) => p.key);
  if (on.length === SPECS.length) return "all";
  if (!on.length) return "none";
  return on.join("+");
}

// --- running ----------------------------------------------------------------

function taskBody() {
  const task = $("task").value;
  const body = { patterns: { ...state } };
  if (task === "mission") body.summary_mode = $("mission-mode").value;
  if (task === "triage") body.report = $("report-input").value;
  if (task === "investigate") body.question = $("question-input").value;
  return body;
}

async function post(path, body, note) {
  $("result-card").hidden = false;
  $("run-note").textContent = note;
  $("result").innerHTML = `<p class="waiting">Running… A mission on a local
    model can take a few minutes. You can watch the trace appear in Jaeger.</p>`;
  [...document.querySelectorAll("button")].forEach((b) => (b.disabled = true));
  try {
    const resp = await fetch(`${AGENT_API}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || `HTTP ${resp.status}`);
    return data;
  } catch (err) {
    $("result").innerHTML = `<pre class="output">request failed: ${esc(err)}
Is the stack up, and is Ollama running?
  docker compose -f docker-compose.his.yml up
  OLLAMA_HOST=0.0.0.0:11434 ollama serve</pre>`;
    return null;
  } finally {
    [...document.querySelectorAll("button")].forEach((b) => (b.disabled = false));
    syncLadder();  // re-lock Compare buttons for unused patterns
    $("run-note").textContent = "";
  }
}

async function run() {
  const task = $("task").value;
  const data = await post(`/${task}`, taskBody(), `running ${task} (${label()})…`);
  if (!data) return;
  history.set(data.pattern_label, data);
  $("result-title").textContent = `${task} — ${data.pattern_label}`;
  $("result").innerHTML = renderEnvelope(data);
  renderHistory();
}

async function compare(key) {
  const task = $("task").value;
  const spec = SPECS.find((p) => p.key === key);
  const data = await post("/compare", { ...taskBody(), task, pattern: key },
    `running ${task} twice: ${key} off, then on…`);
  if (!data) return;
  $("result-title").textContent = `${task} — ${key} off vs on`;
  $("result").innerHTML = `
    <p class="compare-intro"><strong>${esc(spec.title)}</strong>. Only
      <code>${esc(key)}</code> changes; the other switches stay as they are
      (<code>${esc(label())}</code>).</p>
    ${renderDelta(data)}
    <div class="compare">
      <div class="arm off"><h3>${esc(key)} OFF</h3>${renderEnvelope(data.off)}</div>
      <div class="arm on"><h3>${esc(key)} ON</h3>${renderEnvelope(data.on)}</div>
    </div>`;
}

// --- rendering --------------------------------------------------------------

// Off-vs-on table of the key numbers.
function renderDelta(d) {
  const a = d.off.metrics || {}, b = d.on.metrics || {};
  const rows = [
    ["wrong values in map", a.errors_shipped, b.errors_shipped],
    ["LLM calls", a.model_calls, b.model_calls],
    ["prompt tokens", a.prompt_tokens, b.prompt_tokens],
    ["retries", a.retries, b.retries],
    ["tool calls", a.tool_calls, b.tool_calls],
    ["elapsed (ms)", a.elapsed_ms, b.elapsed_ms],
    ["status", d.off.status, d.on.status],
  ].filter(([, x, y]) => x !== undefined || y !== undefined);
  return `<table class="delta">
    <tr><th></th><th>off</th><th>on</th></tr>
    ${rows.map(([k, x, y]) => `<tr><td>${esc(k)}</td>
      <td class="${k === "wrong values in map" && x > 0 ? "bad" : ""}">${fmt(x)}</td>
      <td class="${k === "wrong values in map" && y === 0 ? "good" : ""}">${fmt(y)}</td></tr>`).join("")}
  </table>`;
}

const fmt = (v) => v === null || v === undefined ? "—" : esc(v);

function renderEnvelope(e) {
  const parts = [];
  if (e.status) {
    parts.push(`<p class="status s-${esc(e.status)}">${esc(e.status)}${
      e.reason ? ` — ${esc(e.reason)}` : ""}</p>`);
  }
  if (e.victim_map) parts.push(renderMap(e.victim_map));
  if (e.field_reports && e.field_reports.length) parts.push(renderFieldReports(e.field_reports));
  if (e.label !== undefined) {
    parts.push(`<p class="verdict">label <code>${esc(e.label)}</code>
      · route <code>${esc(e.route)}</code>
      · priority <code>${fmt(e.priority)}</code></p>`);
    if (e.action) parts.push(`<p class="action">${esc(e.action)}</p>`);
  }
  if (e.answer) parts.push(`<p class="action">${esc(e.answer)}</p>`);
  if (e.tool_steps && e.tool_steps.length) parts.push(renderToolSteps(e.tool_steps));
  if (e.steps && e.steps.length) parts.push(renderSteps(e.steps));
  if (e.issues && e.issues.length) parts.push(renderIssues(e.issues));
  if (e.score && e.score.detail && e.score.detail.length) parts.push(renderScore(e.score));
  parts.push(renderMetrics(e.metrics));
  return parts.join("");
}

// Step timeline. `actor` is AI, S (software) or H (human); with the human
// gate off, no H steps appear.
function renderSteps(steps) {
  return `<div class="steps"><h4>Steps (AI = LLM agent, S = software, H = human)</h4>${steps.map((s) => `
    <div class="step">
      <span class="actor a-${esc(s.actor)}">${esc(s.actor)}</span>
      <span class="step-name">${esc(s.step)}</span>
      <span class="step-detail">${esc(s.detail)}</span>
    </div>`).join("")}</div>`;
}

function renderToolSteps(steps) {
  return `<div class="steps"><h4>Tool calls</h4>${steps.map((s) => {
    const kind = s.tool ? "ok" : s.repeat ? "repeat" : "error";
    const name = s.tool || s.repeat || s.error;
    return `<div class="step">
      <span class="actor t-${kind}">${kind}</span>
      <span class="step-name">${esc(name)}</span>
      <span class="step-detail">${esc(JSON.stringify(s.args || {}))}${
        s.detail ? ` — ${esc(s.detail)}` : ""}</span>
    </div>`;
  }).join("")}</div>`;
}

function renderMap(map) {
  if (!map.length) return `<p class="verdict">empty victim map</p>`;
  return `<table class="map">
    <tr><th>sector</th><th>victims</th><th>min conf</th><th>source</th><th>notable</th></tr>
    ${map.map((e) => `<tr>
      <td>${esc(e.sector)}</td><td>${fmt(e.victims)}</td>
      <td>${fmt(e.min_confidence)}</td><td class="src">${fmt(e.source)}</td>
      <td>${esc(e.notable || "")}${e.note ? `<br><em>note: ${esc(e.note)}</em>` : ""}</td>
    </tr>`).join("")}
  </table>`;
}

// Mission field reports: where routing sent each one.
function renderFieldReports(reports) {
  return `<table class="map">
    <tr><th>field report</th><th>route</th><th>priority</th><th>action</th></tr>
    ${reports.map((r) => `<tr>
      <td>${esc(r.report)}</td><td><code>${esc(r.route)}</code></td>
      <td>${fmt(r.priority)}</td><td>${esc(r.action || "")}</td>
    </tr>`).join("")}
  </table>`;
}

function renderIssues(issues) {
  return `<div class="issues"><h4>Problems a turned-off pattern would have caught</h4>
    ${issues.map((i) => `<p><span class="tag warn">${esc(i.pattern)}</span>
      ${esc(i.detail)}</p>`).join("")}</div>`;
}

function renderScore(score) {
  const n = score.errors_shipped;
  return `<div class="score ${n ? "bad" : ""}">
    <h4>Checked against the real drone data${n === null ? "" : `: ${n} wrong value(s) in the map`}</h4>
    ${score.detail.map((d) => `<p>${esc(d)}</p>`).join("")}</div>`;
}

const METRIC_LABELS = {
  model_calls: "LLM calls", prompt_tokens: "prompt tokens", retries: "retries",
  tool_calls: "tool calls", elapsed_ms: "ms total",
  errors_shipped: "wrong values in map",
};

function renderMetrics(m) {
  if (!m) return "";
  return `<div class="metrics">${Object.keys(METRIC_LABELS)
    .filter((k) => m[k] !== undefined)
    .map((k) => `<span><b>${fmt(m[k])}</b>${esc(METRIC_LABELS[k])}</span>`)
    .join("")}</div>`;
}

function renderHistory() {
  if (!history.size) return;
  $("history-card").hidden = false;
  const rows = [...history.entries()].map(([lbl, e]) => {
    const m = e.metrics || {};
    return `<tr><td><code>${esc(lbl)}</code></td><td>${esc(e.task)}</td>
      <td>${fmt(e.status)}</td><td class="${m.errors_shipped > 0 ? "bad" : ""}">
      ${fmt(m.errors_shipped)}</td><td>${fmt(m.model_calls)}</td>
      <td>${fmt(m.elapsed_ms)}</td></tr>`;
  });
  $("history").innerHTML = `<table class="delta">
    <tr><th>patterns on</th><th>task</th><th>status</th><th>wrong values</th>
        <th>LLM calls</th><th>ms</th></tr>${rows.join("")}</table>`;
}

// --- wiring -----------------------------------------------------------------

$("task").addEventListener("change", () => {
  ["mission", "triage", "investigate"].forEach((t) => {
    $(`task-${t}`).hidden = $("task").value !== t;
  });
  syncLadder();
});
$("run-btn").addEventListener("click", run);
$("all-off").addEventListener("click", () => {
  SPECS.forEach((p) => { state[p.key] = false; }); syncLadder();
});
$("all-on").addEventListener("click", () => {
  SPECS.forEach((p) => { state[p.key] = true; }); syncLadder();
});

loadLadder().catch((err) => {
  $("ladder").innerHTML = `<pre class="output">could not load the pattern
registry from ${AGENT_API}/patterns: ${esc(err)}

Is the stack up, and is Ollama running?
  docker compose -f docker-compose.his.yml up
  OLLAMA_HOST=0.0.0.0:11434 ollama serve</pre>`;
});
