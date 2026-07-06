import { API } from "../api.js";

// Executive Diagnosis — editorial, calm, evidence-first.
// Every number is computed by the constraint engine from the founder's
// own audit answers. Nothing on this screen is fabricated.

function scoreColor(s) {
  if (s >= 75) return "hsl(var(--success))";
  if (s >= 55) return "hsl(38 92% 50%)";
  return "hsl(var(--danger, 0 84% 60%))";
}
const fmtINR = (n) => "₹" + Number(n).toLocaleString("en-IN");
const L = `style="font-size:0.7rem;letter-spacing:0.14em;text-transform:uppercase;color:hsl(var(--text-muted));margin-bottom:0.5rem;"`;

export async function renderHealth(container) {
  container.innerHTML = `<div style="display:flex;justify-content:center;align-items:center;height:50vh;"><span style="color:hsl(var(--text-muted));font-size:0.9rem;">Computing diagnosis from your evidence…</span></div>`;

  let h;
  try { h = await API.get("/intelligence/health"); }
  catch (e) {
    container.innerHTML = `<div class="card" style="max-width:640px;margin:3rem auto;">Could not load diagnosis: ${e.message}</div>`;
    return;
  }

  // ---- Not enough evidence: honest empty state --------------------------
  if (!h.sufficient) {
    const missing = (h.missing_summary || []).map(m => `<li style="margin:0.35rem 0;">${m}</li>`).join("");
    const openQs = (h.open_questions || []).map((q, i) => `<li style="margin:0.5rem 0;line-height:1.5;">${q}</li>`).join("");
    container.innerHTML = `
      <div style="max-width:680px;margin:0 auto;padding-top:7vh;">
        <div ${L}>Executive Diagnosis</div>
        <h1 style="font-size:2rem;font-weight:600;margin-bottom:1rem;">Not enough evidence.</h1>
        <p style="color:hsl(var(--text-muted));line-height:1.7;max-width:52ch;">
          AFK diagnoses from evidence, and it will not guess. The Revenue Audit is
          <strong>${Math.round((h.completeness || 0) * 100)}% complete</strong>. Weakest-covered areas:
        </p>
        <ul style="color:hsl(var(--text-muted));margin:1rem 0 1.5rem 1.2rem;line-height:1.6;">${missing}</ul>
        ${openQs ? `<div ${L}>Before I can diagnose, I'd like to know</div><ol style="margin:0.5rem 0 2rem 1.2rem;">${openQs}</ol>` : ""}
        <a href="#audit" class="btn btn-primary">Continue the Revenue Audit →</a>
      </div>`;
    return;
  }

  const pc = h.primary_constraint;
  const st = h.evidence_stats || {};
  const rec = h.recommendation;
  const ch = h.changes;

  // ---- What changed since last diagnosis --------------------------------
  let changesBlock = "";
  if (ch && (ch.score_delta !== 0 || ch.improved.length || ch.declined.length)) {
    const sign = ch.score_delta > 0 ? "+" : "";
    const deltaColor = ch.score_delta > 0 ? "hsl(var(--success))" : (ch.score_delta < 0 ? "hsl(var(--danger,0 84% 60%))" : "inherit");
    const imp = ch.improved.map(x => `<li style="margin:0.25rem 0;">↑ ${x.dimension} <span style="color:hsl(var(--text-muted));">(+${x.delta})</span></li>`).join("");
    const dec = ch.declined.map(x => `<li style="margin:0.25rem 0;">↓ ${x.dimension} <span style="color:hsl(var(--text-muted));">(${x.delta})</span></li>`).join("");
    changesBlock = `
      <div style="padding:1.25rem 1.5rem;border:1px solid hsl(var(--border));border-radius:12px;margin:1.5rem 0 0;">
        <div ${L}>Since your last diagnosis</div>
        <div style="display:flex;gap:2.5rem;flex-wrap:wrap;align-items:flex-start;">
          <div><span style="font-size:1.9rem;font-weight:650;color:${deltaColor};">${sign}${ch.score_delta}</span>
            <div style="font-size:0.75rem;color:hsl(var(--text-muted));">Revenue Health (was ${ch.previous_score})</div></div>
          ${imp ? `<div><div style="font-size:0.75rem;color:hsl(var(--text-muted));margin-bottom:0.3rem;">Improved</div><ul style="list-style:none;font-size:0.85rem;">${imp}</ul></div>` : ""}
          ${dec ? `<div><div style="font-size:0.75rem;color:hsl(var(--text-muted));margin-bottom:0.3rem;">New pressure</div><ul style="list-style:none;font-size:0.85rem;">${dec}</ul></div>` : ""}
          ${ch.constraint_changed ? `<div style="font-size:0.85rem;color:hsl(var(--text-muted));max-width:24ch;">Primary constraint moved:<br><strong style="color:hsl(var(--text));">${ch.previous_constraint} → ${pc.label}</strong></div>` : ""}
        </div>
      </div>`;
  }

  // ---- Evidence provenance ----------------------------------------------
  const provenance = `
    <div style="display:flex;gap:2rem;flex-wrap:wrap;padding:1rem 0 0;">
      ${[[st.total_points, "Evidence points"], [st.audit_answers, "Audit answers"],
         [st.evidence_citations, "Evidence citations"], [st.dimensions_analyzed + "/" + st.dimensions_total, "Dimensions analyzed"]]
        .map(([v, l]) => `<div><div style="font-size:1.15rem;font-weight:650;font-variant-numeric:tabular-nums;">${v}</div><div style="font-size:0.72rem;color:hsl(var(--text-muted));">${l}</div></div>`).join("")}
    </div>`;

  // ---- Confidence breakdown ----------------------------------------------
  const analyzed = h.dimensions.filter(d => d.score !== null).map(d => `<li style="margin:0.25rem 0;">✓ ${d.label}</li>`).join("");
  const notAnalyzed = h.dimensions.filter(d => d.score === null).map(d => `<li style="margin:0.25rem 0;color:hsl(var(--text-muted));">• ${d.label}</li>`).join("");
  const futureEvidence = `<li style="margin:0.25rem 0;color:hsl(var(--text-muted));">• CRM records <span style="font-size:0.72rem;">(arrives in Evidence Engine)</span></li>
                          <li style="margin:0.25rem 0;color:hsl(var(--text-muted));">• Financial data <span style="font-size:0.72rem;">(arrives in Evidence Engine)</span></li>`;

  // ---- Findings with evidence chips ---------------------------------------
  const findings = (pc.findings || []).map(f => {
    const ev = (f.evidence || []).map(e =>
      `<span style="display:inline-block;background:hsl(var(--bg-subtle,220 14% 14%));border:1px solid hsl(var(--border));border-radius:6px;padding:0.15rem 0.5rem;font-size:0.75rem;margin:0.2rem 0.3rem 0 0;color:hsl(var(--text-muted));">${e.question}: <strong style="color:hsl(var(--text));">${e.answer}</strong></span>`).join("");
    return `<div style="padding:1rem 0;border-bottom:1px solid hsl(var(--border));"><div style="line-height:1.65;">${f.reasoning}</div><div style="margin-top:0.4rem;">${ev}</div></div>`;
  }).join("");

  // ---- Recommendation trust card ------------------------------------------
  const recCard = rec ? `
    <div style="border:1px solid hsl(var(--border));border-radius:12px;padding:1.5rem;margin:0.5rem 0 0;">
      <div ${L}>Recommendation</div>
      <div style="font-size:1.1rem;font-weight:600;margin-bottom:0.6rem;">${rec.constraint}: next best action</div>
      <p style="line-height:1.7;max-width:64ch;">${rec.action}</p>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1.25rem;margin-top:1.25rem;padding-top:1.25rem;border-top:1px solid hsl(var(--border));">
        <div><div ${L}>Why</div><div style="font-size:0.85rem;line-height:1.55;">${rec.why}</div></div>
        <div><div ${L}>Confidence</div><div style="font-size:1.3rem;font-weight:650;">${rec.confidence_pct}%</div><div style="font-size:0.72rem;color:hsl(var(--text-muted));line-height:1.5;">${rec.confidence_basis}</div></div>
        <div><div ${L}>Expected impact</div><div style="font-size:1.3rem;font-weight:650;">${rec.expected_impact}</div></div>
      </div>
      <div style="margin-top:1rem;"><div ${L}>Assumptions</div><div style="font-size:0.8rem;color:hsl(var(--text-muted));line-height:1.55;max-width:70ch;">${rec.assumptions}</div></div>
    </div>` : "";

  // ---- Open questions -------------------------------------------------------
  const openQs = (h.open_questions || []).length ? `
    <div style="padding:2rem 0;border-bottom:1px solid hsl(var(--border));">
      <div ${L}>Questions AFK still has</div>
      <p style="font-size:0.85rem;color:hsl(var(--text-muted));margin-bottom:0.75rem;">Before I become more confident, I'd like to know:</p>
      <ol style="margin-left:1.2rem;line-height:1.9;max-width:68ch;">${h.open_questions.map(q => `<li>${q}</li>`).join("")}</ol>
    </div>` : "";

  // ---- Dimension bars ---------------------------------------------------------
  const dims = h.dimensions.map(d => {
    const val = d.score === null
      ? `<span style="color:hsl(var(--text-muted));font-size:0.8rem;">Not enough evidence</span>`
      : `<div style="display:flex;align-items:center;gap:0.75rem;">
           <div style="flex:1;height:4px;background:hsl(var(--border));border-radius:2px;overflow:hidden;"><div style="width:${d.score}%;height:100%;background:${scoreColor(d.score)};"></div></div>
           <span style="font-variant-numeric:tabular-nums;font-weight:600;min-width:2.5rem;text-align:right;">${d.score}</span></div>`;
    return `<div style="display:grid;grid-template-columns:200px 1fr auto;gap:1rem;align-items:center;padding:0.85rem 0;border-bottom:1px solid hsl(var(--border));">
      <div style="font-size:0.9rem;">${d.label}</div><div>${val}</div>
      <div style="font-size:0.75rem;color:hsl(var(--text-muted));">conf ${Math.round(d.confidence * 100)}%</div></div>`;
  }).join("");

  const opp = h.revenue_opportunity ? `
    <div><div ${L}>Revenue Opportunity</div>
      <div style="font-size:1.6rem;font-weight:650;">${fmtINR(h.revenue_opportunity.amount)}<span style="font-size:0.85rem;color:hsl(var(--text-muted));font-weight:400;"> / yr</span></div>
      <div style="font-size:0.72rem;color:hsl(var(--text-muted));max-width:26ch;line-height:1.5;margin-top:0.3rem;">${h.revenue_opportunity.basis}</div></div>` : "";

  container.innerHTML = `
    <div style="max-width:880px;margin:0 auto;">
      <div style="padding:2.5rem 0 1.75rem;border-bottom:1px solid hsl(var(--border));">
        <div ${L}>Executive Diagnosis</div>
        <div style="display:flex;align-items:baseline;gap:1.25rem;flex-wrap:wrap;">
          <span style="font-size:4.5rem;font-weight:650;letter-spacing:-0.03em;line-height:1;color:${scoreColor(h.health_score)};">${h.health_score}</span>
          <span style="font-size:1.1rem;color:hsl(var(--text-muted));">Revenue Health / 100 · ${h.risk_level}</span>
        </div>
        ${provenance}
        ${changesBlock}
      </div>

      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:2rem;padding:2rem 0;border-bottom:1px solid hsl(var(--border));">
        <div><div ${L}>Primary Constraint</div>
          <div style="font-size:1.15rem;font-weight:600;">${pc.label}</div>
          <div style="font-size:0.8rem;color:hsl(var(--text-muted));margin-top:0.3rem;">Dimension score ${pc.score}/100</div></div>
        <div><div ${L}>Diagnosis Confidence</div>
          <div style="font-size:1.6rem;font-weight:650;">${Math.round(h.confidence * 100)}%</div>
          <div style="font-size:0.72rem;color:hsl(var(--text-muted));margin-top:0.3rem;">Computed from evidence — rises as data arrives</div></div>
        ${opp}
      </div>

      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:2rem;padding:1.5rem 0 2rem;border-bottom:1px solid hsl(var(--border));">
        <div><div ${L}>We analyzed</div><ul style="list-style:none;font-size:0.9rem;">${analyzed}</ul></div>
        <div><div ${L}>Missing / future evidence</div><ul style="list-style:none;font-size:0.9rem;">${notAnalyzed}${futureEvidence}</ul></div>
      </div>

      <div style="padding:2rem 0;border-bottom:1px solid hsl(var(--border));">${recCard}</div>

      ${(h.contradictions || []).length ? `
      <div style="padding:2rem 0;border-bottom:1px solid hsl(var(--border));">
        <div ${L}>Founder belief vs business reality</div>
        <p style="font-size:0.85rem;color:hsl(var(--text-muted));margin-bottom:1rem;max-width:64ch;">Where the uploaded evidence disagrees with the audit answers. Not accusations — comparisons worth examining.</p>
        ${h.contradictions.map(c => `
          <div style="border:1px solid ${c.severity === "significant" ? "hsl(38 92% 50% / 0.5)" : "hsl(var(--border))"};border-radius:12px;padding:1.25rem;margin-bottom:1rem;">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.25rem;margin-bottom:0.9rem;">
              <div><div ${L}>You said</div><div style="font-size:0.95rem;">"${c.belief.answer}"<div style="font-size:0.72rem;color:hsl(var(--text-muted));margin-top:0.2rem;">${c.belief.question}</div></div></div>
              <div><div ${L}>The evidence shows</div><div style="font-size:0.95rem;font-weight:600;">${c.evidence.value}${c.evidence.metric.includes("pct") || c.evidence.metric.includes("rate") ? "%" : ""}</div><div style="font-size:0.72rem;color:hsl(var(--text-muted));margin-top:0.2rem;">${c.evidence.basis}</div></div>
            </div>
            <p style="font-size:0.88rem;line-height:1.6;">${c.explanation}</p>
            <p style="font-size:0.82rem;line-height:1.6;color:hsl(var(--text-muted));margin-top:0.6rem;font-style:italic;">${c.follow_up_question}</p>
          </div>`).join("")}
      </div>` : ""}

      ${(h.revenue_drivers || []).length ? `
      <div style="padding:2rem 0;border-bottom:1px solid hsl(var(--border));">
        <div ${L}>What's working</div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;">
          ${h.revenue_drivers.map(d => `
            <div style="border:1px solid hsl(var(--border));border-radius:10px;padding:1rem;">
              <div style="font-size:0.72rem;color:hsl(var(--text-muted));margin-bottom:0.3rem;">${d.label}</div>
              <div style="font-weight:600;">${d.value}</div>
              <div style="font-size:0.7rem;color:hsl(var(--text-muted));margin-top:0.35rem;line-height:1.45;">${d.basis}</div>
            </div>`).join("")}
        </div>
      </div>` : ""}

      ${h.confidence_breakdown ? `
      <div style="padding:2rem 0;border-bottom:1px solid hsl(var(--border));">
        <div ${L}>Where confidence comes from</div>
        ${Object.entries(h.confidence_breakdown.sources).map(([name, src]) => `
          <div style="display:grid;grid-template-columns:160px 1fr auto;gap:1rem;align-items:center;padding:0.6rem 0;border-bottom:1px solid hsl(var(--border));">
            <span style="font-size:0.9rem;">${name}</span>
            <div style="height:4px;background:hsl(var(--border));border-radius:2px;overflow:hidden;">
              <div style="width:${src.coverage_pct}%;height:100%;background:${src.missing ? "transparent" : "hsl(var(--primary))"};"></div>
            </div>
            <span style="font-size:0.75rem;color:hsl(var(--text-muted));">${src.missing ? "Missing" : (src.rows ? src.rows + " rows" + (src.quality_pct ? " · quality " + src.quality_pct + "%" : "") : (src.weight || src.coverage_pct + "%"))}</span>
          </div>`).join("")}
        <p style="font-size:0.72rem;color:hsl(var(--text-muted));margin-top:0.9rem;line-height:1.55;max-width:70ch;">${h.confidence_breakdown.method}</p>
      </div>` : ""}

      ${(h.missing_evidence || []).some(m => !m.covered) ? `
      <div style="padding:2rem 0;border-bottom:1px solid hsl(var(--border));">
        <div ${L}>Evidence that would sharpen this diagnosis</div>
        ${h.missing_evidence.filter(m => !m.covered && m.suggestion).map(m => `
          <div style="padding:0.6rem 0;border-bottom:1px solid hsl(var(--border));">
            <span style="font-weight:600;font-size:0.88rem;">${m.dimension}:</span>
            <span style="font-size:0.85rem;color:hsl(var(--text-muted));"> ${m.suggestion}</span>
          </div>`).join("")}
        <a href="#evidence" class="btn btn-secondary btn-sm" style="margin-top:1rem;">Upload evidence →</a>
      </div>` : ""}

      <div style="padding:2rem 0;border-bottom:1px solid hsl(var(--border));">
        <div ${L}>Why AFK believes this</div>
        ${findings || '<p style="color:hsl(var(--text-muted));">No penalizing findings in the primary constraint dimension.</p>'}
      </div>

      ${openQs}

      <div style="padding:2rem 0 3rem;">
        <div ${L}>All dimensions</div>
        ${dims}
        <p style="font-size:0.75rem;color:hsl(var(--text-muted));line-height:1.6;margin-top:1.25rem;max-width:70ch;">${h.method_note}</p>
      </div>
    </div>`;
}
