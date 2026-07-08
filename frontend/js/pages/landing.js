import { API } from "../api.js";
import { AppRouter } from "../router.js";
import { UI } from "../ui.js";

export function renderLanding(container) {
  container.innerHTML = `
    <header class="nav-header">
      <div class="nav-logo">
        <span style="background:linear-gradient(135deg, hsl(var(--primary)), #a855f7); width:28px; height:28px; border-radius:6px; display:inline-flex; align-items:center; justify-content:center; color:white; font-weight:800; font-size:0.9rem;">A</span>
        AFK Platform
      </div>
      <nav class="nav-links">
        <a href="#offer">Diagnostic offer</a>
        <a href="#features">Platform</a>
        <a href="#pricing">Pricing</a>
        ${API.isAuthenticated() 
          ? `<a href="#diagnosis" class="btn btn-primary btn-sm">Dashboard</a>`
          : `<a href="#login" class="btn btn-secondary btn-sm">Sign In</a>`
        }
      </nav>
    </header>

    <main style="max-width:1200px; margin:0 auto; padding:4rem 2rem; box-sizing:border-box;">
      <!-- Hero Section -->
      <section style="text-align:center; margin-bottom:6rem; position:relative;">
        <div style="position:absolute; top:-100px; left:50%; transform:translateX(-50%); width:600px; height:300px; background:radial-gradient(circle, hsl(var(--primary)/0.15) 0%, transparent 70%); z-index:-1; filter:blur(50px);"></div>
        
        <span style="font-size:0.85rem; font-weight:600; text-transform:uppercase; letter-spacing:0.1em; color:hsl(var(--primary)); background:hsl(var(--primary)/0.1); padding:0.35rem 1rem; border-radius:var(--radius-full); display:inline-block; margin-bottom:1.5rem;">Business Science for Service Founders</span>
        
        <h1 style="font-size:3.5rem; line-height:1.1; margin-bottom:1.5rem; max-width:850px; margin-left:auto; margin-right:auto;">
          Where is your revenue <span style="background:linear-gradient(to right, hsl(var(--primary)), #a855f7); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">actually stuck?</span>
        </h1>
        
        <p style="font-size:1.15rem; max-width:600px; margin:0 auto 2.5rem auto; color:hsl(var(--text-secondary));">
          Evidence → diagnosis → clarity. Upload your invoices and CRM exports, complete the Revenue Audit, and see what your data proves — never invented numbers.
        </p>
        
        <div style="display:flex; justify-content:center; gap:1rem; flex-wrap:wrap;">
          <a href="#offer" class="btn btn-primary btn-lg">Revenue Constraint Diagnostic</a>
          <button type="button" class="btn btn-secondary btn-lg" id="landing-demo-btn">Try demo business</button>
          <a href="#register" class="btn btn-secondary btn-lg" style="opacity:0.85;">Create organisation</a>
        </div>
      </section>

      <!-- Live Simulation Widget (The "WOW" Interaction) -->
      <section style="margin-bottom:6rem;">
        <div class="card glass-card" style="padding:2rem; max-width:800px; margin:0 auto; border-color:hsl(var(--border)); position:relative; overflow:hidden;">
          <div style="display:flex; align-items:center; gap:8px; border-bottom:1px solid hsl(var(--border)/0.5); padding-bottom:1rem; margin-bottom:1.5rem;">
            <span style="width:12px; height:12px; border-radius:50%; background-color:#ef4444;"></span>
            <span style="width:12px; height:12px; border-radius:50%; background-color:#f59e0b;"></span>
            <span style="width:12px; height:12px; border-radius:50%; background-color:#10b981;"></span>
            <span style="font-size:0.75rem; font-family:monospace; color:hsl(var(--text-muted)); margin-left:8px;">automation-engine-v1.sh</span>
          </div>

          <div class="grid grid-cols-2" style="gap:2rem;">
            <div>
              <h3 style="margin-bottom:1rem; font-size:1.1rem;">Interactive Sandbox</h3>
              <p style="font-size:0.85rem; margin-bottom:1.5rem;">Simulate lead arrival to see how the AFK AI qualification workflow engine acts autonomously.</p>
              
              <div class="form-group">
                <label class="form-label" style="font-size:0.75rem;">Company Name</label>
                <input type="text" id="sim-company" class="form-control" value="Stark Industries" style="padding:0.5rem 0.75rem;">
              </div>
              <div class="form-group">
                <label class="form-label" style="font-size:0.75rem;">Employee Count</label>
                <input type="number" id="sim-size" class="form-control" value="250" style="padding:0.5rem 0.75rem;">
              </div>
              <button class="btn btn-primary btn-sm" id="run-sim-btn" style="width:100%;">Trigger Simulation</button>
            </div>
            
            <div style="background-color:hsl(var(--bg-sidebar)/0.7); border:1px solid hsl(var(--border)/0.6); border-radius:var(--radius-md); padding:1rem; font-family:monospace; font-size:0.75rem; color:hsl(var(--text-secondary)); height:240px; overflow-y:auto;" id="sim-log">
              <span style="color:hsl(var(--primary));">> Initializing Sandbox Simulator...</span><br>
              <span>> Click 'Trigger Simulation' to begin.</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Client Logo Showcase (Aesthetic Infinite Roll Simulation) -->
      <section id="features" style="text-align:center; margin-bottom:6rem;">
        <span style="font-size:0.75rem; color:hsl(var(--text-muted)); text-transform:uppercase; letter-spacing:0.1em; display:block; margin-bottom:2rem;">Trusted by modern tech leaders</span>
        <div style="display:flex; justify-content:center; align-items:center; gap:4rem; flex-wrap:wrap; opacity:0.6;">
          <span style="font-family:var(--font-display); font-weight:700; font-size:1.5rem;">ACME</span>
          <span style="font-family:var(--font-display); font-weight:700; font-size:1.5rem;">WAYNE</span>
          <span style="font-family:var(--font-display); font-weight:700; font-size:1.5rem;">STARK</span>
          <span style="font-family:var(--font-display); font-weight:700; font-size:1.5rem;">CYBERDYNE</span>
          <span style="font-family:var(--font-display); font-weight:700; font-size:1.5rem;">OSCORP</span>
        </div>
      </section>

      <!-- Features Cards Grid -->
      <section style="margin-bottom:6rem;">
        <h2 style="text-align:center; margin-bottom:3rem; font-size:2rem;">One platform. Endless capabilities.</h2>
        <div class="grid grid-cols-3">
          <div class="card glass-card">
            <span style="background:hsl(var(--primary)/0.1); width:40px; height:40px; border-radius:8px; display:inline-flex; align-items:center; justify-content:center; color:hsl(var(--primary)); margin-bottom:1.25rem;">✦</span>
            <h3>10+ AI Assistants</h3>
            <p style="font-size:0.85rem; margin:0;">Targeted profiles with memory for content generation, sales consulting, SEO keyword mappings and workflow prompts.</p>
          </div>
          <div class="card glass-card">
            <span style="background:hsl(var(--primary)/0.1); width:40px; height:40px; border-radius:8px; display:inline-flex; align-items:center; justify-content:center; color:hsl(var(--primary)); margin-bottom:1.25rem;">✦</span>
            <h3>Execution Pipelines</h3>
            <p style="font-size:0.85rem; margin:0;">Elegant Kanban, task cards lists and assignee schedules mapping project actions cleanly.</p>
          </div>
          <div class="card glass-card">
            <span style="background:hsl(var(--primary)/0.1); width:40px; height:40px; border-radius:8px; display:inline-flex; align-items:center; justify-content:center; color:hsl(var(--primary)); margin-bottom:1.25rem;">✦</span>
            <h3>Visual Workflow Builder</h3>
            <p style="font-size:0.85rem; margin:0;">Create multi-action rules (qualify lead -> send custom sequence -> update CRM -> notify Slack) instantly.</p>
          </div>
        </div>
      </section>

      <!-- Pricing / offer bridge -->
      <section id="pricing" style="margin-bottom:6rem; text-align:center;">
        <h2 style="font-size:2rem; margin-bottom:1rem;">Start with clarity, then scale.</h2>
        <p style="margin-bottom:1.25rem;max-width:36rem;margin-left:auto;margin-right:auto;">
          The concierge <strong>Revenue Constraint Diagnostic</strong> (₹49,000) is how most founders begin —
          evidence-grounded diagnosis before any platform subscription.
        </p>
        <a href="#offer" class="btn btn-primary" style="margin-bottom:2.5rem;">View diagnostic offer →</a>
        <p style="font-size:0.82rem;color:hsl(var(--text-muted));margin-bottom:2.5rem;">Self-serve platform plans (parked — diagnostic first)</p>
        
        <div style="display:inline-flex; background-color:hsl(var(--bg-sidebar)); padding:4px; border-radius:var(--radius-md); border:1px solid hsl(var(--border)); margin-bottom:3rem;">
          <button class="btn btn-secondary btn-sm" style="background-color:hsl(var(--bg-card)); border:none;" id="toggle-monthly">Monthly</button>
          <button class="btn btn-secondary btn-sm" style="border:none;" id="toggle-annual">Annual (Save 20%)</button>
        </div>

        <div class="grid grid-cols-2" style="max-width:700px; margin:0 auto; text-align:left;">
          <!-- Growth plan -->
          <div class="card glass-card" style="position:relative; display:flex; flex-direction:column; justify-content:space-between; height:400px;">
            <div>
              <span style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em; color:hsl(var(--primary)); font-weight:600; display:block; margin-bottom:0.75rem;">Growth Plan</span>
              <h3 style="font-size:2.5rem; font-family:var(--font-display); font-weight:700; margin-bottom:0.5rem;" id="price-growth">$49<span style="font-size:1rem; font-weight:400; color:hsl(var(--text-muted));">/mo</span></h3>
              <p style="font-size:0.8rem; margin-bottom:1.5rem;">For small teams starting their automation outreach campaigns.</p>
              
              <ul style="padding-left:1.25rem; font-size:0.85rem; color:hsl(var(--text-secondary)); display:flex; flex-direction:column; gap:0.5rem;">
                <li>Up to 10 active automations</li>
                <li>Access to all 10+ AI Assistants</li>
                <li>CRM and Project Kanban boards</li>
                <li>Basic monthly analytics reports</li>
              </ul>
            </div>
            <a href="#login" class="btn btn-primary" style="width:100%;">Start Growth Free</a>
          </div>

          <!-- Enterprise plan -->
          <div class="card glass-card" style="border-color:hsl(var(--primary)); position:relative; display:flex; flex-direction:column; justify-content:space-between; height:400px;">
            <div style="position:absolute; top:-12px; right:1.5rem; background-color:hsl(var(--primary)); color:hsl(var(--primary-foreground)); font-size:0.7rem; font-weight:600; padding:0.25rem 0.75rem; border-radius:var(--radius-full);">RECOMMENDED</div>
            <div>
              <span style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em; color:hsl(var(--primary)); font-weight:600; display:block; margin-bottom:0.75rem;">Scale Plan</span>
              <h3 style="font-size:2.5rem; font-family:var(--font-display); font-weight:700; margin-bottom:0.5rem;" id="price-scale">$149<span style="font-size:1rem; font-weight:400; color:hsl(var(--text-muted));">/mo</span></h3>
              <p style="font-size:0.8rem; margin-bottom:1.5rem;">For venture backed teams scaling out GTM qualification.</p>
              
              <ul style="padding-left:1.25rem; font-size:0.85rem; color:hsl(var(--text-secondary)); display:flex; flex-direction:column; gap:0.5rem;">
                <li>Unlimited workflow execution rules</li>
                <li>Custom CRM field mappings</li>
                <li>Multi-user role access levels</li>
                <li>Real-time webhook notifications</li>
              </ul>
            </div>
            <a href="#login" class="btn btn-primary" style="width:100%;">Scale Outbound Now</a>
          </div>
        </div>
      </section>
    </main>

    <!-- Footer -->
    <footer style="border-top:1px solid hsl(var(--border)/0.5); padding:3rem 2rem; background-color:hsl(var(--bg-sidebar)/0.4); font-size:0.8rem; color:hsl(var(--text-muted)); text-align:center;">
      <div style="max-width:1200px; margin:0 auto; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1.5rem;">
        <div>© 2026 AFK Inc. All rights reserved.</div>
        <div style="display:flex; gap:1.5rem;">
          <a href="#features" style="color:hsl(var(--text-muted));">Features</a>
          <a href="#pricing" style="color:hsl(var(--text-muted));">Pricing</a>
          <a href="#faq" style="color:hsl(var(--text-muted));">FAQ</a>
        </div>
      </div>
    </footer>
  `;

  // Hooks and logic for Sandbox Simulator
  const simLog = container.querySelector("#sim-log");
  const runBtn = container.querySelector("#run-sim-btn");
  const simCompany = container.querySelector("#sim-company");
  const simSize = container.querySelector("#sim-size");

  runBtn.addEventListener("click", () => {
    const company = simCompany.value || "Anonymous Inc";
    const size = parseInt(simSize.value) || 10;
    
    simLog.innerHTML = `<span style="color:hsl(var(--primary));">> Initiating Qualification Run...</span><br>`;
    
    setTimeout(() => {
      simLog.innerHTML += `<span>> Step 1: Lead Captured (Source: Webflow Form)</span><br>`;
      simLog.innerHTML += `<span>  - Company: <strong>${company}</strong> | Size: <strong>${size}</strong></span><br>`;
    }, 400);

    setTimeout(() => {
      simLog.innerHTML += `<span>> Step 2: Evaluation through LLM rules node...</span><br>`;
    }, 1000);

    setTimeout(() => {
      if (size >= 50) {
        simLog.innerHTML += `<span style="color:hsl(var(--success));">> Step 3: QUALIFIED (Company size ${size} >= 50)</span><br>`;
        simLog.innerHTML += `<span>> Step 4: Outbound welcome sequences dispatched to founders...</span><br>`;
        simLog.innerHTML += `<span>> Step 5: Posted webhook to #growth Slack channel.</span><br>`;
        simLog.innerHTML += `<span style="color:hsl(var(--success));">> [Execution Succeeded]</span>`;
      } else {
        simLog.innerHTML += `<span style="color:#ef4444;">> Step 3: DISQUALIFIED (Company size ${size} < 50)</span><br>`;
        simLog.innerHTML += `<span>> Step 4: Route logs to cold newsletters database.</span><br>`;
        simLog.innerHTML += `<span style="color:#ef4444;">> [Execution Terminated]</span>`;
      }
      simLog.scrollTop = simLog.scrollHeight;
    }, 1600);
  });

  // Toggle monthly/annual prices
  const toggleMonthly = container.querySelector("#toggle-monthly");
  const toggleAnnual = container.querySelector("#toggle-annual");
  const pGrowth = container.querySelector("#price-growth");
  const pScale = container.querySelector("#price-scale");

  toggleMonthly.addEventListener("click", () => {
    toggleMonthly.style.backgroundColor = "hsl(var(--bg-card))";
    toggleAnnual.style.backgroundColor = "transparent";
    pGrowth.innerHTML = `$49<span style="font-size:1rem; font-weight:400; color:hsl(var(--text-muted));">/mo</span>`;
    pScale.innerHTML = `$149<span style="font-size:1rem; font-weight:400; color:hsl(var(--text-muted));">/mo</span>`;
  });

  toggleAnnual.addEventListener("click", () => {
    toggleAnnual.style.backgroundColor = "hsl(var(--bg-card))";
    toggleMonthly.style.backgroundColor = "transparent";
    pGrowth.innerHTML = `$39<span style="font-size:1rem; font-weight:400; color:hsl(var(--text-muted));">/mo</span>`;
    pScale.innerHTML = `$119<span style="font-size:1rem; font-weight:400; color:hsl(var(--text-muted));">/mo</span>`;
  });

  const demoBtn = container.querySelector("#landing-demo-btn");
  if (demoBtn) {
    demoBtn.addEventListener("click", async () => {
      demoBtn.disabled = true;
      const label = demoBtn.textContent;
      demoBtn.textContent = "Loading demo…";
      try {
        const data = await API.post("/auth/demo", {});
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("user_profile", JSON.stringify(data.user));
        if (data.demo) {
          localStorage.setItem("afk_demo_session", "true");
        }
        UI.toast("Demo loaded — sample diagnosis ready.", "success");
        window.dispatchEvent(new Event("auth-changed"));
        AppRouter.navigate("#diagnosis");
      } catch (err) {
        UI.toast(err.message || "Demo session unavailable.", "error");
        demoBtn.disabled = false;
        demoBtn.textContent = label;
      }
    });
  }
}
