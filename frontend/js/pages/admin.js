import { API } from "../api.js";
import { UI } from "../ui.js";

export async function renderAdmin(container) {
  container.innerHTML = `<div style="display:flex; justify-content:center; align-items:center; height:50vh;"><span style="color:hsl(var(--text-muted));">Accessing administrative panel...</span></div>`;

  try {
    const users = await API.get("/admin/users");
    const logs = await API.get("/admin/logs");
    const flags = await API.get("/admin/flags");

    renderAdminPanel(container, users, logs, flags);
  } catch (err) {
    container.innerHTML = `
      <div class="card" style="border-color:hsl(var(--danger)/0.5); padding:2.5rem; text-align:center;">
        <h3>Access Restricted</h3>
        <p style="color:hsl(var(--text-muted));">${err.message || "Admin role permissions required."}</p>
      </div>
    `;
  }
}

function renderAdminPanel(container, users, logs, flags) {
  container.innerHTML = `
    <div class="breadcrumb">Settings / Admin</div>
    <div class="content-header">
      <h1>Global System Settings</h1>
    </div>

    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:1.5rem; margin-bottom:2.5rem;">
      <!-- Feature Flags config -->
      <div class="card">
        <h3>Feature Gate flags</h3>
        <p style="font-size:0.75rem; color:hsl(var(--text-muted)); margin-bottom:1.5rem;">Toggle beta platform traits globally.</p>
        
        <div style="display:flex; flex-direction:column; gap:1rem;">
          ${Object.keys(flags).map(key => `
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid hsl(var(--border)/0.3); padding-bottom:0.75rem;">
              <div>
                <strong style="font-size:0.85rem; text-transform:capitalize; display:block;">${key.replace(/_/g, ' ')}</strong>
                <span style="font-size:0.7rem; color:hsl(var(--text-muted));">Identifier: ${key}</span>
              </div>
              <input type="checkbox" class="feature-flag-checkbox" data-flag="${key}" ${flags[key] ? "checked" : ""} style="width:16px; height:16px; accent-color:hsl(var(--primary)); cursor:pointer;">
            </div>
          `).join('')}
        </div>
      </div>

      <!-- Users list -->
      <div class="card" style="display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <h3>Organization Roster</h3>
          <p style="font-size:0.75rem; color:hsl(var(--text-muted)); margin-bottom:1rem;">Manage active access accounts.</p>
          
          <div style="display:flex; flex-direction:column; gap:0.5rem; max-height:220px; overflow-y:auto; padding-right:4px;">
            ${users.map(u => `
              <div style="display:flex; align-items:center; justify-content:space-between; padding:0.65rem; border:1px solid hsl(var(--border)/0.5); border-radius:var(--radius-md); font-size:0.8rem;">
                <div>
                  <strong>${u.full_name}</strong>
                  <span style="font-size:0.7rem; color:hsl(var(--text-muted)); display:block;">${u.email}</span>
                </div>
                <span class="priority-badge ${u.role === 'admin' ? 'priority-high' : 'priority-low'}">${u.role.toUpperCase()}</span>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    </div>

    <!-- Audit logs -->
    <h3>Audit log history</h3>
    <div class="card" style="padding:0; overflow:hidden;">
      <table style="width:100%; border-collapse:collapse; text-align:left; font-size:0.825rem;">
        <thead>
          <tr style="border-bottom:1px solid hsl(var(--border)); background-color:hsl(var(--bg-sidebar)/0.5);">
            <th style="padding:0.75rem 1rem;">Action Trigger</th>
            <th style="padding:0.75rem 1rem;">User ID</th>
            <th style="padding:0.75rem 1rem;">IP Address</th>
            <th style="padding:0.75rem 1rem;">Timestamp</th>
          </tr>
        </thead>
        <tbody>
          ${logs.length === 0 
            ? `<tr><td colspan="4" style="padding:1.5rem; text-align:center; color:hsl(var(--text-muted));">Audit history is empty.</td></tr>`
            : logs.map(l => `
              <tr style="border-bottom:1px solid hsl(var(--border)/0.3);">
                <td style="padding:0.75rem 1rem; font-weight:600; color:hsl(var(--text-primary));">${l.action}</td>
                <td style="padding:0.75rem 1rem; font-family:monospace;">${l.user_email}</td>
                <td style="padding:0.75rem 1rem; color:hsl(var(--text-secondary));">${l.ip_address || "127.0.0.1"}</td>
                <td style="padding:0.75rem 1rem; color:hsl(var(--text-muted));">${new Date(l.created_at).toLocaleString()}</td>
              </tr>
            `).join('')
          }
        </tbody>
      </table>
    </div>
  `;

  // Hook Feature Gates toggles
  const checkboxes = container.querySelectorAll(".feature-flag-checkbox");
  checkboxes.forEach(box => {
    box.addEventListener("change", async (e) => {
      const flagName = box.getAttribute("data-flag");
      const isEnabled = box.checked;
      
      try {
        await API.post("/admin/flags", { flag_name: flagName, is_enabled: isEnabled });
        UI.toast(`Feature flag '${flagName.replace(/_/g, ' ')}' updated.`, "success");
      } catch (err) {
        box.checked = !isEnabled; // Revert checkbox
        UI.toast(err.message || "Failed to toggle flag", "error");
      }
    });
  });
}
