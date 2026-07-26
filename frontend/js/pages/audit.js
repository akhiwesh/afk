import { API } from "../api.js";
import { UI } from "../ui.js";
import { renderGauge, ruleIdChip, scoreStatus } from "../diagnostic-ui.js";

const MODULE_META = {
  context: { subtitle: "Business context before we test how revenue is earned." },
  reflection: { subtitle: "Your hypothesis — captured before we examine each system." },
  demand: { tags: ["Thin funnel", "Single source risk", "No marketing cadence", "Sporadic pipeline"] },
  qualification: { tags: ["No qualification filter", "Calendar pollution", "Low worth-it rate"] },
  conversion: { tags: ["Low close rate", "Weak follow-up discipline", "Founder dependency", "Undocumented process", "Long sales cycle"] },
  pricing: { tags: ["Underpricing", "Habitual discounting", "Stale prices", "Low confidence"] },
  retention: { tags: ["Low repeat rate", "Unknown churn", "No retention process"] },
  operations: { tags: ["Founder in every sale", "Undocumented process", "Delegation gap"] },
};

const QUESTION_EVIDENCE = {
  conversion_close_rate: { level: "High", detail: "Invoices + Leads" },
  conversion_followups: { level: "Medium", detail: "Self-reported" },
  conversion_owner: { level: "High", detail: "Activity data" },
  conversion_process: { level: "Low", detail: "Self-reported" },
  conversion_cycle_days: { level: "High", detail: "Invoice dates" },
  leads_per_month: { level: "Medium", detail: "Self-reported" },
  pct_leads_worth_it: { level: "Medium", detail: "Self-reported" },
  repeat_rate: { level: "Medium", detail: "Self-reported" },
  pricing_confidence: { level: "Low", detail: "Self-reported" },
  gross_margin_band: { level: "Low", detail: "Optional context" },
  cac_known: { level: "Low", detail: "Optional context" },
};

const STATUS_STYLE = {
  healthy: { cls: "is-healthy", label: "Healthy" },
  pressure: { cls: "is-pressure", label: "Pressure" },
  constraint: { cls: "is-critical", label: "Critical" },
  captured: { cls: "is-moderate", label: "Captured" },
  incomplete: { cls: "is-muted", label: "Incomplete" },
  insufficient: { cls: "is-muted", label: "Need more data" },
};

function evidenceBadge(q) {
  const ev = QUESTION_EVIDENCE[q.id] || { level: "Medium", detail: "Self-reported" };
  const cls = ev.level === "High" ? "is-high" : ev.level === "Low" ? "is-low" : "is-medium";
  return `<span class="diag-evidence ${cls}" title="${ev.detail}">Evidence: ${ev.level}</span>`;
}

