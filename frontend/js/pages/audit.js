import { API } from "../api.js";
import { UI } from "../ui.js";

async function runAnalysisSequence(container) {
  const steps = [
    "Analyzing your business…",
    "Building your Business Twin",
    "Understanding your revenue model",
    "Analyzing the customer journey",
    "Detecting constraints",
    "Calculating Revenue Health",
  ];
  container.innerHTML = `
    <div style="max-width:560px;margin:0 auto;padding-top:18vh;">
      <div id="seq" style="display:flex;flex-direction:column;gap:1rem;"></div>
    </div>`;
  const seq = container.querySelector("#seq");
  const wait = (ms) => new Promise(r => setTimeout(r, ms));
  for (const label of steps) {
    const row = document.createElement("div");
    row.style.cssText = "display:flex;align-items:center;gap:0.75rem;opacity:0;transition:opacity 0.4s;";
    row.innerHTML = `<span class="seq-dot" style="width:16px;height:16px;border:2px solid hsl(var(--primary));border-top-color:transparent;border-radius:50%;display:inline-block;animation:spin 0.8s linear infinite;"></span>
      <span style="color:hsl(var(--text-muted));">${label}</span>`;
    seq.appendChild(row);
    requestAnimationFrame(() => (row.style.opacity = "1"));
    await wait(650);
    row.querySelector(".seq-dot").style.cssText = "color:hsl(var(--success));font-weight:700;";
    row.querySelector(".seq-dot").textContent = "✓";
    row.lastElementChild.style.color = "hsl(var(--text))";
  }
  await wait(350);
  seq.insertAdjacentHTML("beforeend", `
    <style>@keyframes spin{to{transform:rotate(360deg)}}</style>
    <div style="margin-top:1.5rem;opacity:0;transition:opacity 0.6s;" id="seq-done">
      <h2 style="font-size:1.35rem;font-weight:650;line-height:1.4;">We've built the first version of your Business Twin.</h2>
      <p style="color:hsl(var(--text-muted));margin-top:0.5rem;">Opening your Executive Diagnosis…</p>
    </div>`);
  requestAnimationFrame(() => (container.querySelector("#seq-done").style.opacity = "1"));
  await wait(1400);
}

const STATUS_STYLE = {
  healthy: { color: "hsl(var(--success))", label: "Healthy" },
  pressure: { color: "hsl(38 92% 55%)", label: "Pressure" },
  constraint: { color: "hsl(var(--danger,0 72% 55%))", label: "Critical" },
  captured: { color: "hsl(var(--primary))", label: "Captured" },
  incomplete: { color: "hsl(var(--text-muted))", label: "Incomplete" },
  insufficient: { color: "hsl(var(--text-muted))", label: "Need more data" },
};

const SYSTEM_FINDING_LABELS = [
  ["finding", "Finding"],
  ["root_cause", "Root Cause"],
  ["business_impact", "Business Impact"],
  ["score_line", "Score"],
  ["recommended_action", "Recommended Action"],
  ["expected_outcome", "Expected Outcome"],
];

