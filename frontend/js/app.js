import { API } from "./api.js";
import { AppRouter } from "./router.js";
import { UI } from "./ui.js";

// Page imports
import { renderLanding } from "./pages/landing.js";
import { renderLogin } from "./pages/login.js";
import { renderRegister } from "./pages/register.js";
import { renderHealth } from "./pages/health.js";
import { renderAudit } from "./pages/audit.js";
import { renderEvidence } from "./pages/evidence.js";
import { renderTwin } from "./pages/twin.js";
import { renderAdmin } from "./pages/admin.js";

/** Revenue product nav — audit → evidence → diagnosis → twin. Legacy routes redirect. */
const REVENUE_NAV = [
  { id: "audit", hash: "#audit", label: "Revenue Audit", icon: "content" },
  { id: "evidence", hash: "#evidence", label: "Evidence", icon: "billing" },
  { id: "diagnosis", hash: "#diagnosis", label: "Diagnosis", icon: "home" },
  { id: "twin", hash: "#twin", label: "Business Twin", icon: "briefcase" },
];

// Unified Application shell mounting logic
class App {
  constructor() {
    this.appMountNode = document.getElementById("app");
    this.theme = localStorage.getItem("theme") || "dark";
    
    // Set theme attribute initially on HTML tag
    document.documentElement.setAttribute("data-theme", this.theme);
    
    this.initRoutes();
    
    // Listen for auth change notifications
    window.addEventListener("auth-changed", () => this.handleAuthChange());
  }

  initRoutes() {
    // Public paths
    AppRouter.addRoute("#", (param) => this.renderPublicView(renderLanding));
    AppRouter.addRoute("#login", (param) => this.renderPublicView(renderLogin));
    AppRouter.addRoute("#register", (param) => this.renderPublicView(renderRegister));

    // Private paths (requires login) — Revenue Intelligence surface
    AppRouter.addRoute("#diagnosis", (param) => this.renderPrivateView(renderHealth, "diagnosis"), true);
    AppRouter.addRoute("#health", (param) => { window.location.hash = "#diagnosis"; }, true);
    AppRouter.addRoute("#audit", (param) => this.renderPrivateView(renderAudit, "audit"), true);
    AppRouter.addRoute("#evidence", (param) => this.renderPrivateView(renderEvidence, "evidence"), true);
    AppRouter.addRoute("#twin", (param) => this.renderPrivateView(renderTwin, "twin"), true);
    AppRouter.addRoute("#admin", (param) => this.renderPrivateView(renderAdmin, "admin"), true);
    // Legacy / parked routes → revenue surface
    AppRouter.addRoute("#dashboard", () => { window.location.hash = "#diagnosis"; }, true);
    AppRouter.addRoute("#analyst", () => { window.location.hash = "#diagnosis"; }, true);
    AppRouter.addRoute("#data", () => { window.location.hash = "#evidence"; }, true);
    AppRouter.addRoute("#crm", () => { window.location.hash = "#evidence"; }, true);
  }

  renderPublicView(renderFn) {
    // Clear shell wrappers and render directly in mount node
    this.appMountNode.innerHTML = "";
    renderFn(this.appMountNode);
  }

