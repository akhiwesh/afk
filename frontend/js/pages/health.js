import { API } from "../api.js";
import { UI } from "../ui.js";
import { navigateToEvidence } from "./evidence.js";
import { renderGauge, ruleIdChip, scoreStatus, dimScoreColor, sectionLabel } from "../diagnostic-ui.js";

const EVIDENCE_KIND_LABELS = {
  invoices: "Invoices",
  leads: "Lead export",
  transactions: "Transactions",
  customers: "Customer list",
};

function rankedMissingEvidence(pc, items) {
  const missing = (items || []).filter((m) => !m.covered && m.suggestion && m.evidence_kind);
  return missing.sort((a, b) => {
    const aPrimary = a.dimension === pc?.label ? 1 : 0;
    const bPrimary = b.dimension === pc?.label ? 1 : 0;
    return bPrimary - aPrimary;
  });
}

function evidenceCtaPanel(pc, missingEvidence) {
  const ranked = rankedMissingEvidence(pc, missingEvidence).slice(0, 3);
  if (!ranked.length) return "";

  return `
    <div class="diag-block">
      <div class="diag-panel is-warn">
        ${sectionLabel("Upload this to sharpen diagnosis")}
        <p class="diag-muted-sm" style="margin-bottom:1rem;max-width:68ch;">
          Audit answers cap confidence at 40% per dimension. Uploaded evidence raises it — and can surface contradictions between what you believe and what your data shows.
        </p>
        ${ranked.map((m, i) => `
          <div class="diag-ev-cta-card ${i === 0 && m.dimension === pc.label ? "is-primary" : ""}">
            <div class="diag-ev-cta-head">
              <span style="font-weight:600;font-size:0.92rem;">${m.dimension}</span>
              ${m.dimension === pc.label
                ? `<span class="diag-evidence is-high">Primary constraint</span>`
                : `<span class="diag-evidence is-medium">Raises confidence</span>`}
            </div>
            <p class="diag-muted-sm" style="margin-bottom:0.75rem;">${m.suggestion}</p>
            <button type="button" class="diag-btn-primary" data-evidence-upload="${m.evidence_kind}">
              Upload ${EVIDENCE_KIND_LABELS[m.evidence_kind] || m.evidence_kind} →
            </button>
          </div>`).join("")}
      </div>
    </div>`;
}

const fmtINR = (n) => "₹" + Number(n).toLocaleString("en-IN");

function treatmentTrackingBlock(pc, outcomesData) {
  if (!pc?.key) return "";
  const protocol = outcomesData?.protocol_id || "AFK-OUT-0001";
  const active = (outcomesData?.outcomes || []).find(
    (o) => o.constraint_key === pc.key && o.status === "started",
  );

  if (active) {
    const since = new Date(active.recorded_at).toLocaleDateString("en-IN", {
      day: "numeric", month: "short", year: "numeric",
    });
    return `
      <div class="diag-treatment-block">
        ${sectionLabel(`Treatment tracking · ${protocol}`)}
        <div class="diag-treatment-status">
          <span class="diag-status-pill is-moderate">In progress</span>
          <span class="diag-muted-sm">Started ${since} · baseline ${active.baseline_dimension_score ?? "—"}/100</span>
          ${active.treatment_id ? ruleIdChip(active.treatment_id) : ""}
        </div>
        <p class="diag-muted-sm">AFK compares your dimension score on the next diagnosis — not revenue claims until evidence confirms.</p>
        <div class="diag-treatment-actions">
          <button type="button" class="diag-btn-primary" data-treatment-action="completed" data-constraint-key="${pc.key}">Mark complete</button>
          <button type="button" class="diag-btn-secondary" data-treatment-action="abandoned" data-constraint-key="${pc.key}">Abandoned</button>
        </div>
      </div>`;
  }

  return `
    <div class="diag-treatment-block">
      ${sectionLabel(`Treatment tracking · ${protocol}`)}
      <p class="diag-muted-sm">Record that you've begun the recommended action. AFK tracks dimension score change over time.</p>
      <button type="button" class="diag-btn-primary" data-treatment-action="started" data-constraint-key="${pc.key}">Start this treatment</button>
    </div>`;
}