function renderPayoff(payoff) {
  if (!payoff) return "";
  const st = STATUS_STYLE[payoff.status] || STATUS_STYLE.incomplete;
  const scoreBlock = payoff.dimension?.score != null ? `
    <div style="margin-top:1rem;display:flex;align-items:baseline;gap:0.5rem;">
      <span style="font-size:2rem;font-weight:700;">${payoff.dimension.score}</span>
      <span style="color:hsl(var(--text-muted));font-size:0.85rem;">/100 · ${payoff.dimension.label}</span>
    </div>` : "";

  const findings = (payoff.findings || []).slice(0, 2).map(f => `
    <li style="margin:0.5rem 0;line-height:1.55;font-size:0.9rem;">${f.reasoning}</li>`).join("");

  const systemFinding = payoff.system_finding ? `
    <div style="margin-top:1rem;display:grid;gap:0.85rem;">
      ${SYSTEM_FINDING_LABELS.map(([key, label]) => payoff.system_finding[key] ? `
        <div>
          <div style="font-size:0.68rem;letter-spacing:0.1em;text-transform:uppercase;color:hsl(var(--text-muted));margin-bottom:0.25rem;">${label}</div>
          <p style="font-size:0.88rem;line-height:1.6;margin:0;">${payoff.system_finding[key]}</p>
        </div>` : "").join("")}
    </div>` : "";

  return `
    <div style="margin-top:1.5rem;border:1px solid hsl(var(--border));border-radius:12px;padding:1.25rem 1.5rem;background:hsl(var(--bg-subtle,220 14% 10%));">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;flex-wrap:wrap;">
        <div>
          <div style="font-size:0.68rem;letter-spacing:0.12em;text-transform:uppercase;color:hsl(var(--text-muted));margin-bottom:0.35rem;">System finding</div>
          <div style="font-weight:600;font-size:1.05rem;line-height:1.45;">${payoff.headline}</div>
        </div>
        <span style="font-size:0.72rem;font-weight:600;color:${st.color};border:1px solid ${st.color};border-radius:999px;padding:0.2rem 0.65rem;white-space:nowrap;">${st.label}</span>
      </div>
      ${payoff.verdict ? `<p style="margin-top:0.75rem;font-size:0.88rem;color:hsl(var(--text-muted));">${payoff.verdict}</p>` : ""}
      ${scoreBlock}
      ${systemFinding}
      ${!payoff.system_finding && findings ? `<ul style="margin:0.75rem 0 0 1.1rem;padding:0;">${findings}</ul>` : ""}
      ${payoff.micro_action ? `
        <div style="margin-top:1rem;padding-top:1rem;border-top:1px solid hsl(var(--border));">
          <div style="font-size:0.68rem;letter-spacing:0.1em;text-transform:uppercase;color:hsl(var(--text-muted));margin-bottom:0.35rem;">If this is your constraint</div>
          <p style="font-size:0.88rem;line-height:1.6;">${payoff.micro_action}</p>
        </div>` : ""}
      ${payoff.confidence_note ? `<p style="margin-top:0.9rem;font-size:0.78rem;color:hsl(var(--text-muted));line-height:1.5;">${payoff.confidence_note}</p>` : ""}
      ${payoff.evidence_hint && !payoff.confidence_note ? `<p style="margin-top:0.9rem;font-size:0.78rem;color:hsl(var(--text-muted));line-height:1.5;">${payoff.evidence_hint}</p>` : ""}
    </div>`;
}

function fieldHtml(q, answers) {
  const v = answers[q.id] ?? "";
  if (q.type === "select") {
    const opts = q.options.map(o => `<option value="${o}" ${v === o ? "selected" : ""}>${o}</option>`).join("");
    return `<select class="input" data-q="${q.id}"><option value="">— Select —</option>${opts}</select>`;
  }
  if (q.type === "scale") {
    const min = q.min ?? 0;
    const max = q.max ?? 100;
    const unit = q.unit ?? "";
    const cur = v !== "" ? v : Math.round((min + max) / 2);
    return `<div style="display:flex;align-items:center;gap:0.75rem;">
      <input class="input" type="range" data-q="${q.id}" min="${min}" max="${max}" value="${cur}" style="flex:1;">
      <span data-scale-val="${q.id}" style="min-width:3rem;font-variant-numeric:tabular-nums;font-weight:600;">${cur}${unit}</span>
    </div>`;
  }
  if (q.type === "number") {
    return `<input class="input" type="number" data-q="${q.id}" value="${v}" placeholder="—" min="0">`;
  }
  return `<textarea class="input" data-q="${q.id}" rows="2" placeholder="In your own words…">${v}</textarea>`;
}

function collectAnswers(container) {
  const payload = {};
  container.querySelectorAll("[data-q]").forEach(el => { payload[el.dataset.q] = el.value; });
  return payload;
}

// Revenue Diagnostic Instrument — one Business System at a time, payoff after each block.

