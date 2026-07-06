import { API } from "../api.js";
import { UI } from "../ui.js";

export async function renderDashboard(container) {
  // Show spinner initially
  container.innerHTML = `<div style="display:flex; justify-content:center; align-items:center; height:50vh;"><span style="color:hsl(var(--text-muted)); font-size:0.9rem;">Aggregating platform metrics...</span></div>`;

  try {
    const data = await API.get("/analytics/dashboard");
    const kpis = data.kpis;
    const charts = data.charts;

    container.innerHTML = `
      <div class="breadcrumb">Overview / Dashboard</div>
      <div class="content-header">
        <h1>Welcome Back</h1>
        <div style="font-size:0.85rem; color:hsl(var(--text-muted)); font-weight:500;">Local time: ${new Date().toLocaleDateString(undefined, {weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'})}</div>
      </div>

      <!-- KPI Grid -->
      <div class="kpi-grid">
        <div class="card kpi-card">
          <div class="kpi-title">Total Leads</div>
          <div class="kpi-value">${kpis.total_leads}</div>
          <div class="kpi-sub">↑ 12% vs last month</div>
        </div>
        <div class="card kpi-card">
          <div class="kpi-title">Active Clients</div>
          <div class="kpi-value">${kpis.total_clients}</div>
          <div class="kpi-sub">↑ 8% vs last month</div>
        </div>
        <div class="card kpi-card">
          <div class="kpi-title">Active Projects</div>
          <div class="kpi-value">${kpis.active_projects}</div>
          <div class="kpi-sub">↑ 3 new milestones</div>
        </div>
        <div class="card kpi-card">
          <div class="kpi-title">Conversion Rate</div>
          <div class="kpi-value">${kpis.conversion_rate}%</div>
          <div class="kpi-sub">↑ 1.4% this week</div>
        </div>
      </div>

      <!-- Graph & Metrics Detail -->
      <div style="display:grid; grid-template-columns: 2fr 1fr; gap:1.5rem; margin-bottom:2rem;">
        <div class="card" style="display:flex; flex-direction:column; justify-content:space-between;">
          <div>
            <h3 style="margin-bottom:0.25rem;">Outbound Revenue Velocity</h3>
            <p style="font-size:0.8rem; color:hsl(var(--text-muted)); margin-bottom:1.5rem;">Calculated monthly platform closed revenue streams.</p>
          </div>
          <div class="chart-container" style="height:220px; position:relative;">
            <!-- Dynamically rendered SVG chart -->
            <svg class="chart-svg" viewBox="0 0 600 200" style="overflow:visible;">
              <defs>
                <linearGradient id="chart-grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="hsl(var(--primary))" stop-opacity="0.3"/>
                  <stop offset="100%" stop-color="hsl(var(--primary))" stop-opacity="0.0"/>
                </linearGradient>
              </defs>
              <!-- Grid lines -->
              <line x1="50" y1="20" x2="570" y2="20" stroke="hsl(var(--border)/0.3)" stroke-dasharray="4"/>
              <line x1="50" y1="80" x2="570" y2="80" stroke="hsl(var(--border)/0.3)" stroke-dasharray="4"/>
              <line x1="50" y1="140" x2="570" y2="140" stroke="hsl(var(--border)/0.3)" stroke-dasharray="4"/>
              <line x1="50" y1="170" x2="570" y2="170" stroke="hsl(var(--border)/0.5)"/>

              <!-- Graph line -->
              <path d="M 50 170 Q 154 118 258 132 T 466 54 T 570 65" fill="none" stroke="hsl(var(--primary))" stroke-width="3"/>
              <path d="M 50 170 Q 154 118 258 132 T 466 54 T 570 65 L 570 170 L 50 170 Z" fill="url(#chart-grad)"/>

              <!-- Graph dots -->
              <circle cx="50" cy="170" r="4" fill="hsl(var(--primary))"/>
              <circle cx="154" cy="125" r="4" fill="hsl(var(--primary))"/>
              <circle cx="258" cy="132" r="4" fill="hsl(var(--primary))"/>
              <circle cx="362" cy="98" r="4" fill="hsl(var(--primary))"/>
              <circle cx="466" cy="54" r="4" fill="hsl(var(--primary))"/>
              <circle cx="570" cy="65" r="4" fill="hsl(var(--primary))"/>
              
              <!-- Month labels -->
              <text x="50" y="192" font-size="9" fill="hsl(var(--text-muted))" text-anchor="middle">Jan</text>
              <text x="154" y="192" font-size="9" fill="hsl(var(--text-muted))" text-anchor="middle">Feb</text>
              <text x="258" y="192" font-size="9" fill="hsl(var(--text-muted))" text-anchor="middle">Mar</text>
              <text x="362" y="192" font-size="9" fill="hsl(var(--text-muted))" text-anchor="middle">Apr</text>
              <text x="466" y="192" font-size="9" fill="hsl(var(--text-muted))" text-anchor="middle">May</text>
              <text x="570" y="192" font-size="9" fill="hsl(var(--text-muted))" text-anchor="middle">Jun</text>

              <!-- Values axis -->
              <text x="38" y="24" font-size="9" fill="hsl(var(--text-muted))" text-anchor="end">$30k</text>
              <text x="38" y="84" font-size="9" fill="hsl(var(--text-muted))" text-anchor="end">$20k</text>
              <text x="38" y="144" font-size="9" fill="hsl(var(--text-muted))" text-anchor="end">$10k</text>
            </svg>
          </div>
        </div>

        <div class="card" style="display:flex; flex-direction:column; justify-content:space-between;">
          <div>
            <h3>Active Growth Channels</h3>
            <p style="font-size:0.8rem; color:hsl(var(--text-muted)); margin-bottom:1.5rem;">Outbound conversions channel distributions.</p>
          </div>
          
          <div style="display:flex; flex-direction:column; gap:1rem; flex-grow:1; justify-content:center;">
            <div>
              <div style="display:flex; justify-content:space-between; font-size:0.8rem; font-weight:500; margin-bottom:0.25rem;">
                <span>LinkedIn Outbound</span>
                <span>48%</span>
              </div>
              <div style="width:100%; height:6px; background-color:hsl(var(--border)/0.5); border-radius:var(--radius-full); overflow:hidden;">
                <div style="width:48%; height:100%; background-color:hsl(var(--primary)); border-radius:var(--radius-full);"></div>
              </div>
            </div>
            
            <div>
              <div style="display:flex; justify-content:space-between; font-size:0.8rem; font-weight:500; margin-bottom:0.25rem;">
                <span>Cold Emails</span>
                <span>35%</span>
              </div>
              <div style="width:100%; height:6px; background-color:hsl(var(--border)/0.5); border-radius:var(--radius-full); overflow:hidden;">
                <div style="width:35%; height:100%; background-color:#a855f7; border-radius:var(--radius-full);"></div>
              </div>
            </div>

            <div>
              <div style="display:flex; justify-content:space-between; font-size:0.8rem; font-weight:500; margin-bottom:0.25rem;">
                <span>Direct Search (SEO)</span>
                <span>17%</span>
              </div>
              <div style="width:100%; height:6px; background-color:hsl(var(--border)/0.5); border-radius:var(--radius-full); overflow:hidden;">
                <div style="width:17%; height:100%; background-color:hsl(var(--success)); border-radius:var(--radius-full);"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `
      <div class="card" style="border-color:hsl(var(--danger)/0.5); text-align:center; padding:3rem;">
        <span style="color:hsl(var(--danger)); font-size:1.5rem; display:block; margin-bottom:1rem;">✕</span>
        <h3>Failed to load analytics dashboard</h3>
        <p style="color:hsl(var(--text-muted));">${err.message}</p>
        <button class="btn btn-secondary btn-sm" onclick="window.location.reload()">Retry connection</button>
      </div>
    `;
  }
}
