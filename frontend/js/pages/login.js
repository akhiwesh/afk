import { API } from "../api.js";
import { UI } from "../ui.js";
import { AppRouter } from "../router.js";

export function renderLogin(container) {
  container.innerHTML = `
    <div style="min-height:100vh; display:flex; align-items:center; justify-content:center; background-color:hsl(var(--bg-app)); padding:2rem; box-sizing:border-box;">
      <div class="card glass-card" style="width:100%; max-width:400px; padding:2.5rem; border-color:hsl(var(--border)); box-shadow:var(--shadow-lg);">
        <div style="text-align:center; margin-bottom:2rem;">
          <a href="#" style="font-family:var(--font-display); font-weight:700; font-size:1.5rem; color:hsl(var(--text-primary)); display:flex; align-items:center; justify-content:center; gap:0.5rem; margin-bottom:0.5rem;">
            <span style="background:linear-gradient(135deg, hsl(var(--primary)), #a855f7); width:32px; height:32px; border-radius:6px; display:inline-flex; align-items:center; justify-content:center; color:white; font-weight:800; font-size:1rem;">A</span>
            AFK Platform
          </a>
          <p style="font-size:0.85rem; color:hsl(var(--text-secondary));">Revenue clarity for service businesses — sign in to your organisation</p>
        </div>

        <form id="login-form">
          <div class="form-group">
            <label class="form-label" for="login-email">Email Address</label>
            <input type="email" id="login-email" class="form-control" placeholder="you@youragency.com" required>
          </div>
          
          <div class="form-group" style="position:relative;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
              <label class="form-label" for="login-password" style="margin:0;">Password</label>
              <a href="#forgot" style="font-size:0.75rem; color:hsl(var(--text-muted));" id="forgot-link">Forgot password?</a>
            </div>
            <input type="password" id="login-password" class="form-control" placeholder="••••••••" required>
          </div>

          <button type="submit" class="btn btn-primary" style="width:100%; margin-top:1.25rem; font-weight:600;">Sign In</button>
        </form>

        <div style="display:flex; align-items:center; margin:1.5rem 0; gap:8px;">
          <div style="flex-grow:1; height:1px; background-color:hsl(var(--border)/0.5);"></div>
          <span style="font-size:0.7rem; color:hsl(var(--text-muted)); text-transform:uppercase;">Or explore first</span>
          <div style="flex-grow:1; height:1px; background-color:hsl(var(--border)/0.5);"></div>
        </div>

        <button type="button" class="btn btn-secondary" id="demo-session-btn" style="width:100%; font-weight:600;">
          Try demo business →
        </button>
        <p style="font-size:0.72rem; text-align:center; color:hsl(var(--text-muted)); margin-top:0.65rem; line-height:1.45;">
          Sample agency with a completed Revenue Audit — no signup required.
        </p>

        <p style="font-size:0.75rem; text-align:center; color:hsl(var(--text-muted)); margin-top:2rem;">
          Don't have an account? <a href="#register" style="color:hsl(var(--primary)); font-weight:600;" id="to-register-btn">Create organization</a>
          · <a href="#offer" style="color:hsl(var(--primary)); font-weight:600;">View diagnostic offer</a>
        </p>
        <div id="local-login-hint" style="display:none;margin-top:1.25rem;padding:0.85rem 1rem;border-radius:8px;border:1px solid hsl(var(--border));background:hsl(var(--bg-subtle,220 14% 12%));font-size:0.72rem;line-height:1.55;color:hsl(var(--text-muted));"></div>
      </div>
    </div>
  `;

  const hint = container.querySelector("#local-login-hint");
  if (hint && (location.hostname === "localhost" || location.hostname === "127.0.0.1")) {
    hint.style.display = "block";
    hint.innerHTML = `
      <strong style="color:hsl(var(--text-primary));">Local testing</strong><br>
      Use <strong>Try demo business</strong> for a one-click walkthrough, or register your own org.<br>
      <span style="opacity:0.9;">Legacy seed: <code style="font-size:0.7rem;">admin@afk.agency</code> / <code style="font-size:0.7rem;">password123</code> (requires <code>AFK_SEED_DEMO=true</code>)</span>`;
  }

  // Submit Handler
  const form = container.querySelector("#login-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = container.querySelector("#login-email").value;
    const password = container.querySelector("#login-password").value;

    try {
      const data = await API.post("/auth/login", { email, password });
      
      // Store locally
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user_profile", JSON.stringify(data.user));
      
      UI.toast("Welcome back!", "success");
      
      // Notify parent router shell
      window.dispatchEvent(new Event("auth-changed"));
      AppRouter.navigate("#diagnosis");
    } catch (err) {
      const msg = err.message || "Incorrect email or password";
      UI.toast(msg.includes("Incorrect") ? `${msg} — try Create organization if you haven't registered yet.` : msg, "error");
    }
  });

  container.querySelector("#demo-session-btn").addEventListener("click", async () => {
    const btn = container.querySelector("#demo-session-btn");
    btn.disabled = true;
    btn.textContent = "Loading demo…";
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
      btn.disabled = false;
      btn.textContent = "Try demo business →";
    }
  });

  // Forgot password handler
  container.querySelector("#forgot-link").addEventListener("click", (e) => {
    e.preventDefault();
    UI.modal("Reset Password", `
      <div class="form-group">
        <label class="form-label">Email Address</label>
        <input type="email" class="form-control" name="email" value="${container.querySelector('#login-email').value}" placeholder="you@youragency.com">
      </div>
    `, async (values) => {
      if (!values.email) throw new Error("Email address required");
      await API.post("/auth/forgot-password", { email: values.email });
      UI.toast("Recovery sequence sent to inbox.", "success");
    });
  });
}