function wireTreatmentHandlers(container) {
  container.querySelectorAll("[data-treatment-action]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const status = btn.dataset.treatmentAction;
      const constraintKey = btn.dataset.constraintKey;
      const labels = { started: "Starting…", completed: "Saving…", abandoned: "Saving…" };
      const original = btn.textContent;
      btn.disabled = true;
      btn.textContent = labels[status] || "Saving…";
      container.querySelectorAll("[data-treatment-action]").forEach((b) => { b.disabled = true; });
      try {
        const res = await API.post("/intelligence/outcomes", {
          constraint_key: constraintKey,
          status,
        });
        const verdict = res.outcome?.outcome_verdict;
        const msg = status === "started"
          ? "Treatment started — AFK is tracking progress."
          : status === "completed"
            ? `Treatment complete — verdict: ${verdict || "recorded"}.`
            : "Treatment marked abandoned.";
        UI.toast(msg, "success");
        await renderHealth(container);
      } catch (e) {
        UI.toast(e.message || "Could not record treatment.", "error");
        container.querySelectorAll("[data-treatment-action]").forEach((b) => {
          b.disabled = false;
          if (b === btn) b.textContent = original;
        });
      }
    });
  });
}

export async function renderHealth(container) {
  container.innerHTML = `<div class="diag-page diag-page--embedded"><div class="diag-health-inner" style="padding:3rem 0;text-align:center;"><span class="diag-muted">Computing diagnosis from your evidence…</span></div></div>`;

  let h, moat, outcomes;
  try {
    [h, outcomes] = await Promise.all([
      API.get("/intelligence/health"),
      API.get("/intelligence/outcomes").catch(() => null),
    ]);
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
      ${treatmentTrackingBlock(pc, outcomes)}
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
  const chainBlock = chainDims.length ? (() => {
    const pcKey = pc.key;
    const W = 680, cy = 92, n = chainDims.length;
    const step = (W - 100) / (n - 1);
    const nodes = chainDims.map((d, i) => ({
      d, x: Math.round(50 + i * step),
      r: d.key === pcKey ? 30 : 25,
      sc: d.score,
      flow: d.score === null ? 6 : Math.max(4, Math.round((d.score / 100) * 26)),
      hue: d.score === null ? "#94a3b8" : d.score >= 70 ? "#1D9E75" : d.score >= 50 ? "#EF9F27" : "#E24B4A",
    }));
    const pipes = nodes.slice(0, -1).map((nd, i) => {
      const nx = nodes[i + 1];
      const th = Math.max(4, Math.min(nd.flow, nx.flow));
      return `<path class="diag-flow" d="M${nd.x} ${cy} H${nx.x}" stroke="${nx.hue}" stroke-width="${th}" fill="none" opacity="0.3" stroke-linecap="round"/>`;
    }).join("");
    const circles = nodes.map(nd => {
      const isPc = nd.d.key === pcKey;
      return `<circle cx="${nd.x}" cy="${cy}" r="${nd.r}" fill="${nd.hue}" fill-opacity="${nd.sc === null ? 0.12 : 0.16}" stroke="${nd.hue}" stroke-width="${isPc ? 2 : 1}"/>`
        + `<text x="${nd.x}" y="${cy}" text-anchor="middle" dominant-baseline="central" style="font-size:15px;font-weight:600;fill:var(--diag-text-primary);font-variant-numeric:tabular-nums;">${nd.sc ?? "\u2014"}</text>`
        + `<text x="${nd.x}" y="${cy + nd.r + 20}" text-anchor="middle" style="font-size:12px;fill:var(--diag-text-secondary);">${nd.d.label.split(" ")[0]}</text>`
        + (isPc ? `<text x="${nd.x}" y="${cy + nd.r + 36}" text-anchor="middle" style="font-size:11px;fill:${nd.hue};">primary constraint</text>` : "");
    }).join("");
    const lost = h.revenue_opportunity ? `<text x="0" y="196" style="font-size:12px;fill:var(--diag-amber-dark);">${fmtINR(h.revenue_opportunity.amount)}/yr is the modelled opportunity at this constraint</text>` : "";
    return `
    <div class="diag-block">
      ${sectionLabel("Your revenue engine")}
      <p class="diag-muted-sm" style="margin-bottom:1rem;max-width:68ch;">
        How money moves through your business, left to right. The pipe narrows where revenue is lost \u2014 the narrowest point is your constraint.
      </p>
      <svg width="100%" viewBox="0 0 680 210" role="img" style="overflow:visible;">
        <title>Revenue engine flow</title>
        <desc>Business systems in sequence; flow thickness reflects each system score, narrowing at the primary constraint.</desc>
        ${pipes}${circles}
        <text x="0" y="176" style="font-size:12px;fill:var(--diag-text-secondary);">Flow thickness = how much revenue survives each stage</text>
        ${lost}
      </svg>
    </div>`;
  })() : "";

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
      <div class="diag-reveal" style="--d:0s;display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;flex-wrap:wrap;margin-bottom:0.25rem;">
        <p class="diag-hero-kicker" style="margin:0;">Executive Diagnosis</p>
        <button type="button" class="diag-btn-secondary" id="health-export-pdf" style="flex-shrink:0;">Download PDF</button>
      </div>

      <div class="diag-reveal" style="--d:.1s;display:flex;align-items:baseline;gap:0.75rem;flex-wrap:wrap;margin:0.25rem 0 0.5rem;">
        <span style="font-size:4rem;font-weight:600;line-height:1;font-variant-numeric:tabular-nums;">${h.health_score}</span>
        <span style="font-size:1.1rem;" class="diag-muted">/ 100</span>
        <span class="diag-status-pill ${hs.cls}">${hs.label}</span>
      </div>

      <p class="diag-reveal" style="--d:.2s;font-size:1.05rem;line-height:1.65;max-width:56ch;margin:0 0 1.75rem;">
        ${pc.one_liner || "Your primary constraint is " + pc.label + "."}
      </p>

      <div class="diag-reveal" style="--d:.3s;">
        ${provenance}
        ${changesBlock}
      </div>

      ${evidenceCtaPanel(pc, h.missing_evidence)}

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

      ${(() => {
        const em = h.evidence_metrics || {};
        const LABELS = {
          avg_order_value: ["Average order value", v => fmtINR(v)],
          avg_monthly_revenue: ["Average monthly revenue", v => fmtINR(v)],
          avg_discount_pct: ["Average discount", v => v + "%"],
          repeat_customer_rate: ["Repeat customers", v => v + "%"],
          revenue_concentration_pct: ["Revenue concentration", v => v + "%"],
          revenue_trend_pct: ["Revenue trend", v => (v >= 0 ? "+" : "") + v + "%"],
          seasonality_swing_pct: ["Seasonal swing", v => v + "%"],
          dormant_customer_pct: ["Dormant customers", v => v + "%"],
          lead_conversion_pct: ["Lead conversion", v => v + "%"],
          top_lead_source: ["Top lead source", v => v],
        };
        const rows = Object.keys(LABELS).filter(k => em[k]).map(k => {
          const [label, fmt] = LABELS[k];
          return \`<div class="diag-mini-card">
            <div class="diag-stat-label" style="margin-bottom:0.3rem;">\${label}</div>
            <div style="font-weight:600;font-size:1.05rem;">\${fmt(em[k].value)}</div>
            <div class="diag-stat-label" style="margin-top:0.35rem;line-height:1.35;">\${em[k].basis}</div>
          </div>\`;
        }).join("");
        return rows ? \`
      <div class="diag-block">
        \${sectionLabel("What your data reveals")}
        <p class="diag-muted-sm" style="margin-bottom:1rem;max-width:68ch;">Measured directly from your uploaded files — computed, never asked. The more you upload, the more appears here.</p>
        <div class="diag-card-grid">\${rows}</div>
      </div>\` : "";
      })()}

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

  wireTreatmentHandlers(container);

  container.querySelectorAll("[data-evidence-upload]").forEach((btn) => {
    btn.addEventListener("click", () => navigateToEvidence(btn.dataset.evidenceUpload));
  });

  container.querySelector("#health-export-pdf")?.addEventListener("click", async () => {
    const btn = container.querySelector("#health-export-pdf");
    const label = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Generating…";
    try {
      const filename = await API.download("/intelligence/health/export.pdf");
      UI.toast(`Downloaded ${filename}`, "success");
    } catch (e) {
      UI.toast(e.message || "Could not export PDF.", "error");
    } finally {
      btn.disabled = false;
      btn.textContent = label;
    }
  });
}