function fieldHtml(q, answers, qIndex, prefills) {
  const pf = (prefills || {})[q.id];
  // If the founder hasn't answered but evidence measured it, seed the value so
  // they confirm rather than type. Their own saved answer always wins.
  const v = (answers[q.id] ?? "") !== "" ? answers[q.id] : (pf ? pf.value : "");
  const num = String(qIndex + 1).padStart(2, "0");

  let control = "";
  if (q.type === "select" && q.options?.length) {
    control = `<div class="diag-choices" data-q="${q.id}">
      ${q.options.map(o => `
        <button type="button" class="diag-choice ${v === o ? "is-selected" : ""}" data-value="${o.replace(/"/g, "&quot;")}">${o}</button>`).join("")}
    </div>`;
  } else if (q.type === "scale") {
    const min = q.min ?? 0;
    const max = q.max ?? 100;
    const unit = q.unit ?? "";
    const cur = v !== "" ? v : Math.round((min + max) / 2);
    control = `<div class="diag-range">
      <input type="range" data-q="${q.id}" min="${min}" max="${max}" value="${cur}">
      <span class="diag-range-val" data-scale-val="${q.id}">${cur}${unit}</span>
    </div>`;
  } else if (q.type === "number") {
    control = `<div style="display:flex;align-items:center;gap:0.5rem;">
      <input class="diag-number" type="number" data-q="${q.id}" value="${v}" placeholder="e.g. 45" min="0">
      <span class="diag-muted" style="font-size:0.85rem;">${q.unit || "days"}</span>
    </div>`;
  } else {
    control = `<textarea class="diag-textarea" data-q="${q.id}" rows="2" placeholder="In your own words…">${v}</textarea>`;
  }

  const optional = q.optional ? ` <span class="diag-muted" style="font-size:0.72rem;font-weight:400;">(optional)</span>` : "";
  return `
    <div class="diag-qcard">
      <div class="diag-qhead">
        <div style="display:flex;gap:0.75rem;flex:1;">
          <span class="diag-qnum">${num}</span>
          <p class="diag-qlabel">${q.label}${optional}</p>
        </div>
        ${evidenceBadge(q)}
      </div>
      ${pf && (answers[q.id] ?? "") === "" ? `
        <div class="diag-prefill" data-prefill-for="${q.id}">
          <span class="diag-prefill-dot"></span>
          <span>${pf.note} <span class="diag-muted">Confirm or change below.</span></span>
        </div>` : ""}
      ${control}
    </div>`;
}

function collectAnswers(container) {
  const payload = {};
  container.querySelectorAll("[data-q]").forEach(el => {
    if (el.classList?.contains("diag-choices")) return;
    if (el.type === "range" || el.type === "number" || el.tagName === "TEXTAREA") {
      payload[el.dataset.q] = el.value;
    }
  });
  container.querySelectorAll(".diag-choices").forEach(group => {
    const sel = group.querySelector(".diag-choice.is-selected");
    if (sel) payload[group.dataset.q] = sel.dataset.value;
  });
  return payload;
}

function wireInteractions(container, state, render) {
  container.querySelectorAll('input[type="range"][data-q]').forEach(slider => {
    const out = container.querySelector(`[data-scale-val="${slider.dataset.q}"]`);
    const unit = state.modules.flatMap(m => m.questions).find(q => q.id === slider.dataset.q)?.unit ?? "";
    const sync = () => { if (out) out.textContent = `${slider.value}${unit}`; };
    slider.addEventListener("input", sync);
    sync();
  });

  container.querySelectorAll(".diag-choices").forEach(group => {
    group.querySelectorAll(".diag-choice").forEach(btn => {
      btn.addEventListener("click", () => {
        group.querySelectorAll(".diag-choice").forEach(b => b.classList.remove("is-selected"));
        btn.classList.add("is-selected");
      });
    });
  });

  container.querySelector("[data-breakdown-toggle]")?.addEventListener("click", () => {
    const el = container.querySelector("[data-breakdown]");
    if (el) el.hidden = !el.hidden;
  });
}

function renderPayoff(payoff, showBreakdown) {
  if (!payoff) return "";
  const st = STATUS_STYLE[payoff.status] || STATUS_STYLE.incomplete;
  const score = payoff.dimension?.score;
  const findings = payoff.findings || [];

  const breakdownRows = findings.map(f => `
    <div class="diag-breakdown-row is-hit">
      <span>${ruleIdChip(f.rule_id, f.rule_pack)}${(f.reasoning || "").slice(0, 48)}…</span>
      <span class="diag-breakdown-pen is-hit">-${f.penalty || "?"}</span>
    </div>`).join("");

  const totalPen = findings.reduce((s, f) => s + (f.penalty || 0), 0);

  const ruledFindings = findings.filter(f => f.rule_id).slice(0, 4);

  const sections = payoff.system_finding
    ? [
        ["Finding", payoff.system_finding.finding],
        ["Root Cause", payoff.system_finding.root_cause],
        ["Business Impact", payoff.system_finding.business_impact],
        ["Score", payoff.system_finding.score_line],
        ["Recommended Action", payoff.system_finding.recommended_action],
        ["Expected Outcome", payoff.system_finding.expected_outcome],
      ].filter(([, c]) => c)
    : [[ "Finding", payoff.headline ]];

  return `
    <div class="diag-result">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;flex-wrap:wrap;">
        <p class="diag-result-kicker">Assessment Result</p>
        <span class="diag-status-pill ${st.cls}">${st.label}</span>
      </div>
      ${score != null ? renderGauge(score) : ""}
      ${findings.length ? `
        <button type="button" class="diag-breakdown-toggle" data-breakdown-toggle>Scoring breakdown</button>
        <div data-breakdown ${showBreakdown ? "" : "hidden"}>
          ${breakdownRows}
          <div class="diag-breakdown-row" style="font-weight:600;">
            <span>Total penalty</span>
            <span class="diag-breakdown-pen is-hit">-${totalPen}</span>
          </div>
        </div>` : ""}
      ${ruledFindings.length ? `
        <div style="margin-top:0.75rem;display:flex;flex-wrap:wrap;gap:0.35rem;">
          ${ruledFindings.map(f => ruleIdChip(f.rule_id, f.rule_pack)).join("")}
        </div>` : ""}
      <div style="margin-top:0.5rem;">
        ${sections.map(([label, content]) => `
          <div class="diag-section">
            <p class="diag-section-label">${label}</p>
            <div class="diag-section-body">${content}</div>
          </div>`).join("")}
      </div>
      ${(payoff.contradictions || []).length ? `
        <div class="diag-section">
          <p class="diag-section-label">Belief vs uploaded evidence</p>
          ${payoff.contradictions.map(c => `
            <div style="border:1px solid #fde68a;border-radius:8px;padding:0.85rem;margin-bottom:0.5rem;font-size:0.82rem;">
              <div><strong>You said:</strong> "${c.belief.answer}"</div>
              <div style="margin-top:0.35rem;"><strong>Evidence:</strong> ${c.evidence.value} — ${c.evidence.basis}</div>
            </div>`).join("")}
        </div>` : ""}
      ${payoff.confidence_note ? `<p class="diag-hint">${payoff.confidence_note}</p>` : ""}
      ${payoff.evidence_hint && !payoff.confidence_note ? `<p class="diag-hint">💡 ${payoff.evidence_hint}</p>` : ""}
    </div>`;
}

function renderDiagnosisPreview(preview) {
  if (!preview) return "";
  const hv = preview.hypothesis_verdict;
  return `
    <div class="diag-preview">
      <div class="diag-result-kicker">Executive preview · ${preview.priority_model || "AFK-PRI-0001"}</div>
      ${renderGauge(preview.primary_score)}
      <div style="text-align:center;margin-bottom:1rem;">
        <div style="font-weight:600;">${preview.primary_constraint}</div>
        <div class="diag-muted" style="font-size:0.82rem;">Health ${preview.health_score}/100</div>
      </div>
      ${hv ? `<p class="diag-section-body"><strong>${hv.verdict}</strong> — ${hv.explanation}</p>` : ""}
      ${(preview.compound_findings || []).length ? `
        <div style="margin-top:0.75rem;">
          ${preview.compound_findings.map(c => `
            <div class="diag-section-body" style="padding:0.35rem 0;">${ruleIdChip(c.compound_id)}${c.reasoning}</div>`).join("")}
        </div>` : ""}
    </div>`;
}

async function runAnalysisSequence(container) {
  const steps = ["Analyzing your business…", "Building your Business Twin", "Detecting constraints", "Calculating Revenue Health"];
  container.innerHTML = `<div class="diag-page"><div class="diag-inner" style="padding-top:18vh;"><div id="seq" style="display:flex;flex-direction:column;gap:1rem;"></div></div></div>`;
  const seq = container.querySelector("#seq");
  const wait = (ms) => new Promise(r => setTimeout(r, ms));
  for (const label of steps) {
    const row = document.createElement("div");
    row.style.cssText = "display:flex;align-items:center;gap:0.75rem;";
    row.innerHTML = `<span style="width:16px;height:16px;border:2px solid #9a3412;border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;"></span><span class="diag-muted">${label}</span>`;
    seq.appendChild(row);
    await wait(550);
    row.innerHTML = `<span style="color:#4c7a4a;font-weight:700;">✓</span><span>${label}</span>`;
  }
  await wait(400);
  seq.insertAdjacentHTML("beforeend", `<style>@keyframes spin{to{transform:rotate(360deg)}}</style>
    <h2 style="font-family:'Lora',Georgia,serif;font-size:1.35rem;margin-top:1rem;">Your Business Twin is ready.</h2>
    <p class="diag-muted">Opening Executive Diagnosis…</p>`);
  await wait(1200);
}

function renderLivePanel(lp) {
  if (!lp) return `<div class="diag-live" id="live-panel"><span class="diag-muted" style="font-size:0.8rem;">Answer a question to see your engine react.</span></div>`;
  const pct = Math.round((lp.answered / lp.total) * 100);
  const bar = (lp.dimensions || []).map(d => {
    const sc = d.score;
    const hue = sc === null ? "#94a3b8" : sc >= 70 ? "#1D9E75" : sc >= 50 ? "#EF9F27" : "#E24B4A";
    const w = sc === null ? Math.max(6, Math.round((d.coverage || 0) * 100)) : sc;
    const isPc = lp.primary_constraint && d.key === lp.primary_constraint.key;
    return `<div style="display:grid;grid-template-columns:104px 1fr 30px;gap:8px;align-items:center;margin:5px 0;">
      <span style="font-size:0.72rem;${isPc ? "font-weight:600;" : ""}" class="${isPc ? "" : "diag-muted"}">${d.label.split(" ")[0]}</span>
      <span style="height:5px;border-radius:3px;background:var(--diag-border-subtle);display:block;overflow:hidden;">
        <span style="display:block;height:100%;width:${w}%;background:${hue};transition:width .5s cubic-bezier(.16,.84,.44,1);opacity:${sc === null ? .35 : 1};"></span>
      </span>
      <span style="font-size:0.72rem;font-variant-numeric:tabular-nums;text-align:right;">${sc == null ? "\u2014" : sc}</span>
    </div>`;
  }).join("");
  const head = lp.sufficient ? `
      <div style="display:flex;align-items:baseline;gap:8px;">
        <span style="font-size:2.4rem;font-weight:600;line-height:1;font-variant-numeric:tabular-nums;">${lp.health_score}</span>
        <span class="diag-muted" style="font-size:0.8rem;">/ 100 · ${lp.risk_level}</span>
      </div>
      <p style="font-size:0.82rem;line-height:1.5;margin:.4rem 0 .75rem;">${lp.primary_constraint && lp.primary_constraint.one_liner ? lp.primary_constraint.one_liner : ""}</p>`
    : `<p style="font-size:0.82rem;line-height:1.5;margin:0 0 .75rem;" class="diag-muted">${lp.message || "Keep going \u2014 the engine will not guess."}</p>`;
  return `<div class="diag-live" id="live-panel">
      <div class="diag-result-kicker" style="margin-bottom:.5rem;">Live diagnosis · ${lp.answered}/${lp.total} answered (${pct}%)</div>
      ${head}${bar}
      <p class="diag-muted" style="font-size:0.68rem;margin-top:.6rem;line-height:1.4;">Recomputed by the deterministic engine on every change.</p>
    </div>`;
}

async function refreshLivePanel(container) {
  const host = container.querySelector("#live-panel");
  if (!host) return;
  try {
    const lp = await API.post("/intelligence/audit/live-preview", { answers: collectAnswers(container) });
    const fresh = container.querySelector("#live-panel");
    if (fresh) fresh.outerHTML = renderLivePanel(lp);
  } catch (e) { }
}

export async function renderAudit(container, startModuleId = null) {
  container.innerHTML = `<div class="diag-page"><div class="diag-inner" style="padding:3rem 0;text-align:center;"><span class="diag-muted">Loading diagnostic…</span></div></div>`;

  let state;
  try {
    state = await API.get("/intelligence/audit/modules");
  } catch (e) {
    container.innerHTML = `<div class="diag-page"><div class="diag-inner"><p>Could not load audit: ${e.message}</p></div></div>`;
    return;
  }

  let activeId = startModuleId || state.current_module || state.modules[0]?.id;
  let showingPayoff = false;
  let lastPayoff = null;
  let showBreakdown = true;

  const render = () => {
    const mod = state.modules.find(m => m.id === activeId) || state.modules[0];
    const idx = state.modules.findIndex(m => m.id === mod.id);
    const answers = state.answers || {};
    const pct = Math.round((state.systems_complete / state.systems_total) * 100);
    const meta = MODULE_META[mod.id] || {};
    const tags = (meta.tags || []).map(t => `<span class="diag-tag">${t}</span>`).join("");

    const stepper = state.modules.map((m, i) => {
      const done = m.progress.complete;
      const active = m.id === mod.id;
      const dot = done ? "✓" : String(i + 1);
      const cls = ["diag-step", active ? "is-active" : "", done ? "is-done" : ""].filter(Boolean).join(" ");
      return `<button type="button" class="${cls}" data-goto="${m.id}">
        <span class="diag-step-dot">${dot}</span>
        <span>${m.title.replace(" System", "").replace(" & Monetization", "")}</span>
      </button>`;
    }).join("");

    const requiredQs = mod.questions.filter(q => !q.optional);
    const optionalQs = mod.questions.filter(q => q.optional);
    const questions = requiredQs.map((q, i) => fieldHtml(q, answers, i, mod.prefills)).join("");
    const optionalBlock = optionalQs.length ? `
      <div class="diag-optional-block">
        <div class="diag-optional-kicker">Optional context · AFK-AUD-0001 phase-b</div>
        ${optionalQs.map((q, i) => fieldHtml(q, answers, requiredQs.length + i, mod.prefills)).join("")}
      </div>` : "";

    container.innerHTML = `
      <div class="diag-page">
        <div class="diag-inner">
          <div class="diag-hero">
            <p class="diag-hero-kicker">Revenue Diagnostic · System ${idx + 1} of ${state.modules.length}</p>
            <h1>${mod.title}</h1>
            <p>${mod.hook || meta.subtitle || ""}</p>
            ${tags ? `<div class="diag-tags">${tags}</div>` : ""}
          </div>

          <div class="diag-progress"><div style="width:${pct}%;"></div></div>
          <p class="diag-muted" style="font-size:0.82rem;margin:0 0 1rem;">${state.systems_complete} of ${state.systems_total} systems examined</p>

          <div class="diag-stepper">${stepper}</div>

          ${state.systems_complete === state.systems_total && state.diagnosis_preview ? renderDiagnosisPreview(state.diagnosis_preview) : ""}

          ${showingPayoff && lastPayoff ? renderPayoff(lastPayoff, showBreakdown) : `
            <div class="diag-live-grid">
              <div>${questions}${optionalBlock}
                ${mod.evidence_hint ? `<p class="diag-hint">💡 ${mod.evidence_hint}</p>` : ""}
              </div>
              ${renderLivePanel(null)}
            </div>
          `}

          <div class="diag-actions">
            ${showingPayoff ? `
              <button type="button" class="diag-btn-primary" id="audit-next">${idx < state.modules.length - 1 ? "Next system →" : "View full diagnosis →"}</button>
              <button type="button" class="diag-btn-secondary" id="audit-edit">Edit answers</button>
            ` : `
              <button type="button" class="diag-btn-primary" id="audit-save">${idx < state.modules.length - 1 ? "Save & see finding" : "Finish & diagnose"}</button>
              ${idx > 0 ? `<button type="button" class="diag-btn-secondary" id="audit-back">← Previous</button>` : ""}
            `}
            <span class="diag-muted" style="font-size:0.82rem;">${mod.progress.answered}/${mod.progress.total} answered</span>
          </div>
        </div>
      </div>`;

    wireInteractions(container, state, render);

    if (!showingPayoff) {
      refreshLivePanel(container);
      let lpT = null;
      const ping = () => { clearTimeout(lpT); lpT = setTimeout(() => refreshLivePanel(container), 350); };
      container.querySelectorAll("[data-q]").forEach(el => {
        el.addEventListener("click", ping);
        el.addEventListener("input", ping);
        el.addEventListener("change", ping);
      });
    }

    container.querySelectorAll("[data-goto]").forEach(btn => {
      btn.addEventListener("click", () => {
        activeId = btn.dataset.goto;
        showingPayoff = false;
        lastPayoff = state.modules.find(m => m.id === activeId)?.payoff || null;
        if (lastPayoff) showingPayoff = true;
        render();
      });
    });

    container.querySelector("#audit-back")?.addEventListener("click", () => {
      if (idx > 0) {
        activeId = state.modules[idx - 1].id;
        showingPayoff = !!state.modules[idx - 1].payoff;
        lastPayoff = state.modules[idx - 1].payoff || null;
        render();
      }
    });

    container.querySelector("#audit-edit")?.addEventListener("click", () => {
      showingPayoff = false;
      render();
    });

    container.querySelector("#audit-next")?.addEventListener("click", async () => {
      if (idx < state.modules.length - 1) {
        activeId = state.modules[idx + 1].id;
        showingPayoff = false;
        lastPayoff = null;
        render();
      } else {
        await runAnalysisSequence(container);
        window.location.hash = "#diagnosis";
      }
    });

    container.querySelector("#audit-save")?.addEventListener("click", async () => {
      const btn = container.querySelector("#audit-save");
      btn.disabled = true;
      btn.textContent = "Saving…";
      try {
        const res = await API.put(`/intelligence/audit/modules/${mod.id}`, {
          answers: collectAnswers(container),
        });
        state = await API.get("/intelligence/audit/modules");
        lastPayoff = res.payoff;
        showingPayoff = true;

        if (res.all_modules_complete && res.diagnosed) {
          btn.textContent = "Done";
          render();
          await runAnalysisSequence(container);
          window.location.hash = "#diagnosis";
          return;
        }

        render();
        UI.toast(res.payoff?.verdict || "System saved.", "success");
      } catch (e) {
        UI.toast(`Save failed: ${e.message}`, "error");
        btn.disabled = false;
        btn.textContent = idx < state.modules.length - 1 ? "Save & see finding" : "Finish & diagnose";
      }
    });
  };

  render();
}
