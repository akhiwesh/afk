import { API } from "../api.js";
import { AppRouter } from "../router.js";
import { UI } from "../ui.js";

const REVENUE_BANDS = [
  "Under ₹5L/mo",
  "₹5L–10L/mo",
  "₹10L–25L/mo",
  "₹25L–1Cr/mo",
  "₹1Cr+/mo",
  "Prefer not to say",
];

const FAQ = [
  {
    q: "Is this software or a service?",
    a: "Both, deliberately. You get access to the AFK Revenue Diagnostic instrument. A founder leads the engagement — interpreting your evidence, pressure-testing assumptions, and delivering the executive memo. This is not self-serve SaaS at scale yet.",
  },
  {
    q: "What evidence do I need?",
    a: "At minimum: a completed Revenue Audit (guided in-platform) plus whatever you already have — invoice exports, CRM lead lists, or transaction spreadsheets. More evidence raises confidence; the engine will not invent numbers where data is missing.",
  },
  {
    q: "How is the primary constraint chosen?",
    a: "AFK ranks constraints by revenue exposure and fixability — not whichever dimension has the lowest score in isolation. Every finding cites the evidence that triggered it. You will see the formula and confidence level, not a black-box score.",
  },
  {
    q: "What happens after the diagnostic?",
    a: "You receive a 90-day treatment protocol tied to your primary constraint, plus one follow-up diagnosis checkpoint. Implementation is yours or your team's — we do not run your sales motion for you.",
  },
  {
    q: "Who is this not for?",
    a: "Pre-revenue startups, businesses without a repeatable offer, or teams looking for a CRM/automation suite. AFK diagnoses revenue constraints — it does not replace your ops stack.",
  },
  {
    q: "Is the method validated on businesses like mine?",
    a: "AFK is an early-stage diagnostic. The sample business uses synthetic data, and the scoring rules are still hypotheses. A founder reviews each client diagnosis with you. We do not claim industry-calibrated benchmarks or guaranteed revenue growth.",
  },
];

function navHeader() {
  const authed = API.isAuthenticated();
  return `
    <header class="nav-header">
      <a href="#" class="nav-logo" style="text-decoration:none;">
        <span style="background:linear-gradient(135deg, hsl(var(--primary)), #a855f7); width:28px; height:28px; border-radius:6px; display:inline-flex; align-items:center; justify-content:center; color:white; font-weight:800; font-size:0.9rem;">A</span>
        AFK · Revenue Clarity
      </a>
      <nav class="nav-links">
        <a href="#" data-offer-scroll="deliverables">Deliverables</a>
        <a href="#" data-offer-scroll="process">Process</a>
        <a href="#" data-offer-scroll="pricing">Pricing</a>
        <a href="#" data-offer-scroll="faq">FAQ</a>
        ${authed
          ? `<a href="#diagnosis" class="btn btn-primary btn-sm">Your diagnosis</a>`
          : `<button type="button" class="btn btn-secondary btn-sm" id="offer-nav-demo">Try demo</button>`}
      </nav>
    </header>`;
}

async function startDemo(btn) {
  if (btn) {
    btn.disabled = true;
    const label = btn.textContent;
    btn.textContent = "Loading…";
    try {
      await runDemo();
    } catch (err) {
      UI.toast(err.message || "Demo unavailable.", "error");
      btn.disabled = false;
      btn.textContent = label;
    }
    return;
  }
  await runDemo();
}

async function runDemo() {
  const data = await API.post("/auth/demo", {});
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("user_profile", JSON.stringify(data.user));
  if (data.demo) localStorage.setItem("afk_demo_session", "true");
  UI.toast("Sample diagnosis loaded.", "success");
  window.dispatchEvent(new Event("auth-changed"));
  AppRouter.navigate("#diagnosis");
}

function openApplicationModal() {
  UI.modal(
    "Apply for Revenue Constraint Diagnostic",
    `
      <p style="font-size:0.82rem;color:hsl(var(--text-secondary));margin:0 0 1rem;line-height:1.5;">
        Tell us about your business. We reply within one business day with fit confirmation and next steps.
      </p>
      <div class="form-group">
        <label class="form-label">Full name</label>
        <input type="text" class="form-control" name="full_name" required placeholder="Jordan Lee">
      </div>
      <div class="form-group">
        <label class="form-label">Work email</label>
        <input type="email" class="form-control" name="email" required placeholder="you@youragency.com">
      </div>
      <div class="form-group">
        <label class="form-label">Company</label>
        <input type="text" class="form-control" name="company" required placeholder="Meridian Growth Co.">
      </div>
      <div class="form-group">
        <label class="form-label">Monthly revenue (approx.)</label>
        <select class="form-control" name="revenue_band">
          <option value="">Select a band</option>
          ${REVENUE_BANDS.map((b) => `<option value="${b}">${b}</option>`).join("")}
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">Biggest revenue worry right now</label>
        <input type="text" class="form-control" name="primary_worry" placeholder="e.g. referrals dried up, close rate slipped">
      </div>
      <div class="form-group">
        <label class="form-label">Anything else? (optional)</label>
        <textarea class="form-control" name="message" rows="3" placeholder="Team size, industry, timeline…"></textarea>
      </div>
    `,
    async (values) => {
      if (!values.full_name?.trim()) throw new Error("Full name is required");
      if (!values.email?.trim()) throw new Error("Work email is required");
      if (!values.company?.trim()) throw new Error("Company is required");
      const res = await API.post("/offer/inquiry", {
        full_name: values.full_name.trim(),
        email: values.email.trim(),
        company: values.company.trim(),
        revenue_band: values.revenue_band || "",
        primary_worry: values.primary_worry?.trim() || "",
        message: values.message?.trim() || "",
      });
      UI.toast(res.message, "success");
    },
    { submitLabel: "Submit application" },
  );
}

