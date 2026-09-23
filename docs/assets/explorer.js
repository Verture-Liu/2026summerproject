const ARMS = [
  { key: "paleorigor", label: "PaleoRigor", color: "var(--arm-pr)" },
  { key: "raw_llm",    label: "Ablated arm", color: "var(--arm-ab)" },
];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, c =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const verdict = (ok) => `<span class="verdict ${ok ? "ok" : "bad"}">
  <span class="glyph" aria-hidden="true">${ok ? "✓" : "✕"}</span>${ok ? "Passed" : "Failed"}</span>`;

function stepList(run, forbidden) {
  if (!run.steps.length) return "";
  return `<ol class="steps">` + run.steps.map((s, i) => {
    const bad = forbidden.includes(s.skill);
    return `<li><span class="step-n">${i + 1}</span><div>
      <div class="step-skill${bad ? " forbidden" : ""}">${esc(s.skill)}</div>
      <div class="step-io">${esc(s.inputs.join(", ") || "—")} → ${esc(s.outputs.join(", ") || "—")}</div>
    </div></li>`;
  }).join("") + `</ol>`;
}

function runBody(run, sc) {
  if (run.decision === "blocked") {
    const rc = run.reason_code
      ? `<p style="margin:12px 0 0"><span class="reason-code">${esc(run.reason_code)}</span></p>` : "";
    return rc + `<p class="code">${esc(run.message || "")}</p>`;
  }
  const codes = run.failure_codes.length
    ? `<p style="margin:10px 0 0">` + run.failure_codes.map(c =>
        `<span class="fail-code">${esc(c)}</span>`).join("") + `</p>` : "";
  return codes + stepList(run, sc.forbidden_skills || []);
}

function renderExhibit(data) {
  const sc = data.scenarios.find(s => s.id === "H5-B1") || data.scenarios[0];
  const el = document.getElementById("exhibit");
  const cols = ARMS.map(arm => {
    const run = sc.runs[arm.key][0];
    return `<div class="exhibit-col">
      <p class="arm-name"><span class="swatch" style="background:${arm.color}"></span>${arm.label}</p>
      ${verdict(run.success)}
      ${runBody(run, sc)}
    </div>`;
  }).join("");
  el.innerHTML = `<div class="exhibit-head">
      <p class="card-kicker">The request — scenario ${esc(sc.id)}</p>
      <p class="ask">“${esc(sc.instruction)}”</p>
    </div><div class="exhibit-body">${cols}</div>`;
}

function renderSummary(data) {
  const box = document.getElementById("summary");
  const card = (title, s, p) => {
    const rows = ARMS.map(arm => {
      const a = s[arm.key], pct = (a.successes / a.total) * 100;
      return `<div class="bar-row">
        <div class="bar-label"><span>${arm.label}</span>
          <span><b>${a.successes}/${a.total}</b> · ${pct.toFixed(1)}%</span></div>
        <div class="bar-track">
          <div class="bar-fill" style="width:${pct}%;background:${arm.color}"></div>
          <div class="bar-ci" style="left:${a.wilson[0]}%;width:${(a.wilson[1] - a.wilson[0])}%"></div>
        </div></div>`;
    }).join("");
    return `<div class="bar-card"><p class="card-kicker">${title}</p>${rows}
      <p class="bar-note">Whiskers show two-sided Wilson 95% intervals.
         Exact McNemar p = ${p}.</p></div>`;
  };
  box.innerHTML = card(`Primary model — ${esc(data.models.primary)}`, data.summary.flash, data.summary.mcnemar_flash_p)
                + card(`Second model — ${esc(data.models.second)}`, data.summary.pro, data.summary.mcnemar_pro_p);
}

function renderGrid(data) {
  const t = document.getElementById("grid");
  const head = `<thead><tr><th>Scenario</th><th>Class</th>` +
    ARMS.map(a => `<th>${a.label}</th>`).join("") + `<th>Expected outcome</th></tr></thead>`;
  const rows = data.scenarios.map(sc => {
    const cells = ARMS.map(arm => `<td><div class="cellrow">` + sc.runs[arm.key].map(r =>
      `<span class="cell ${r.success ? "ok" : "bad"}" title="repeat ${r.repeat}: ${r.success ? "passed" : "failed"}${r.reason_code ? " (" + r.reason_code + ")" : ""}" tabindex="0">${r.success ? "✓" : "✕"}</span>`
    ).join("") + `</div></td>`).join("");
    const expect = sc.class === "boundary"
      ? `<span class="reason-code">${esc(sc.expected_reason_code)}</span>`
      : `run and produce the required outputs`;
    return `<tr><td class="scen-id">${esc(sc.id)}</td>
      <td><span class="tag ${sc.class === "boundary" ? "boundary" : ""}">${esc(sc.class)}</span></td>
      ${cells}<td>${expect}</td></tr>`;
  }).join("");
  t.innerHTML = head + `<tbody>${rows}</tbody>`;
}

function renderDetail(data, id) {
  const sc = data.scenarios.find(s => s.id === id);
  document.querySelectorAll("#picker button").forEach(b =>
    b.setAttribute("aria-pressed", String(b.dataset.id === id)));
  const cols = ARMS.map(arm => `<div class="runs-col">
      <p class="arm-name"><span class="swatch" style="background:${arm.color}"></span>${arm.label}</p>
      ${sc.runs[arm.key].map(r => `<div class="run">
        <div class="run-head">${verdict(r.success)}
          <span class="run-meta">repeat ${r.repeat} · ${r.decision} · ${r.latency_s}s · ${r.tokens} tok</span></div>
        ${runBody(r, sc)}</div>`).join("")}
    </div>`).join("");
  document.getElementById("detail").innerHTML =
    `<div class="exhibit" style="margin-top:0"><div class="exhibit-head">
       <p class="card-kicker">${esc(sc.id)} · ${esc(sc.class)} · inputs: ${esc(sc.inputs.join(", ") || "none")}</p>
       <p class="ask">“${esc(sc.instruction)}”</p></div></div>
     <div class="runs">${cols}</div>`;
}

fetch("data/benchmark_v5.json").then(r => r.json()).then(data => {
  renderExhibit(data);
  renderSummary(data);
  renderGrid(data);
  const picker = document.getElementById("picker");
  picker.innerHTML = data.scenarios.map(s =>
    `<button type="button" data-id="${s.id}" aria-pressed="false">${s.id} · ${s.class}</button>`).join("");
  picker.addEventListener("click", e => {
    const b = e.target.closest("button");
    if (b) renderDetail(data, b.dataset.id);
  });
  renderDetail(data, "H5-B1");
}).catch(err => {
  document.getElementById("exhibit").innerHTML =
    `<div class="exhibit-col"><p>Could not load the benchmark extract. ${esc(err.message)}</p></div>`;
});
