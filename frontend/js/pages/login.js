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
          <span style="font-size:0.7rem; color:hsl(var(--text-muted)); text-transform:uppercase;">Or continue with</span>
          <div style="flex-grow:1; height:1px; background-color:hsl(var(--border)/0.5);"></div>
        </div>

        <button class="btn btn-secondary" id="google-login-btn" style="width:100%; font-weight:500;">
          <svg style="width:16px; height:16px; margin-right:4px;" viewBox="0 0 24 24">
            <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
            <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
            <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
            <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
          </svg>
          Google Account
        </button>

        <p style="font-size:0.75rem; text-align:center; color:hsl(var(--text-muted)); margin-top:2rem;">
          Don't have an account? <a href="#register" style="color:hsl(var(--primary)); font-weight:600;" id="to-register-btn">Create organization</a>
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
      Demo seed is off — register first, or sign in with an existing account.<br>
      <span style="opacity:0.9;">Demo: <code style="font-size:0.7rem;">admin@afk.agency</code> / <code style="font-size:0.7rem;">password123</code><br>
      Wizard test: <code style="font-size:0.7rem;">founder@afk.dev</code> / <code style="font-size:0.7rem;">AfkWizard1</code></span>`;
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

  // Simple alert simulation for OAuth button
  container.querySelector("#google-login-btn").addEventListener("click", () => {
    UI.toast("Google OAuth popup simulated. Sign in with standard email credentials.", "success");
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