export function renderOffer(container) {
  container.innerHTML = `
    <div class="offer-page">
      ${navHeader()}
      <main class="offer-main">
        <section class="offer-hero">
          <div class="offer-hero-glow"></div>
          <span class="offer-kicker">Concierge · 2-week engagement</span>
          <h1>Revenue Constraint Diagnostic</h1>
          <p class="offer-hero-lead">
            Find where revenue is actually stuck — with evidence, not gut feel.
            A founder-led diagnostic using the AFK instrument: audit, uploaded data, executive diagnosis, and a 90-day treatment protocol.
          </p>
          <div class="offer-hero-ctas">
            <button type="button" class="btn btn-primary btn-lg" id="offer-apply-hero">Apply for diagnostic</button>
            <button type="button" class="btn btn-secondary btn-lg" id="offer-demo-hero">See sample diagnosis</button>
          </div>
          <p class="offer-hero-note">
            Built for B2B service founders · ₹5L–₹25L/mo typical range ·
            AFK will say "insufficient evidence" rather than guess.
          </p>
        </section>

        <section class="offer-section" id="deliverables">
          <div class="offer-section-head">
            <h2>What you walk away with</h2>
            <p>A diagnosis you can inspect, discuss, and act on with your team.</p>
          </div>
          <div class="offer-deliverables">
            <article class="offer-deliverable">
              <div class="offer-deliverable-num">01 · Diagnosis</div>
              <h3>Executive Revenue Diagnosis</h3>
              <p>Health score, risk level, and primary constraint — every finding cites audit answers or uploaded evidence. Shareable PDF included.</p>
            </article>
            <article class="offer-deliverable">
              <div class="offer-deliverable-num">02 · Evidence</div>
              <h3>Contradiction map</h3>
              <p>Where your stated beliefs diverge from invoice/CRM data — e.g. "pricing feels fine" vs 22% average discounting.</p>
            </article>
            <article class="offer-deliverable">
              <div class="offer-deliverable-num">03 · Protocol</div>
              <h3>90-day treatment plan</h3>
              <p>Constraint-specific playbook with tracked outcomes — baseline dimension score recorded when you start treatment.</p>
            </article>
            <article class="offer-deliverable">
              <div class="offer-deliverable-num">04 · Follow-up</div>
              <h3>Checkpoint diagnosis</h3>
              <p>One follow-up run after ~90 days to measure dimension movement — not revenue claims until evidence confirms.</p>
            </article>
          </div>
        </section>

        <section class="offer-section">
          <div class="offer-section-head">
            <h2>Who this is for</h2>
          </div>
          <div class="offer-fit-grid">
            <div class="offer-fit-card is-yes">
              <h3>Good fit</h3>
              <ul>
                <li>B2B agencies, consultancies, or professional services</li>
                <li>₹5L–₹25L/mo revenue with a repeatable offer</li>
                <li>Founder still involved in sales or delivery</li>
                <li>Can export invoices, leads, or transaction data</li>
              </ul>
            </div>
            <div class="offer-fit-card is-no">
              <h3>Not yet</h3>
              <ul>
                <li>Pre-revenue or still finding product-market fit</li>
                <li>Looking for CRM, automation, or outbound tooling</li>
                <li>Expecting AFK to run implementation for you</li>
                <li>Need guaranteed revenue uplift forecasts</li>
              </ul>
            </div>
          </div>
        </section>

        <section class="offer-section" id="process">
          <div class="offer-section-head">
            <h2>How the two weeks run</h2>
            <p>Founder-led, async-friendly. Most work happens inside the platform.</p>
          </div>
          <div class="offer-steps">
            <div class="offer-step">
              <h3>Application + fit call</h3>
              <p>30-minute call to confirm scope, evidence availability, and timeline.</p>
              <span>Day 0–2</span>
            </div>
            <div class="offer-step">
              <h3>Audit + evidence upload</h3>
              <p>Complete the Revenue Audit and upload whatever exports you have — invoices, CRM, transactions.</p>
              <span>Day 2–7</span>
            </div>
            <div class="offer-step">
              <h3>Diagnosis session</h3>
              <p>Walk through the executive diagnosis live — primary constraint, confidence levels, and contradictions.</p>
              <span>Day 7–10</span>
            </div>
            <div class="offer-step">
              <h3>Treatment handoff</h3>
              <p>Start the 90-day protocol in-platform. Checkpoint diagnosis scheduled before close.</p>
              <span>Day 10–14</span>
            </div>
          </div>
        </section>

        <section class="offer-section" id="pricing">
          <div class="offer-section-head">
            <h2>Investment</h2>
            <p>One engagement. No recurring platform fee during the diagnostic window.</p>
          </div>
          <div class="offer-pricing-wrap">
            <div class="offer-pricing-card">
              <span class="offer-kicker">Revenue Constraint Diagnostic</span>
              <p class="offer-price">₹49,000</p>
              <p class="offer-price-note">One-time · 2-week concierge engagement · GST extra if applicable</p>
              <ul>
                <li>Full Revenue Audit + evidence review</li>
                <li>Executive diagnosis PDF</li>
                <li>90-day treatment protocol + tracking</li>
                <li>One 90-day checkpoint diagnosis</li>
                <li>Platform access for engagement period</li>
              </ul>
              <button type="button" class="btn btn-primary" style="width:100%;" id="offer-apply-pricing">Apply now</button>
            </div>
          </div>
        </section>

        <section class="offer-section">
          <div class="offer-section-head">
            <h2>What we will and won't claim</h2>
          </div>
          <div class="offer-honesty">
            <div class="offer-honesty-grid">
              <div>
                <h3 style="color:#166534;">We will</h3>
                <ul>
                  <li>Show formulas behind opportunity ranges</li>
                  <li>Label confidence and missing evidence explicitly</li>
                  <li>Rank one primary constraint with reasoning</li>
                  <li>Track treatment outcomes against dimension scores</li>
                </ul>
              </div>
              <div>
                <h3 style="color:#9f2d1f;">We won't</h3>
                <ul>
                  <li>Guarantee revenue uplift from audit answers alone</li>
                  <li>Present AI prose as audited financial advice</li>
                  <li>Claim calibrated accuracy before 10 observed cases</li>
                  <li>Sell you CRM or automation you don't need</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        <section class="offer-section" id="faq">
          <div class="offer-section-head">
            <h2>Questions</h2>
          </div>
          <div class="offer-faq">
            ${FAQ.map((item, i) => `
              <div class="offer-faq-item" data-faq="${i}">
                <button type="button" class="offer-faq-q">
                  ${item.q}
                  <span class="offer-faq-chevron">▾</span>
                </button>
                <div class="offer-faq-a">${item.a}</div>
              </div>`).join("")}
          </div>
        </section>

        <section class="offer-final-cta">
          <h2>Ready to see where revenue is stuck?</h2>
          <p>Apply for the diagnostic, or explore the sample business first — same instrument, synthetic data.</p>
          <div class="offer-hero-ctas">
            <button type="button" class="btn btn-primary btn-lg" id="offer-apply-final">Apply for diagnostic</button>
            <button type="button" class="btn btn-secondary btn-lg" id="offer-demo-final">Try demo business</button>
          </div>
        </section>
      </main>

      <footer class="offer-footer">
        <div class="offer-footer-inner">
          <span>© 2026 AFK Agency. Revenue clarity for service founders.</span>
          <div class="offer-footer-links">
            <a href="#offer">Offer</a>
            <a href="#login">Sign in</a>
            <a href="#register">Create organisation</a>
          </div>
        </div>
      </footer>
    </div>
  `;

  container.querySelectorAll("[id^='offer-apply']").forEach((btn) => {
    btn.addEventListener("click", openApplicationModal);
  });

  ["#offer-demo-hero", "#offer-demo-final", "#offer-nav-demo"].forEach((sel) => {
    const el = container.querySelector(sel);
    if (el) el.addEventListener("click", () => startDemo(el));
  });

  container.querySelectorAll(".offer-faq-q").forEach((btn) => {
    btn.addEventListener("click", () => {
      const item = btn.closest(".offer-faq-item");
      const wasOpen = item.classList.contains("is-open");
      container.querySelectorAll(".offer-faq-item").forEach((x) => x.classList.remove("is-open"));
      if (!wasOpen) item.classList.add("is-open");
    });
  });

  container.querySelectorAll("[data-offer-scroll]").forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const id = link.getAttribute("data-offer-scroll");
      const target = container.querySelector(`#${id}`);
      if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
}
