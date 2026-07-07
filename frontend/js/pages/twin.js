import { API } from "../api.js";
import { UI } from "../ui.js";
import { sectionLabel } from "../diagnostic-ui.js";

export async function renderTwin(container) {
  container.innerHTML = `<div class="diag-page diag-page--embedded"><div class="diag-health-inner" style="padding:3rem 0;text-align:center;"><span class="diag-muted">Loading business twin…</span></div></div>`;

  let t, timeline = [], trajectory = null, outcomes = null;
  try {
    [t, timeline, trajectory, outcomes] = await Promise.all([
      API.get("/intelligence/twin"),
      API.get("/intelligence/memory/timeline"),
      API.get("/intelligence/trajectory").catch(() => null),
      API.get("/intelligence/outcomes").catch(() => null),
    ]);
  } catch (e) {
    container.innerHTML = `<div class="diag-page diag-page--embedded"><div class="diag-health-inner"><div class="diag-panel">Could not load twin: ${e.message}</div></div></div>`;
    return;
  }

  const p = t.profile || {};
  const rows = [
    ["Business type", p.business_type],
    ["Industry", p.industry],
    ["Growth stage", p.growth_stage],
    ["Team size", p.team_size],
    ["Revenue model", p.revenue_model],
    ["Monthly revenue", p.monthly_revenue ? "₹" + Number(p.monthly_revenue).toLocaleString("en-IN") : null],
    ["Average deal value", p.avg_deal_value ? "₹" + Number(p.avg_deal_value).toLocaleString("en-IN") : null],
    ["12-month target", p.revenue_goal_12m ? "₹" + Number(p.revenue_goal_12m).toLocaleString("en-IN") + " / mo" : null],
    ["Primary lead source", p.primary_lead_source],
    ["Sales motion", p.sales_motion ? `Founder involvement: ${p.sales_motion}` : null],
    ["Pricing posture", p.pricing_posture],
  ].map(([k, v]) => `
    <div style="display:grid;grid-template-columns:220px 1fr;gap:1rem;padding:0.8rem 0;border-bottom:1px solid #f1f5f9;">
      <span class="diag-muted" style="font-size:0.85rem;">${k}</span>
      <span style="font-weight:${v ? 500 : 400};" class="${v ? "" : "diag-muted"}">${v ?? "Not provided"}</span>
    </div>`).join("");

  const list = (items, empty) => items && items.length
    ? items.map(c => `<li style="margin:0.4rem 0;">${c.dimension} <span class="diag-muted" style="font-size:0.8rem;">(${c.score}/100)</span></li>`).join("")
    : `<li class="diag-muted">${empty}</li>`;

  const dnaBlock = t.dna ? `
    <div class="diag-block">
      ${sectionLabel("Business DNA")}
      <div class="diag-card-grid">
        ${t.dna.map(d => `
          <div class="diag-mini-card" title="${d.source ? "Derived from: " + d.source : ""}">
            <div class="diag-stat-label" style="margin-bottom:0.35rem;">${d.label}</div>
            <div style="font-weight:${d.known ? 600 : 400};font-size:${d.known ? "0.95rem" : "0.78rem"};" class="${d.known ? "" : "diag-muted"}">${d.value}</div>
            ${d.source ? `<div class="diag-stat-label" style="margin-top:0.35rem;">from: ${d.source}</div>` : ""}
          </div>`).join("")}
      </div>
    </div>` : "";

  container.innerHTML = `
    <div class="diag-page diag-page--embedded">
    <div class="diag-health-inner">
      <div class="diag-hero" style="margin-bottom:1.5rem;">
        <p class="diag-hero-kicker">Business Twin</p>
        <h1>The structured understanding of this company.</h1>
        <p>Built from your audit answers — not AI output. Profile ${Math.round((t.completeness || 0) * 100)}% complete (${t.fields_answered}/${t.fields_total} fields).</p>
      </div>

      ${t.narrative ? `
      <div class="diag-block">
        ${sectionLabel("Business Summary")}
        <p class="diag-section-body" style="font-size:1.05rem;max-width:68ch;">${t.narrative}</p>
      </div>` : ""}

      ${dnaBlock}

      <div class="diag-block">
        ${sectionLabel("Profile fields")}
        ${rows}
      </div>

      <div class="diag-stat-grid diag-block">
        <div>
          <div class="diag-section-label">Current constraints</div>
          <ul style="margin-left:1.1rem;line-height:1.6;">${list(t.constraints, "None identified yet — complete more of the audit.")}</ul>
        </div>
        <div>
          <div class="diag-section-label">Current strengths</div>
          <ul style="margin-left:1.1rem;line-height:1.6;">${list(t.strengths, "None confirmed yet — needs more evidence.")}</ul>
        </div>
      </div>

      ${outcomes?.summary?.total ? `
      <div class="diag-panel diag-block">
        ${sectionLabel(`Treatment outcomes · ${outcomes.protocol_id || "AFK-OUT-0001"}`)}
        <div class="diag-provenance" style="padding:0;margin-bottom:0.75rem;">
          <div><div class="diag-stat-val is-sm">${outcomes.summary.improved}</div><div class="diag-stat-label">improved</div></div>
          <div><div class="diag-stat-val is-sm">${outcomes.summary.active}</div><div class="diag-stat-label">in progress</div></div>
          <div><div class="diag-stat-val is-sm">${outcomes.summary.completed}</div><div class="diag-stat-label">completed</div></div>
        </div>
        <p class="diag-stat-label">${outcomes.summary.note || "Dimension score delta — not revenue claims."}</p>
      </div>` : ""}

      ${trajectory?.sufficient ? `
      <div class="diag-panel diag-block">
        ${sectionLabel("Diagnosis trajectory")}
        <div class="diag-provenance" style="padding:0;margin-bottom:0.75rem;">
          <div><div class="diag-stat-val is-sm">${trajectory.health_delta > 0 ? "+" : ""}${trajectory.health_delta}</div>
            <div class="diag-stat-label">Health ${trajectory.health_from} → ${trajectory.health_to}</div></div>
          ${trajectory.constraint_changed ? `<div class="diag-section-body">Constraint: ${trajectory.constraint_from} → <strong>${trajectory.constraint_to}</strong></div>` : ""}
        </div>
        <p class="diag-muted-sm">${trajectory.interpretation}</p>
      </div>` : ""}

      ${t.self_diagnosis ? `
      <div class="diag-panel diag-block">
        ${sectionLabel("In the founder's own words")}
        <p class="diag-section-body">"${t.self_diagnosis}"</p>
        ${t.biggest_worry ? `<p class="diag-muted-sm" style="margin-top:0.6rem;">Biggest worry: "${t.biggest_worry}"</p>` : ""}
      </div>` : ""}

      ${timeline.length ? `
      <div class="diag-block">
        ${sectionLabel("Business Memory")}
        <div class="diag-card-grid" style="margin-bottom:1.5rem;">
          <div class="diag-mini-card">
            <div class="diag-stat-label">Events on record</div>
            <div class="diag-stat-val is-sm">${timeline.length}</div>
          </div>
          <div class="diag-mini-card">
            <div class="diag-stat-label">Diagnoses computed</div>
            <div class="diag-stat-val is-sm">${timeline.filter(e => e.type === "diagnosis_computed").length}</div>
          </div>
          <div class="diag-mini-card">
            <div class="diag-stat-label">Evidence added</div>
            <div class="diag-stat-val is-sm">${timeline.filter(e => e.type === "evidence_added").length}</div>
          </div>
        </div>
        <div style="position:relative;padding-left:1.5rem;border-left:2px solid var(--diag-slate-200);">
          ${timeline.map(ev => {
            const meta = {
              diagnosis_computed: { icon: "◆", color: "var(--diag-amber-dark)", badge: "Diagnosis" },
              evidence_added: { icon: "▲", color: "#4c7a4a", badge: "Evidence" },
              evidence_removed: { icon: "▽", color: "var(--diag-slate-400)", badge: "Evidence removed" },
              audit_saved: { icon: "●", color: "#bd6b2e", badge: "Audit" },
            }[ev.type] || { icon: "○", color: "inherit", badge: ev.type };
            const d = new Date(ev.at);
            return `<div style="position:relative;padding:0 0 1.5rem 0.75rem;">
              <span style="position:absolute;left:-2.05rem;top:0.1rem;width:1rem;text-align:center;color:${meta.color};background:var(--diag-slate-50);">${meta.icon}</span>
              <div class="diag-stat-label">${d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })} · ${d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}</div>
              <div class="diag-section-body" style="margin:0.15rem 0 0.3rem;">${ev.summary}</div>
              <span class="diag-evidence is-medium" style="border-radius:999px;">${meta.badge}</span>
            </div>`;
          }).join("")}
        </div>
      </div>` : ""}

      <div class="diag-block">
        <div class="diag-panel">
          ${sectionLabel("Contribute to AFK Science")}
          <p class="diag-muted-sm" style="max-width:64ch;">Add this business as an anonymized case study — no names, no exact revenue, no customer data. You review exactly what gets stored before approving.</p>
          <div id="case-zone" style="margin-top:0.9rem;">
            <button class="diag-btn-secondary" id="case-draft">Preview anonymized case</button>
          </div>
        </div>
      </div>
    </div>
    </div>`;

  const zone = container.querySelector("#case-zone");
  container.querySelector("#case-draft")?.addEventListener("click", async () => {
    zone.innerHTML = `<span class="diag-muted" style="font-size:0.85rem;">Building anonymized draft…</span>`;
    try {
      const d = await API.post("/intelligence/cases/draft", {});
      const c = d.case;
      zone.innerHTML = `
        <pre style="font-size:0.72rem;line-height:1.5;background:#f8fafc;border:1px solid var(--diag-slate-200);border-radius:8px;padding:1rem;overflow-x:auto;max-height:280px;overflow-y:auto;">${JSON.stringify(c, null, 2).replace(/</g, "&lt;")}</pre>
        <p class="diag-stat-label" style="margin:0.75rem 0;line-height:1.55;">${d.consent_text}</p>
        <div style="display:flex;gap:0.6rem;">
          <button class="diag-btn-primary" id="case-approve">Approve & contribute</button>
          <button class="diag-btn-secondary" id="case-cancel">Cancel</button>
        </div>`;
      zone.querySelector("#case-cancel").addEventListener("click", () => {
        zone.innerHTML = `<button class="diag-btn-secondary" id="case-redraft">Preview anonymized case</button>`;
        zone.querySelector("#case-redraft").addEventListener("click", () => window.location.reload());
      });
      zone.querySelector("#case-approve").addEventListener("click", async () => {
        try {
          const r = await API.post("/intelligence/cases/approve", { case: c, consent: true });
          zone.innerHTML = `<span style="font-size:0.9rem;color:#4c7a4a;">Contributed as ${r.case_id}. This business is now part of AFK's scientific record.</span>`;
        } catch (e) {
          UI.toast(`Could not contribute: ${e.message}`, "error");
        }
      });
    } catch (e) {
      zone.innerHTML = `<span style="font-size:0.85rem;color:#b0452e;">${e.message}</span>`;
    }
  });
}