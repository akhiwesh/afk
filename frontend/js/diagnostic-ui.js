export const ZONE_HEX = { rose: "#B0452E", amber: "#BD6B2E", sky: "#3E6E82", emerald: "#4C7A4A" };

export function scoreStatus(score) {
  if (score == null) return { label: "—", colorKey: "sky", cls: "is-muted" };
  if (score >= 85) return { label: "Healthy", colorKey: "emerald", cls: "is-healthy" };
  if (score >= 70) return { label: "Moderate", colorKey: "sky", cls: "is-moderate" };
  if (score >= 55) return { label: "Pressure", colorKey: "amber", cls: "is-pressure" };
  return { label: "Critical", colorKey: "rose", cls: "is-critical" };
}

export function dimScoreColor(score) {
  if (score == null) return "#cbd5e1";
  if (score >= 75) return "#166534";
  if (score >= 55) return "#a16207";
  return "#9f2d1f";
}

export function sectionLabel(text) {
  return `<p class="diag-section-label">${text}</p>`;
}

const GAUGE_ZONE = {
  rose: "#9f2d1f",
  amber: "#a16207",
  sky: "#1e4a5f",
  emerald: "#166534",
};

export function renderGauge(score) {
  if (score == null) return "";
  const st = scoreStatus(score);
  const needleAngle = (score - 50) * 1.8;
  const zoneHex = GAUGE_ZONE[st.colorKey] || GAUGE_ZONE.sky;
  return `
    <div class="diag-gauge-wrap">
      <svg viewBox="0 0 200 160" style="width:100%;" role="img" aria-label="Health score ${score} out of 100, ${st.label}">
        <path d="M 22,110 A 78 78 0 0 1 112.2,32.96" fill="none" stroke="${GAUGE_ZONE.rose}" stroke-width="14"/>
        <path d="M 112.2,32.96 A 78 78 0 0 1 145.85,46.9" fill="none" stroke="${GAUGE_ZONE.amber}" stroke-width="14"/>
        <path d="M 145.85,46.9 A 78 78 0 0 1 169.5,74.59" fill="none" stroke="${GAUGE_ZONE.sky}" stroke-width="14"/>
        <path d="M 169.5,74.59 A 78 78 0 0 1 178,110" fill="none" stroke="${GAUGE_ZONE.emerald}" stroke-width="14"/>
        <text x="16" y="123" font-size="10" font-weight="600" fill="#475569">0</text>
        <text x="184" y="123" font-size="10" font-weight="600" fill="#475569" text-anchor="end">100</text>
        <g transform="rotate(${needleAngle} 100 110)"><polygon points="96,110 104,110 100,36" fill="#7c2d12"/></g>
        <circle cx="100" cy="110" r="8" fill="#431407" stroke="#ffffff" stroke-width="2"/>
      </svg>
      <div class="diag-gauge-score">
        <div class="diag-gauge-num">${score}<span class="diag-gauge-denom">/100</span></div>
        <div class="diag-gauge-status" style="color:${zoneHex};">${st.label}</div>
      </div>
      <div class="diag-gauge-legend">
        <span style="color:${GAUGE_ZONE.rose};">CRITICAL</span>
        <span style="color:${GAUGE_ZONE.amber};">PRESSURE</span>
        <span style="color:${GAUGE_ZONE.sky};">MODERATE</span>
        <span style="color:${GAUGE_ZONE.emerald};">HEALTHY</span>
      </div>
    </div>`;
}

export function ruleIdChip(ruleId, rulePack) {
  if (!ruleId) return "";
  return `<span class="diag-rule-chip" title="${rulePack || ""}">${ruleId}</span>`;
}