export async function renderAudit(container, startModuleId = null) {
  container.innerHTML = `<div style="display:flex;justify-content:center;align-items:center;height:50vh;"><span style="color:hsl(var(--text-muted));font-size:0.9rem;">Loading diagnostic…</span></div>`;

  let state;
  try {
    state = await API.get("/intelligence/audit/modules");
  } catch (e) {
    container.innerHTML = `<div class="card" style="max-width:640px;margin:3rem auto;">Could not load audit: ${e.message}</div>`;
    return;
  }

  let activeId = startModuleId || state.current_module || state.modules[0]?.id;
  let showingPayoff = false;
  let lastPayoff = null;

  const render = () => {
    const mod = state.modules.find(m => m.id === activeId) || state.modules[0];
    const idx = state.modules.findIndex(m => m.id === mod.id);
    const answers = state.answers || {};
    const pct = Math.round((state.systems_complete / state.systems_total) * 100);

    const stepper = state.modules.map((m, i) => {
      const done = m.progress.complete;
      const active = m.id === mod.id;
      const dot = done ? "✓" : String(i + 1);
      return `<button type="button" data-goto="${m.id}" style="display:flex;align-items:center;gap:0.4rem;background:none;border:none;cursor:pointer;padding:0.25rem 0.5rem;opacity:${active ? 1 : 0.55};">
        <span style="width:1.4rem;height:1.4rem;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:0.7rem;font-weight:600;border:1px solid ${done ? "hsl(var(--success))" : active ? "hsl(var(--primary))" : "hsl(var(--border))"};color:${done ? "hsl(var(--success))" : "inherit"};">${dot}</span>
        <span style="font-size:0.72rem;max-width:5rem;text-align:left;line-height:1.2;">${m.title.replace(" System", "").replace(" & Monetization", "")}</span>
      </button>`;
    }).join("");

    const questions = mod.questions.map(q => `
      <label style="display:block;margin-bottom:1rem;">
        <span style="display:block;font-size:0.85rem;margin-bottom:0.35rem;">${q.label}</span>
        ${fieldHtml(q, answers)}
      </label>`).join("");

    container.innerHTML = `
      <div style="max-width:720px;margin:0 auto;">
        <div style="padding:2rem 0 1rem;">
          <div style="font-size:0.7rem;letter-spacing:0.14em;text-transform:uppercase;color:hsl(var(--text-muted));margin-bottom:0.5rem;">Revenue Diagnostic</div>
          <h1 style="font-size:1.65rem;font-weight:600;">One system at a time.</h1>
          <p style="color:hsl(var(--text-muted));margin-top:0.5rem;line-height:1.6;max-width:52ch;font-size:0.9rem;">
            ${state.systems_complete} of ${state.systems_total} systems examined.
            You see findings after each block — not only at the end.
          </p>
          <div style="margin-top:1rem;height:4px;background:hsl(var(--border));border-radius:2px;overflow:hidden;">
            <div style="height:100%;width:${pct}%;background:hsl(var(--primary));transition:width 0.4s;"></div>
          </div>
        </div>

        <div style="display:flex;gap:0.25rem;flex-wrap:wrap;padding-bottom:1.5rem;border-bottom:1px solid hsl(var(--border));">${stepper}</div>

        <section style="padding:2rem 0;">
          <div style="font-size:0.68rem;letter-spacing:0.12em;text-transform:uppercase;color:hsl(var(--primary));margin-bottom:0.35rem;">System ${idx + 1} of ${state.modules.length}</div>
          <h2 style="font-size:1.25rem;font-weight:600;margin-bottom:0.35rem;">${mod.title}</h2>
          <p style="font-size:0.88rem;color:hsl(var(--text-muted));line-height:1.55;margin-bottom:1.5rem;">${mod.hook}</p>

          ${showingPayoff && lastPayoff ? renderPayoff(lastPayoff) : `
            <div style="display:grid;gap:0.25rem;">${questions}</div>
            ${mod.evidence_hint ? `<p style="margin-top:1rem;font-size:0.78rem;color:hsl(var(--text-muted));line-height:1.5;">💡 ${mod.evidence_hint}</p>` : ""}
          `}
        </section>

        <div style="padding:0 0 3rem;display:flex;gap:0.75rem;align-items:center;flex-wrap:wrap;">
          ${showingPayoff ? `
            <button class="btn btn-primary" id="audit-next">${idx < state.modules.length - 1 ? "Next system →" : "View full diagnosis →"}</button>
            <button class="btn btn-secondary" id="audit-edit">Edit answers</button>
          ` : `
            <button class="btn btn-primary" id="audit-save">${idx < state.modules.length - 1 ? "Save & see finding" : "Finish & diagnose"}</button>
            ${idx > 0 ? `<button class="btn btn-secondary" id="audit-back">← Previous</button>` : ""}
          `}
          <span style="font-size:0.78rem;color:hsl(var(--text-muted));">${mod.progress.answered}/${mod.progress.total} in this system</span>
        </div>
      </div>`;

    container.querySelectorAll('input[type="range"][data-q]').forEach(slider => {
      const out = container.querySelector(`[data-scale-val="${slider.dataset.q}"]`);
      const unit = state.modules.flatMap(m => m.questions).find(q => q.id === slider.dataset.q)?.unit ?? "";
      const sync = () => { if (out) out.textContent = `${slider.value}${unit}`; };
      slider.addEventListener("input", sync);
      sync();
    });

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