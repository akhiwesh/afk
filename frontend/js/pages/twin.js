import { API } from "../api.js";

// Business Twin — the structured understanding of the company.
// Explicitly NOT AI output: it restates the founder's own evidence.

export async function renderTwin(container) {
  container.innerHTML = `<div style="display:flex;justify-content:center;align-items:center;height:50vh;"><span style="color:hsl(var(--text-muted));font-size:0.9rem;">Loading business twin…</span></div>`;

  let t, timeline = [], trajectory = null;
  try {
    [t, timeline, trajectory] = await Promise.all([
      API.get("/intelligence/twin"),
      API.get("/intelligence/memory/timeline"),
      API.get("/intelligence/trajectory").catch(() => null),
    ]);
  }
  catch (e) {
    container.innerHTML = `<div class="card" style="max-width:640px;margin:3rem auto;">Could not load twin: ${e.message}</div>`;
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
    <div style="display:grid;grid-template-columns:220px 1fr;gap:1rem;padding:0.8rem 0;border-bottom:1px solid hsl(var(--border));">
      <span style="font-size:0.85rem;color:hsl(var(--text-muted));">${k}</span>
      <span style="font-weight:${v ? 500 : 400};color:${v ? "inherit" : "hsl(var(--text-muted))"};">${v ?? "Not provided"}</span>
    </div>`).join("");

  const list = (items, empty) => items && items.length
    ? items.map(c => `<li style="margin:0.4rem 0;">${c.dimension} <span style="color:hsl(var(--text-muted));font-size:0.8rem;">(${c.score}/100)</span></li>`).join("")
    : `<li style="color:hsl(var(--text-muted));">${empty}</li>`;

  container.innerHTML = `
    <div style="max-width:880px;margin:0 auto;">
      <div style="padding:2.5rem 0 1.5rem;border-bottom:1px solid hsl(var(--border));">
        <div style="font-size:0.7rem;letter-spacing:0.14em;text-transform:uppercase;color:hsl(var(--text-muted));margin-bottom:0.5rem;">Business Twin</div>
        <h1 style="font-size:1.8rem;font-weight:600;">The structured understanding of this company.</h1>
        <p style="color:hsl(var(--text-muted));margin-top:0.5rem;font-size:0.9rem;">
          Built from your audit answers — not AI output. Profile ${Math.round((t.completeness || 0) * 100)}% complete
          (${t.fields_answered}/${t.fields_total} fields).
        </p>
      </div>
      ${t.narrative ? `
      <div style="padding:1.75rem 0;border-bottom:1px solid hsl(var(--border));">
        <div style="font-size:0.7rem;letter-spacing:0.14em;text-transform:uppercase;color:hsl(var(--text-muted));margin-bottom:0.7rem;">Business Summary</div>
        <p style="font-size:1.05rem;line-height:1.8;max-width:68ch;">${t.narrative}</p>
      </div>` : ''}

      ${t.dna ? `
      <div style="padding:1.75rem 0;border-bottom:1px solid hsl(var(--border));">
        <div style="font-size:0.7rem;letter-spacing:0.14em;text-transform:uppercase;color:hsl(var(--text-muted));margin-bottom:1rem;">Business DNA</div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem;">
          ${t.dna.map(d => `
            <div style="border:1px solid hsl(var(--border));border-radius:10px;padding:0.9rem 1rem;" title="${d.source ? 'Derived from: ' + d.source : ''}">
              <div style="font-size:0.68rem;letter-spacing:0.1em;text-transform:uppercase;color:hsl(var(--text-muted));margin-bottom:0.35rem;">${d.label}</div>
              <div style="font-weight:${d.known ? 600 : 400};font-size:${d.known ? '0.95rem' : '0.78rem'};color:${d.known ? 'inherit' : 'hsl(var(--text-muted))'};">${d.value}</div>
            </div>`).join('')}
        </div>
      </div>` : ''}

      ${t.narrative ? `
      <div style="padding:1.75rem 0 0.5rem;">
        <div style="font-size:0.7rem;letter-spacing:0.14em;text-transform:uppercase;color:hsl(var(--text-muted));margin-bottom:0.6rem;">Business Summary</div>
        <p style="font-size:1.05rem;line-height:1.8;max-width:66ch;">${t.narrative}</p>
      </div>` : ""}
      ${t.dna ? `
      <div style="padding:1.75rem 0;border-bottom:1px solid hsl(var(--border));">
        <div style="font-size:0.7rem;letter-spacing:0.14em;text-transform:uppercase;color:hsl(var(--text-muted));margin-bottom:0.9rem;">Business DNA</div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:1rem;">
          ${t.dna.map(d => `
            <div style="border:1px solid hsl(var(--border));border-radius:10px;padding:0.9rem 1rem;">
              <div style="font-size:0.68rem;letter-spacing:0.1em;text-transform:uppercase;color:hsl(var(--text-muted));margin-bottom:0.35rem;">${d.label}</div>
              <div style="font-weight:${d.known ? 600 : 400};font-size:0.95rem;color:${d.known ? "inherit" : "hsl(var(--text-muted))"};line-height:1.35;">${d.value}</div>
              ${d.source ? `<div style="font-size:0.68rem;color:hsl(var(--text-muted));margin-top:0.35rem;">from: ${d.source}</div>` : ""}
            </div>`).join("")}
        </div>
      </div>` : ""}
      <div style="padding:1.5rem 0;">${rows}</div>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:2rem;padding:1rem 0 2rem;">
        <div>
          <h3 style="font-size:0.9rem;font-weight:600;margin-bottom:0.5rem;">Current constraints</h3>
          <ul style="margin-left:1.1rem;line-height:1.6;">${list(t.constraints, "None identified yet — complete more of the audit.")}</ul>
        </div>
        <div>
          <h3 style="font-size:0.9rem;font-weight:600;margin-bottom:0.5rem;">Current strengths</h3>
          <ul style="margin-left:1.1rem;line-height:1.6;">${list(t.strengths, "None confirmed yet — needs more evidence.")}</ul>
        </div>
      </div>
      ${trajectory?.sufficient ? `
      <div style="padding:1.5rem;border:1px solid hsl(var(--border));border-radius:10px;margin-bottom:2rem;">
        <div style="font-size:0.7rem;letter-spacing:0.14em;text-transform:uppercase;color:hsl(var(--text-muted));margin-bottom:0.6rem;">Diagnosis trajectory</div>
        <div style="display:flex;gap:2rem;flex-wrap:wrap;margin-bottom:0.75rem;">
          <div><span style="font-size:1.5rem;font-weight:650;">${trajectory.health_delta > 0 ? "+" : ""}${trajectory.health_delta}</span>
            <div style="font-size:0.72rem;color:hsl(var(--text-muted));">Health ${trajectory.health_from} → ${trajectory.health_to}</div></div>
          ${trajectory.constraint_changed ? `<div style="font-size:0.85rem;">Constraint: ${trajectory.constraint_from} → <strong>${trajectory.constraint_to}</strong></div>` : ""}
        </div>
        <p style="font-size:0.88rem;line-height:1.6;color:hsl(var(--text-muted));">${trajectory.interpretation}</p>
      </div>` : ""}
      ${t.self_diagnosis ? `
      <div style="padding:1.5rem;border:1px solid hsl(var(--border));border-radius:10px;margin-bottom:3rem;">
        <div style="font-size:0.7rem;letter-spacing:0.14em;text-transform:uppercase;color:hsl(var(--text-muted));margin-bottom:0.6rem;">In the founder's own words</div>
        <p style="line-height:1.7;">“${t.self_diagnosis}”</p>
        ${t.biggest_worry ? `<p style="line-height:1.7;color:hsl(var(--text-muted));margin-top:0.6rem;">Biggest worry: “${t.biggest_worry}”</p>` : ""}
      </div>` : ""}
      ${timeline.length ? `
      <div style="padding:1rem 0 3rem;">
        <div style="font-size:0.7rem;letter-spacing:0.14em;text-transform:uppercase;color:hsl(var(--text-muted));margin-bottom:1rem;">Business Memory</div>
        <div style="display:flex;gap:0.75rem;margin-bottom:1.5rem;flex-wrap:wrap;">
          <div style="flex:1;min-width:140px;border:1px solid hsl(var(--border));border-radius:10px;padding:0.75rem 1rem;">
            <div style="font-size:0.72rem;color:hsl(var(--text-muted));">Events on record</div>
            <div style="font-size:1.4rem;font-weight:650;">${timeline.length}</div>
          </div>
          <div style="flex:1;min-width:140px;border:1px solid hsl(var(--border));border-radius:10px;padding:0.75rem 1rem;">
            <div style="font-size:0.72rem;color:hsl(var(--text-muted));">Diagnoses computed</div>
            <div style="font-size:1.4rem;font-weight:650;">${timeline.filter(e=>e.type==="diagnosis_computed").length}</div>
          </div>
          <div style="flex:1;min-width:140px;border:1px solid hsl(var(--border));border-radius:10px;padding:0.75rem 1rem;">
            <div style="font-size:0.72rem;color:hsl(var(--text-muted));">Evidence added</div>
            <div style="font-size:1.4rem;font-weight:650;">${timeline.filter(e=>e.type==="evidence_added").length}</div>
          </div>
        </div>
        <div style="position:relative;padding-left:1.5rem;border-left:2px solid hsl(var(--border));">
          ${timeline.map(ev => {
            const meta = {
              diagnosis_computed: {icon:"◆", color:"hsl(var(--primary))", badge:"Diagnosis"},
              evidence_added:     {icon:"▲", color:"hsl(var(--success))", badge:"Evidence"},
              evidence_removed:   {icon:"▽", color:"hsl(var(--text-muted))", badge:"Evidence removed"},
              audit_saved:        {icon:"●", color:"hsl(38 92% 55%)", badge:"Audit"},
            }[ev.type] || {icon:"○", color:"inherit", badge:ev.type};
            const d = new Date(ev.at);
            return `<div style="position:relative;padding:0 0 1.5rem 0.75rem;">
              <span style="position:absolute;left:-2.05rem;top:0.1rem;width:1rem;text-align:center;color:${meta.color};background:hsl(var(--bg,222 20% 7%));">${meta.icon}</span>
              <div style="font-size:0.72rem;color:hsl(var(--text-muted));">${d.toLocaleDateString("en-IN",{day:"numeric",month:"short",year:"numeric"})} · ${d.toLocaleTimeString("en-IN",{hour:"2-digit",minute:"2-digit"})}</div>
              <div style="font-size:0.92rem;line-height:1.55;margin:0.15rem 0 0.3rem;">${ev.summary}</div>
              <span style="display:inline-block;font-size:0.68rem;border:1px solid ${meta.color};color:${meta.color};border-radius:999px;padding:0.1rem 0.6rem;">${meta.badge}</span>
            </div>`;
          }).join("")}
        </div>
      </div>` : ""}
      <div style="padding:0 0 3rem;">
        <div style="border:1px solid hsl(var(--border));border-radius:12px;padding:1.25rem 1.5rem;">
          <div style="font-size:0.7rem;letter-spacing:0.14em;text-transform:uppercase;color:hsl(var(--text-muted));margin-bottom:0.5rem;">Contribute to AFK Science</div>
          <p style="font-size:0.88rem;color:hsl(var(--text-muted));line-height:1.6;max-width:64ch;">Add this business as an anonymized case study — no names, no exact revenue, no customer data. You review exactly what gets stored before approving.</p>
          <div id="case-zone" style="margin-top:0.9rem;">
            <button class="btn btn-secondary btn-sm" id="case-draft">Preview anonymized case</button>
          </div>
        </div>
      </div>
    </div>`;

  const zone = container.querySelector("#case-zone");
  container.querySelector("#case-draft")?.addEventListener("click", async () => {
    zone.innerHTML = `<span style="font-size:0.85rem;color:hsl(var(--text-muted));">Building anonymized draft…</span>`;
    try {
      const d = await API.post("/intelligence/cases/draft", {});
      const c = d.case;
      zone.innerHTML = `
        <pre style="font-size:0.72rem;line-height:1.5;background:hsl(var(--bg-subtle,220 14% 12%));border:1px solid hsl(var(--border));border-radius:8px;padding:1rem;overflow-x:auto;max-height:280px;overflow-y:auto;">${JSON.stringify(c, null, 2).replace(/</g,"&lt;")}</pre>
        <p style="font-size:0.78rem;color:hsl(var(--text-muted));margin:0.75rem 0;line-height:1.55;">${d.consent_text}</p>
        <div style="display:flex;gap:0.6rem;">
          <button class="btn btn-primary btn-sm" id="case-approve">Approve & contribute</button>
          <button class="btn btn-secondary btn-sm" id="case-cancel">Cancel</button>
        </div>`;
      zone.querySelector("#case-cancel").addEventListener("click", () => {
        zone.innerHTML = `<button class="btn btn-secondary btn-sm" id="case-redraft">Preview anonymized case</button>`;
        zone.querySelector("#case-redraft").addEventListener("click", () => window.location.reload());
      });
      zone.querySelector("#case-approve").addEventListener("click", async () => {
        try {
          const r = await API.post("/intelligence/cases/approve", { case: c, consent: true });
          zone.innerHTML = `<span style="font-size:0.9rem;color:hsl(var(--success));">Contributed as ${r.case_id}. This business is now part of AFK's scientific record.</span>`;
        } catch (e) {
          UI.toast(`Could not contribute: ${e.message}`, "error");
        }
      });
    } catch (e) {
      zone.innerHTML = `<span style="font-size:0.85rem;color:hsl(var(--danger,0 84% 60%));">${e.message}</span>`;
    }
  });
}
