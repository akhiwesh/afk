import { API } from "../api.js";
import { UI } from "../ui.js";
import { AppRouter } from "../router.js";

export function renderRegister(container) {
  container.innerHTML = `
    <div style="min-height:100vh; display:flex; align-items:center; justify-content:center; background-color:hsl(var(--bg-app)); padding:2rem; box-sizing:border-box;">
      <div class="card glass-card" style="width:100%; max-width:400px; padding:2.5rem; border-color:hsl(var(--border)); box-shadow:var(--shadow-lg);">
        <div style="text-align:center; margin-bottom:2rem;">
          <a href="#" style="font-family:var(--font-display); font-weight:700; font-size:1.5rem; color:hsl(var(--text-primary)); display:flex; align-items:center; justify-content:center; gap:0.5rem; margin-bottom:0.5rem;">
            <span style="background:linear-gradient(135deg, hsl(var(--primary)), #a855f7); width:32px; height:32px; border-radius:6px; display:inline-flex; align-items:center; justify-content:center; color:white; font-weight:800; font-size:1rem;">A</span>
            AFK Platform
          </a>
          <p style="font-size:0.85rem; color:hsl(var(--text-secondary));">Create your agency or consultancy — evidence-first revenue diagnosis</p>
        </div>

        <form id="register-form">
          <div class="form-group">
            <label class="form-label" for="reg-org">Organization Name</label>
            <input type="text" id="reg-org" class="form-control" placeholder="Northstar Consulting" required>
          </div>
          
          <div class="form-group">
            <label class="form-label" for="reg-name">Full Name</label>
            <input type="text" id="reg-name" class="form-control" placeholder="Alex Mercer" required>
          </div>
          
          <div class="form-group">
            <label class="form-label" for="reg-email">Email Address</label>
            <input type="email" id="reg-email" class="form-control" placeholder="admin@acme.com" required>
          </div>
          
          <div class="form-group">
            <label class="form-label" for="reg-password">Password</label>
            <input type="password" id="reg-password" class="form-control" placeholder="••••••••" required minlength="8">
            <p style="font-size:0.7rem;color:hsl(var(--text-muted));margin-top:0.35rem;line-height:1.45;">
              At least 8 characters with uppercase, lowercase, and a number (e.g. <code style="font-size:0.68rem;">MyAgency1</code>)
            </p>
          </div>

          <button type="submit" class="btn btn-primary" style="width:100%; margin-top:1.25rem; font-weight:600;">Register Organization</button>
        </form>

        <p style="font-size:0.75rem; text-align:center; color:hsl(var(--text-muted)); margin-top:2rem;">
          Already have an account? <a href="#login" style="color:hsl(var(--primary)); font-weight:600;">Sign In instead</a>
        </p>
      </div>
    </div>
  `;

  // Submit Register Form
  const form = container.querySelector("#register-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const organization_name = container.querySelector("#reg-org").value;
    const full_name = container.querySelector("#reg-name").value;
    const email = container.querySelector("#reg-email").value;
    const password = container.querySelector("#reg-password").value;

    try {
      await API.post("/auth/register", {
        organization_name,
        full_name,
        email,
        password
      });

      const login = await API.post("/auth/login", { email, password });
      localStorage.setItem("access_token", login.access_token);
      localStorage.setItem("user_profile", JSON.stringify(login.user));

      UI.toast("Welcome — let's examine your revenue systems.", "success");
      window.dispatchEvent(new Event("auth-changed"));
      AppRouter.navigate("#audit");
    } catch (err) {
      UI.toast(err.message || "Registration failed", "error");
    }
  });
}
