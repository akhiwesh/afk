import { API } from "../api.js";
import { renderGauge, ruleIdChip, scoreStatus, dimScoreColor, sectionLabel } from "../diagnostic-ui.js";

const fmtINR = (n) => "₹" + Number(n).toLocaleString("en-IN");

export async function renderHealth(container) {
  container.innerHTML = `<div class="diag-page diag-page--embedded"><div class="diag-health-inner" style="padding:3rem 0;text-align:center;"><span class="diag-muted">Computing diagnosis from your evidence…</span></div></div>`;

  let h, moat;
  try {
    h = await API.get("/intelligence/health");
    try { moat = await API.get("/knowledge/moat"); } catch { moat = null; }
  } catch (e) {
    container.innerHTML = `<div class="diag-page diag-page--embedded"><div class="diag-health-inner"><div class="diag-panel">Could not load diagnosis: ${e.message}</div></div></div>`;
    return;
  }

  if (!h.sufficient) {
    const missing = (h.missing_summary || []).map(m => `<li style="margin:0.35rem 0;">${m}</li>`).join("");
    const openQs = (h.open_questions || []).map(q => `<li style="margin:0.5rem 0;line-height:1.5;">${q}</li>`).join("");
    container.innerHTML = `
      <div class="diag-page diag-page--embedded">
        <div class="diag-health-inner diag-empty">
          ${sectionLabel("Executive Diagnosis")}
          <h1>Not enough evidence.</h1>
          <p class="diag-muted" style="line-height:1.7;max-width:52ch;">
            AFK diagnoses from evidence, and it will not guess. The Revenue Audit is
            <strong>${Math.round((h.completeness || 0) * 100)}% complete</strong>. Weakest-covered areas:
          </p>
          <ul class="diag-muted" style="margin:1rem 0 1.5rem 1.2rem;line-height:1.6;">${missing}</ul>
          ${openQs ? `${sectionLabel("Before I can diagnose, I'd like to know")}<ol style="margin:0.5rem 0 2rem 1.2rem;line-height:1.7;">${openQs}</ol>` : ""}
          <a href="#audit" class="diag-btn-primary" style="text-decoration:none;">Continue the Revenue Audit →</a>
        </div>
      </div>`;
    return;
  }

  const pc = h.primary_constraint;
  const st = h.evidence_stats || {};
  const rec = h.recommendation;
  const ch = h.changes;
  const hv = h.hypothesis_verdict;
  const fc = h.funnel_coherence;
  const compound = h.compound_findings || [];
  const epi = h.epistemic_confidence || h.confidence_breakdown;
  const ZONE_DELTA = { up: "#4c7a4a", down: "#b0452e" };

  let changesBlock = "";
  if (ch && (ch.score_delta !== 0 || ch.improved.length || ch.declined.length)) {
    const sign = ch.score_delta > 0 ? "+" : "";
    const deltaColor = ch.score_delta > 0 ? ZONE_DELTA.up : (ch.score_delta < 0 ? ZONE_DELTA.down : "inherit");
    const imp = ch.improved.map(x => `<li style="margin:0.25rem 0;">↑ ${x.dimension} <span class="diag-muted">(+${x.delta})</span></li>`).join("");
    const dec = ch.declined.map(x => `<li style="margin:0.25rem 0;">↓ ${x.dimension} <span class="diag-muted">(${x.delta})</span></li>`).join("");
    changesBlock = `
      <div class="diag-panel" style="margin-top:1rem;">
        ${sectionLabel("Since your last diagnosis")}
        <div style="display:flex;gap:2.5rem;flex-wrap:wrap;align-items:flex-start;">
          <div><span class="diag-stat-val is-lg" style="color:${deltaColor};">${sign}${ch.score_delta}</span>
            <div class="diag-stat-label">Revenue Health (was ${ch.previous_score})</div></div>
          ${imp ? `<div><div class="diag-stat-label" style="margin-bottom:0.3rem;">Improved</div><ul style="list-style:none;font-size:0.85rem;">${imp}</ul></div>` : ""}
          ${dec ? `<div><div class="diag-stat-label" style="margin-bottom:0.3rem;">New pressure</div><ul style="list-style:none;font-size:0.85rem;">${dec}</ul></div>` : ""}
          ${ch.constraint_changed ? `<div class="diag-muted-sm" style="max-width:24ch;">Primary constraint moved:<br><strong style="color:var(--diag-slate-800);">${ch.previous_constraint} → ${pc.label}</strong></div>` : ""}
        </div>
      </div>`;
  }

  const provenance = `
    <div class="diag-provenance">
      ${[[st.total_points, "Evidence points"], [st.audit_answers, "Audit answers"],
         [st.evidence_citations, "Evidence citations"], [st.dimensions_analyzed + "/" + st.dimensions_total, "Dimensions analyzed"]]
        .map(([v, l]) => `<div><div class="diag-provenance-val">${v}</div><div class="diag-stat-label">${l}</div></div>`).join("")}
    </div>`;

  const analyzed = h.dimensions.filter(d => d.score !== null).map(d => `<li style="margin:0.25rem 0;">✓ ${d.label}</li>`).join("");
  const notAnalyzed = h.dimensions.filter(d => d.score === null).map(d => `<li style="margin:0.25rem 0;" class="diag-muted">• ${d.label}</li>`).join("");
  const futureEvidence = `<li style="margin:0.25rem 0;" class="diag-muted">• CRM records <span style="font-size:0.72rem;">(arrives in Evidence Engine)</span></li>
                          <li style="margin:0.25rem 0;" class="diag-muted">• Financial data <span style="font-size:0.72rem;">(arrives in Evidence Engine)</span></li>`;

  const findings = (pc.findings || []).map(f => {
    const ruleChip = ruleIdChip(f.rule_id, f.rule_pack);
    const ev = (f.evidence || []).map(e =>
      `<span class="diag-ev-chip">${e.question}: <strong>${e.answer}</strong></span>`).join("");
    return `<div class="diag-finding-row">${ruleChip}${f.reasoning}<div style="margin-top:0.4rem;">${ev}</div></div>`;
  }).join("");

  const recCard = rec ? `
    <div class="diag-panel">
      ${sectionLabel("Recommendation")}
      <div style="font-size:1.1rem;font-weight:600;margin-bottom:0.6rem;">${rec.constraint}: next best action</div>
      <p class="diag-section-body" style="max-width:64ch;">${rec.action}</p>
      <div class="diag-stat-grid" style="margin-top:1.25rem;padding-top:1.25rem;border-top:1px solid #f1f5f9;">
        <div><div class="diag-section-label">Why</div><div class="diag-muted-sm">${rec.why}</div></div>
        <div><div class="diag-section-label">Confidence</div><div class="diag-stat-val is-sm">${rec.confidence_pct}%</div><div class="diag-stat-label">${rec.confidence_basis}</div></div>
        <div><div class="diag-section-label">Expected impact</div><div class="diag-stat-val is-sm">${rec.expected_impact}</div></div>
      </div>
      <div style="margin-top:1rem;"><div class="diag-section-label">Assumptions</div><div class="diag-muted-sm" style="max-width:70ch;">${rec.assumptions}</div></div>
    </div>` : "";

  const openQs = (h.open_questions || []).length ? `
    <div class="diag-block">
      ${sectionLabel("Questions AFK still has")}
      <p class="diag-muted-sm" style="margin-bottom:0.75rem;">Before I become more confident, I'd like to know:</p>
      <ol style="margin-left:1.2rem;line-height:1.9;max-width:68ch;">${h.open_questions.map(q => `<li>${q}</li>`).join("")}</ol>
    </div>` : "";

  const dims = h.dimensions.map(d => {
    const val = d.score === null
      ? `<span class="diag-muted" style="font-size:0.8rem;">Not enough evidence</span>`
      : `<div class="diag-score-row">
           <div class="diag-score-bar"><div style="width:${d.score}%;background:${dimScoreColor(d.score)};"></div></div>
           <span style="font-variant-numeric:tabular-nums;font-weight:600;min-width:2.5rem;text-align:right;">${d.score}</span></div>`;
    return `<div class="diag-row">
      <div class="diag-row-label">${d.label}</div><div>${val}</div>
      <div class="diag-stat-label">conf ${Math.round(d.confidence * 100)}%</div></div>`;
  }).join("");

  const opp = h.revenue_opportunity ? `
    <div>${sectionLabel("Revenue Opportunity")}
      <div class="diag-stat-val">${fmtINR(h.revenue_opportunity.amount)}<span style="font-size:0.85rem;font-weight:400;" class="diag-muted"> / yr</span></div>
      <div class="diag-stat-label" style="max-width:26ch;">${h.revenue_opportunity.basis}</div></div>` : "";

  const priAdj = h.priority_evidence_adjustments?.pricing || pc.priority?.evidence_adjustment;
  const priorityNote = pc.priority ? `
    <div class="diag-stat-label" style="margin-top:0.5rem;max-width:46ch;">
      Impact priority ${pc.priority.priority_score}
      (severity ${pc.priority.severity_index} × exposure ${pc.priority.effective_revenue_exposure ?? pc.priority.revenue_exposure} × fixability ${pc.priority.fixability}).
      ${pc.selection_method === "impact_priority_evidence_adjusted" && priAdj
        ? `Evidence adjusted pricing exposure — ${priAdj.basis}`
        : pc.overrides_lowest_score
          ? `Lowest score is ${pc.lowest_score_label} (${pc.lowest_score}/100) — ranked #1 by ₹ exposure, not raw severity.`
          : "Also the lowest dimension score — severity and impact agree."}
    </div>` : "";

  const hypothesisBlock = hv ? `
    <div class="diag-block">
      ${sectionLabel("Founder hypothesis vs measured constraint")}
      <div class="diag-panel ${hv.verdict === "contradicted" ? "is-warn" : ""}">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.25rem;margin-bottom:0.9rem;">
          <div><div class="diag-section-label">You said</div><div style="font-size:0.95rem;">"${hv.founder_hypothesis || "—"}"</div></div>
          <div><div class="diag-section-label">Verdict</div>
            <div style="font-size:0.95rem;font-weight:600;text-transform:capitalize;">${hv.verdict}</div>
            ${hv.inferred_belief_system ? `<div class="diag-stat-label" style="margin-top:0.2rem;">Mapped to ${hv.inferred_belief_system}</div>` : ""}
          </div>
        </div>
        <p class="diag-section-body">${hv.explanation}</p>
      </div>
    </div>` : "";

  const funnelBlock = fc ? `
    <div class="diag-block">
      ${sectionLabel("Funnel arithmetic check")}
      <div class="diag-panel is-warn">
        <div class="diag-stat-grid" style="gap:1.5rem;margin-bottom:0.75rem;">
          <div><div class="diag-section-label">Stated revenue</div><div style="font-weight:600;">${fmtINR(fc.stated_monthly_revenue)}/mo</div></div>
          <div><div class="diag-section-label">Funnel estimate</div><div style="font-weight:600;">${fmtINR(fc.theoretical_monthly_revenue)}/mo</div></div>
          <div><div class="diag-section-label">Ratio</div><div style="font-weight:600;">${fc.ratio}×</div></div>
        </div>
        <p class="diag-section-body">${fc.explanation}</p>
        <p class="diag-stat-label" style="margin-top:0.5rem;">${fc.basis}</p>
      </div>
    </div>` : "";

  const compoundBlock = compound.length ? `
    <div class="diag-block">
      ${sectionLabel("Cross-system interactions")}
      ${compound.map(c => `
        <div class="diag-finding-row">
          <div class="diag-stat-label" style="margin-bottom:0.3rem;">
            ${c.compound_id ? ruleIdChip(c.compound_id) : ""}${(c.systems || []).join(" + ")}
          </div>
          <div class="diag-section-body">${c.reasoning}</div>
        </div>`).join("")}
    </div>` : "";

  const epiMethod = epi?.method || "AFK-CFM-0001: questionnaire caps at 40%; uploaded evidence raises confidence.";
  const epiOverall = epi?.overall != null ? Math.round(epi.overall * 100) : Math.round(h.confidence * 100);

  const CHAIN_ORDER = ["demand", "qualification", "conversion", "pricing", "retention", "founder_dependency"];
  const chainDims = CHAIN_ORDER.map(k => h.dimensions.find(d => d.key === k)).filter(Boolean);
  const chainBlock = chainDims.length ? `
    <div class="diag-block">
      ${sectionLabel("Revenue engine chain")}
      <p class="diag-muted-sm" style="margin-bottom:1.25rem;max-width:68ch;">
        How money moves through your business — colored by constraint index. Left to right: leads → close → monetize → repeat.
      </p>
      <div class="diag-chain">
        ${chainDims.map((d, i) => {
          const sc = d.score;
          const bg = dimScoreColor(sc);
          const short = d.label.split(" ")[0];
          return `${i > 0 ? `<span class="diag-muted" style="font-size:0.75rem;">→</span>` : ""}
            <div class="diag-chain-node" title="${d.label}: ${sc ?? "—"}/100">
              <div class="diag-chain-box" style="background:${bg};opacity:${sc === null ? 0.35 : 1};"></div>
              <div class="diag-stat-label" style="margin-top:0.3rem;line-height:1.2;">${short}</div>
              <div style="font-size:0.72rem;font-weight:600;font-variant-numeric:tabular-nums;">${sc ?? "—"}</div>
            </div>`;
        }).join("")}
      </div>
    </div>` : "";

  const ranking = h.constraint_priority_ranking || [];
  const rankingBlock = ranking.length ? `
    <div class="diag-block">
      ${sectionLabel(`Constraint priority ranking · ${pc.priority?.model_id || "AFK-PRI-0001"}`)}
      <p class="diag-muted-sm" style="margin-bottom:1rem;max-width:68ch;">
        Ranked by impact (severity × exposure × fixability), not dimension score alone. Operator-judgment weights — not industry benchmarks.
      </p>
      ${ranking.map((r, i) => `
        <div class="diag-rank-row">
          <span style="font-weight:650;color:${i === 0 ? "var(--diag-amber-dark)" : "var(--diag-slate-400)"};">#${i + 1}</span>
          <span style="font-size:0.9rem;">${r.label}</span>
          <span class="diag-stat-label">score ${r.score}</span>
          <span style="font-variant-numeric:tabular-nums;font-weight:600;font-size:0.85rem;">${r.priority_score}</span>
        </div>`).join("")}
    </div>` : "";

  const hs = scoreStatus(h.health_score);
  container.innerHTML = `
    <div class="diag-page diag-page--embedded">
    <div class="diag-health-inner">
      <div class="diag-hero" style="margin-bottom:1.5rem;">
        <p class="diag-hero-kicker">Executive Diagnosis</p>
        <h1>Revenue Health</h1>
        <p>${h.risk_level} · primary constraint ${pc.label}</p>
      </div>

      <div class="diag-hero-score">
        ${renderGauge(h.health_score)}
        <div>
          <span class="diag-status-pill ${hs.cls}" style="margin-bottom:0.75rem;display:inline-block;">${hs.label}</span>
          ${provenance}
          ${changesBlock}
        </div>
      </div>

      <div class="diag-stat-grid diag-block">
        <div>${sectionLabel("Primary Constraint")}
          <div style="font-size:1.15rem;font-weight:600;">${pc.label}</div>
          <div class="diag-stat-label">Dimension score ${pc.score}/100 · impact-ranked</div>
          ${priorityNote}</div>
        <div>${sectionLabel("Epistemic Confidence")}
          <div class="diag-stat-val">${epiOverall}%</div>
          <div class="diag-stat-label" style="max-width:28ch;">${epiMethod}</div></div>
        ${opp}
      </div>

      ${chainBlock}

      <div class="diag-stat-grid diag-block">
        <div><div class="diag-section-label">We analyzed</div><ul style="list-style:none;font-size:0.9rem;">${analyzed}</ul></div>
        <div><div class="diag-section-label">Missing / future evidence</div><ul style="list-style:none;font-size:0.9rem;">${notAnalyzed}${futureEvidence}</ul></div>
      </div>

      <div class="diag-block">${recCard}</div>

      ${hypothesisBlock}
      ${funnelBlock}
      ${compoundBlock}
      ${rankingBlock}

      ${(h.contradictions || []).length ? `
      <div class="diag-block">
        ${sectionLabel("Founder belief vs business reality")}
        <p class="diag-muted-sm" style="margin-bottom:1rem;max-width:64ch;">Where the uploaded evidence disagrees with the audit answers. Not accusations — comparisons worth examining.</p>
        ${h.contradictions.map(c => `
          <div class="diag-panel ${c.severity === "significant" ? "is-warn" : ""}" style="margin-bottom:1rem;">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.25rem;margin-bottom:0.9rem;">
              <div><div class="diag-section-label">You said</div><div style="font-size:0.95rem;">"${c.belief.answer}"<div class="diag-stat-label" style="margin-top:0.2rem;">${c.belief.question}</div></div></div>
              <div><div class="diag-section-label">The evidence shows</div><div style="font-size:0.95rem;font-weight:600;">${c.evidence.value}${c.evidence.metric.includes("pct") || c.evidence.metric.includes("rate") ? "%" : ""}</div><div class="diag-stat-label" style="margin-top:0.2rem;">${c.evidence.basis}</div></div>
            </div>
            <p class="diag-section-body">${c.explanation}</p>
            <p class="diag-muted-sm" style="margin-top:0.6rem;font-style:italic;">${c.follow_up_question}</p>
          </div>`).join("")}
      </div>` : ""}

      ${(h.revenue_drivers || []).length ? `
      <div class="diag-block">
        ${sectionLabel("What's working")}
        <div class="diag-card-grid">
          ${h.revenue_drivers.map(d => `
            <div class="diag-mini-card">
              <div class="diag-stat-label" style="margin-bottom:0.3rem;">${d.label}</div>
              <div style="font-weight:600;">${d.value}</div>
              <div class="diag-stat-label" style="margin-top:0.35rem;">${d.basis}</div>
            </div>`).join("")}
        </div>
      </div>` : ""}

      ${h.confidence_breakdown ? `
      <div class="diag-block">
        ${sectionLabel("Where confidence comes from")}
        ${Object.entries(h.confidence_breakdown.sources).map(([name, src]) => `
          <div class="diag-row" style="grid-template-columns:160px 1fr auto;">
            <span style="font-size:0.9rem;">${name}</span>
            <div class="diag-score-bar"><div style="width:${src.coverage_pct}%;background:${src.missing ? "transparent" : "var(--diag-amber)"};"></div></div>
            <span class="diag-stat-label">${src.missing ? "Missing" : (src.rows ? src.rows + " rows" + (src.quality_pct ? " · quality " + src.quality_pct + "%" : "") : (src.weight || src.coverage_pct + "%"))}</span>
          </div>`).join("")}
        <p class="diag-stat-label" style="margin-top:0.9rem;max-width:70ch;">${h.confidence_breakdown.method}</p>
      </div>` : ""}

      ${(h.missing_evidence || []).some(m => !m.covered) ? `
      <div class="diag-block">
        ${sectionLabel("Evidence that would sharpen this diagnosis")}
        ${h.missing_evidence.filter(m => !m.covered && m.suggestion).map(m => `
          <div style="padding:0.6rem 0;border-bottom:1px solid #f1f5f9;">
            <span style="font-weight:600;font-size:0.88rem;">${m.dimension}:</span>
            <span class="diag-muted-sm"> ${m.suggestion}</span>
          </div>`).join("")}
        <a href="#evidence" class="diag-btn-secondary" style="margin-top:1rem;display:inline-block;text-decoration:none;">Upload evidence →</a>
      </div>` : ""}

      <div class="diag-block">
        ${sectionLabel("Why AFK believes this")}
        ${findings || '<p class="diag-muted">No penalizing findings in the primary constraint dimension.</p>'}
      </div>

      ${openQs}

      <div class="diag-block">
        ${sectionLabel("All dimensions")}
        ${dims}
        <p class="diag-stat-label" style="margin-top:1.25rem;max-width:70ch;">${h.method_note}</p>
        ${h.science_provenance ? `
        <p class="diag-stat-label" style="margin-top:0.75rem;max-width:70ch;">
          ${h.science_provenance.priority_model_id} · ${h.science_provenance.confidence_model_id} ·
          ${h.science_provenance.engine_version} · ${h.science_provenance.rule_pack}
          ${h.science_provenance.compound_pack ? ` · ${h.science_provenance.compound_pack}` : ""}
          ${moat ? ` · moat ${moat.moat_score}/100 (${moat.pillars_passed}/${moat.pillars_total})` : ""}
        </p>` : ""}
      </div>
    </div>
    </div>`;
}