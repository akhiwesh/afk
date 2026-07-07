export const ZONE_HEX = { rose: "#B0452E", amber: "#BD6B2E", sky: "#3E6E82", emerald: "#4C7A4A" };

export function scoreStatus(score) {
  if (score == null) return { label: "—", colorKey: "sky", cls: "is-muted" };
  if (score >= 85) return { label: "Healthy", colorKey: "emerald", cls: "is-healthy" };
  if (score >= 70) return { label: "Moderate", colorKey: "sky", cls: "is-moderate" };
  if (score >= 55) return { label: "Pressure", colorKey: "amber", cls: "is-pressure" };
  return { label: "Critical", colorKey: "rose", cls: "is-critical" };
}

export function dimScoreColor(score) {
  if (score == null) return "#e2e8f0";
  if (score >= 75) return ZONE_HEX.emerald;
  if (score >= 55) return ZONE_HEX.amber;
  return ZONE_HEX.rose;
}

export function sectionLabel(text) {
  return `<p class="diag-section-label">${text}</p>`;
}

export function renderGauge(score) {
  if (score == null) return "";
  const st = scoreStatus(score);
  const needleAngle = (score - 50) * 1.8;
  const zoneHex = ZONE_HEX[st.colorKey] || ZONE_HEX.sky;
  return `
    <div style="max-width:260px;margin:0 auto;">
      <svg viewBox="0 0 200 160" style="width:100%;">
        <path d="M 22,110 A 78 78 0 0 1 112.2,32.96" fill="none" stroke="${ZONE_HEX.rose}" stroke-width="14"/>
        <path d="M 112.2,32.96 A 78 78 0 0 1 145.85,46.9" fill="none" stroke="${ZONE_HEX.amber}" stroke-width="14"/>
        <path d="M 145.85,46.9 A 78 78 0 0 1 169.5,74.59" fill="none" stroke="${ZONE_HEX.sky}" stroke-width="14"/>
        <path d="M 169.5,74.59 A 78 78 0 0 1 178,110" fill="none" stroke="${ZONE_HEX.emerald}" stroke-width="14"/>
        <text x="16" y="123" font-size="9" fill="#94a3b8">0</text>
        <text x="184" y="123" font-size="9" fill="#94a3b8" text-anchor="end">100</text>
        <g transform="rotate(${needleAngle} 100 110)"><polygon points="96,110 104,110 100,36" fill="#8a5a2b"/></g>
        <circle cx="100" cy="110" r="8" fill="#57381b" stroke="#F1EEE4" stroke-width="2"/>
      </svg>
      <div style="text-align:center;margin-top:-1rem;">
        <div style="font-family:ui-monospace,monospace;font-size:2.25rem;font-weight:700;">${score}<span style="font-size:1rem;font-weight:400;color:#94a3b8;">/100</span></div>
        <div style="font-family:'Lora',Georgia,serif;font-weight:600;color:${zoneHex};">${st.label}</div>
      </div>
      <div class="diag-gauge-legend">
        <span style="color:${ZONE_HEX.rose};">CRITICAL</span>
        <span style="color:${ZONE_HEX.amber};">PRESSURE</span>
        <span style="color:${ZONE_HEX.sky};">MODERATE</span>
        <span style="color:${ZONE_HEX.emerald};">HEALTHY</span>
      </div>
    </div>`;
}

export function ruleIdChip(ruleId, rulePack) {
  if (!ruleId) return "";
  return `<span class="diag-rule-chip" title="${rulePack || ""}">${ruleId}</span>`;
}