  renderPrivateView(renderFn, activeMenuItem) {
    const user = API.getUser();
    
    // Renders the dashboard shell framework if it's not present
    let layoutEl = this.appMountNode.querySelector(".dashboard-layout");
    if (!layoutEl) {
      this.appMountNode.innerHTML = `
        <div class="dashboard-layout">
          <!-- Navigation Sidebar -->
          <aside class="sidebar">
            <div class="sidebar-logo">
              <span class="sidebar-logo-mark">A</span>
              <span>AFK · Revenue Clarity</span>
            </div>

            <div id="onboarding-checklist" class="onboarding-checklist"></div>

            <p class="sidebar-section-label">Revenue diagnostic</p>
            <nav class="sidebar-menu">
              ${REVENUE_NAV.map((item) => `
                <a href="${item.hash}" class="sidebar-item" id="menu-${item.id}">
                  ${UI.icon(item.icon)} ${item.label}
                </a>`).join("")}
            </nav>

            ${user && user.role === "admin" ? `
              <p class="sidebar-section-label sidebar-section-label--spaced">Admin</p>
              <nav class="sidebar-menu sidebar-menu--compact">
                <a href="#admin" class="sidebar-item" id="menu-admin">
                  ${UI.icon("settings")} Settings
                </a>
              </nav>` : ""}

            <div class="sidebar-footer">
              <div class="user-profile">
                <div class="avatar">${user ? user.full_name.split(' ').map(n => n[0]).join('') : "U"}</div>
                <div class="user-info">
                  <span class="user-name">${user ? user.full_name : "User Profile"}</span>
                  <span class="user-role">${user ? user.role.toUpperCase() : ""}</span>
                </div>
              </div>
              <div style="display:flex; gap:8px; align-items:center;">
                <button class="btn btn-secondary btn-sm" id="theme-toggle-btn" style="padding:0.4rem; font-size:0.9rem;">
                  ${this.theme === 'dark' ? UI.icon('sun') : UI.icon('moon')}
                </button>
                <button class="btn btn-secondary btn-sm" id="logout-btn" style="padding:0.4rem; font-size:0.9rem;" title="Sign Out">
                  ${UI.icon('logout')}
                </button>
              </div>
            </div>
          </aside>

          <!-- Main workspace sheet -->
          <main class="main-content" id="workspace-container"></main>
        </div>
      `;
      layoutEl = this.appMountNode.querySelector(".dashboard-layout");
      
      // Hook logout Action
      layoutEl.querySelector("#logout-btn").addEventListener("click", async () => {
        try {
          await API.post("/auth/logout");
        } catch (e) {
          // Fallback delete
        }
        localStorage.removeItem("access_token");
        localStorage.removeItem("user_profile");
        UI.toast("Signed out successfully.", "success");
        window.dispatchEvent(new Event("auth-changed"));
        AppRouter.navigate("#");
      });

      // Hook Theme Toggle Action
      layoutEl.querySelector("#theme-toggle-btn").addEventListener("click", () => {
        this.theme = this.theme === "dark" ? "light" : "dark";
        localStorage.setItem("theme", this.theme);
        document.documentElement.setAttribute("data-theme", this.theme);
        
        // Re-render button icon
        const btn = layoutEl.querySelector("#theme-toggle-btn");
        btn.innerHTML = this.theme === 'dark' ? UI.icon('sun') : UI.icon('moon');
        UI.toast(`Switched to ${this.theme} mode.`, "success");
      });
    }

    // Update active state class in sidebar
    const menuItems = layoutEl.querySelectorAll(".sidebar-item");
    menuItems.forEach(item => item.classList.remove("active"));
    
    const activeEl = layoutEl.querySelector(`#menu-${activeMenuItem}`);
    if (activeEl) {
      activeEl.classList.add("active");
    }

    // Revenue clarity checklist (evidence → audit → diagnosis)
    this.renderOnboardingChecklist(layoutEl);

    // Render inside the nested workspace container
    const workspaceContainer = layoutEl.querySelector("#workspace-container");
    renderFn(workspaceContainer);
  }

  async renderOnboardingChecklist(layoutEl) {
    const host = layoutEl.querySelector("#onboarding-checklist");
    if (!host) return;
    try {
      const data = await API.get("/intelligence/onboarding");
      const steps = data.steps || [];
      const allDone = steps.every((s) => s.done);
      if (allDone) {
        host.innerHTML = "";
        return;
      }
      host.innerHTML = `
        <p class="sidebar-section-label">Your clarity path</p>
        ${steps.map((s) => `
          <a href="${s.href}" class="onboarding-step ${s.done ? "is-done" : ""}">
            <span class="onboarding-step-icon">${s.done ? "✓" : "○"}</span>
            <span>${s.label}${s.id === "audit" && !s.done ? ` (${s.progress}/${s.total})` : ""}${s.id === "evidence" && s.progress ? ` (${s.progress})` : ""}</span>
          </a>`).join("")}
      `;
    } catch {
      host.innerHTML = "";
    }
  }

  handleAuthChange() {
    // Reset core shell to force redrawing sidebar or public view layout structure
    this.appMountNode.innerHTML = "";
  }
}

// Initialise Application
document.addEventListener("DOMContentLoaded", () => {
  window.appInstance = new App();
});
