import { API } from "../api.js";
import { UI } from "../ui.js";

export async function renderCRM(container) {
  container.innerHTML = `<div style="display:flex; justify-content:center; align-items:center; height:50vh;"><span style="color:hsl(var(--text-muted)); font-size:0.9rem;">Fetching contacts...</span></div>`;

  try {
    const clients = await API.get("/crm/clients");
    renderList(container, clients);
  } catch (err) {
    container.innerHTML = `<div class="card" style="border-color:hsl(var(--danger)/0.5); padding:2rem; text-align:center;"><h3>Error loading CRM</h3><p>${err.message}</p></div>`;
  }
}

function renderList(container, clients) {
  container.innerHTML = `
    <div class="breadcrumb">Workspace / CRM</div>
    <div class="content-header">
      <h1>CRM Leads & Pipeline</h1>
      <button class="btn btn-primary btn-sm" id="add-client-btn">
        <span style="font-size:1.1rem; line-height:0; display:inline-block; font-weight:700;">+</span> Add Client
      </button>
    </div>

    <!-- Active Pipeline Stage Counts Summary -->
    <div class="grid grid-cols-4" style="gap:1rem; margin-bottom:2rem;">
      ${["contact", "qualified", "proposal", "won"].map(stage => {
        const count = clients.filter(c => c.pipeline_stage === stage).length;
        return `
          <div class="card glass-card" style="padding:1rem; display:flex; align-items:center; justify-content:space-between;">
            <div>
              <span style="font-size:0.75rem; text-transform:uppercase; color:hsl(var(--text-muted)); font-weight:600;">${stage}</span>
              <h3 style="margin:0; font-size:1.25rem; font-family:var(--font-display);">${count}</h3>
            </div>
            <span style="background-color:hsl(var(--primary)/0.1); color:hsl(var(--primary)); padding:0.25rem 0.5rem; border-radius:var(--radius-sm); font-size:0.7rem; font-weight:600;">Stage</span>
          </div>
        `;
      }).join('')}
    </div>

    <!-- Leads Table -->
    <div class="card" style="padding:0; overflow:hidden;">
      <table style="width:100%; border-collapse:collapse; text-align:left; font-size:0.875rem;">
        <thead>
          <tr style="border-bottom:1px solid hsl(var(--border)); background-color:hsl(var(--bg-sidebar)/0.5);">
            <th style="padding:1rem;">Name</th>
            <th style="padding:1rem;">Company</th>
            <th style="padding:1rem;">Email</th>
            <th style="padding:1rem;">Pipeline Stage</th>
            <th style="padding:1rem;">Status</th>
            <th style="padding:1rem; text-align:right;">Actions</th>
          </tr>
        </thead>
        <tbody>
          ${clients.length === 0 
            ? `<tr><td colspan="6" style="padding:2rem; text-align:center; color:hsl(var(--text-muted));">No CRM records found.</td></tr>`
            : clients.map(client => `
              <tr style="border-bottom:1px solid hsl(var(--border)/0.5); transition:background-color var(--transition-fast);" class="table-row-hover">
                <td style="padding:1rem; font-weight:600;">${client.name}</td>
                <td style="padding:1rem; color:hsl(var(--text-secondary));">${client.company}</td>
                <td style="padding:1rem; font-family:monospace; font-size:0.8rem;">${client.email}</td>
                <td style="padding:1rem;">
                  <select class="form-control stage-selector" data-id="${client.id}" style="width:auto; padding:0.25rem 0.5rem; font-size:0.75rem; border-color:hsl(var(--border));">
                    ${["contact", "qualified", "proposal", "negotiation", "won", "lost"].map(st => `
                      <option value="${st}" ${client.pipeline_stage === st ? "selected" : ""}>${st.toUpperCase()}</option>
                    `).join('')}
                  </select>
                </td>
                <td style="padding:1rem;">
                  <span class="priority-badge ${client.status === 'active' ? 'priority-low' : 'priority-medium'}" style="font-size:0.65rem;">
                    ${client.status}
                  </span>
                </td>
                <td style="padding:1rem; text-align:right;">
                  <button class="btn btn-secondary btn-sm view-client-btn" data-id="${client.id}">View Details</button>
                </td>
              </tr>
            `).join('')
          }
        </tbody>
      </table>
    </div>
  `;

  // Apply row hover styling programmatically
  const rowStyle = document.createElement("style");
  rowStyle.innerHTML = `
    .table-row-hover:hover {
      background-color: hsl(var(--border) / 0.15);
    }
  `;
  document.head.appendChild(rowStyle);

  // Hook Add Client Modal
  container.querySelector("#add-client-btn").addEventListener("click", () => {
    UI.modal("Add New CRM Client", `
      <div class="form-group">
        <label class="form-label">Client Name</label>
        <input type="text" class="form-control" name="name" required placeholder="John Doe">
      </div>
      <div class="form-group">
        <label class="form-label">Company Name</label>
        <input type="text" class="form-control" name="company" required placeholder="Acme Corp">
      </div>
      <div class="form-group">
        <label class="form-label">Email Address</label>
        <input type="email" class="form-control" name="email" required placeholder="john@acme.com">
      </div>
      <div class="form-group">
        <label class="form-label">Phone Number</label>
        <input type="text" class="form-control" name="phone" placeholder="+1 (555) 000-0000">
      </div>
    `, async (values) => {
      if (!values.name || !values.company || !values.email) {
        throw new Error("Please fill in name, company and email.");
      }
      await API.post("/crm/clients", values);
      UI.toast("Client added to CRM.", "success");
      renderCRM(container); // Reload
    });
  });

  // Hook stage updates
  const stageSelectors = container.querySelectorAll(".stage-selector");
  stageSelectors.forEach(sel => {
    sel.addEventListener("change", async (e) => {
      const clientId = e.target.getAttribute("data-id");
      const newStage = e.target.value;
      try {
        await API.put(`/crm/clients/${clientId}`, { pipeline_stage: newStage });
        UI.toast("Pipeline stage updated.", "success");
      } catch (err) {
        UI.toast(err.message || "Failed to update stage", "error");
      }
    });
  });

  // Hook View Details Button
  const viewBtns = container.querySelectorAll(".view-client-btn");
  viewBtns.forEach(btn => {
    btn.addEventListener("click", (e) => {
      const clientId = e.target.getAttribute("data-id");
      renderClientDetails(container, clientId);
    });
  });
}

async function renderClientDetails(container, clientId) {
  container.innerHTML = `<div style="display:flex; justify-content:center; align-items:center; height:50vh;"><span style="color:hsl(var(--text-muted));">Opening profile details...</span></div>`;
  
  try {
    const details = await API.get(`/crm/clients/${clientId}`);
    const client = details.client;
    const notes = details.notes;
    
    container.innerHTML = `
      <div class="breadcrumb">CRM / Client Directory / ${client.name}</div>
      <div class="content-header">
        <h1>${client.name}</h1>
        <button class="btn btn-secondary btn-sm" id="back-to-crm-btn">Back to CRM List</button>
      </div>

      <div style="display:grid; grid-template-columns: 1fr 2fr; gap:1.5rem;">
        <!-- Left info card -->
        <div class="card glass-card" style="height:fit-content;">
          <h3 style="border-bottom:1px solid hsl(var(--border)/0.5); padding-bottom:0.75rem; margin-bottom:1rem;">Profile Overview</h3>
          
          <div style="display:flex; flex-direction:column; gap:1rem; font-size:0.85rem;">
            <div>
              <span style="font-size:0.7rem; color:hsl(var(--text-muted)); display:block; text-transform:uppercase;">Company</span>
              <strong>${client.company}</strong>
            </div>
            <div>
              <span style="font-size:0.7rem; color:hsl(var(--text-muted)); display:block; text-transform:uppercase;">Email</span>
              <strong>${client.email}</strong>
            </div>
            <div>
              <span style="font-size:0.7rem; color:hsl(var(--text-muted)); display:block; text-transform:uppercase;">Phone</span>
              <strong>${client.phone || "—"}</strong>
            </div>
            <div>
              <span style="font-size:0.7rem; color:hsl(var(--text-muted)); display:block; text-transform:uppercase;">Pipeline Stage</span>
              <span class="priority-badge priority-low">${client.pipeline_stage.toUpperCase()}</span>
            </div>
          </div>
        </div>

        <!-- Notes and History -->
        <div style="display:flex; flex-direction:column; gap:1.5rem;">
          <div class="card">
            <h3>Interaction History & Notes</h3>
            
            <!-- Write Note Form -->
            <form id="add-note-form" style="margin-bottom:1.5rem;">
              <div class="form-group">
                <textarea id="note-content" class="form-control" rows="3" placeholder="Add interaction summary..." required style="resize:none;"></textarea>
              </div>
              <button type="submit" class="btn btn-primary btn-sm">Save Note</button>
            </form>

            <!-- Notes List -->
            <div style="display:flex; flex-direction:column; gap:1rem;" id="notes-list-container">
              ${notes.length === 0 
                ? `<span style="font-size:0.85rem; color:hsl(var(--text-muted));">No interactions logged yet.</span>`
                : notes.map(note => `
                  <div style="background-color:hsl(var(--bg-sidebar)/0.5); border:1px solid hsl(var(--border)/0.5); padding:1rem; border-radius:var(--radius-md); font-size:0.85rem;">
                    <p style="margin:0 0 0.5rem 0; color:hsl(var(--text-primary));">${note.content}</p>
                    <span style="font-size:0.7rem; color:hsl(var(--text-muted));">${new Date(note.created_at).toLocaleString()}</span>
                  </div>
                `).join('')
              }
            </div>
          </div>
        </div>
      </div>
    `;

    // Hook Back Button
    container.querySelector("#back-to-crm-btn").addEventListener("click", () => renderCRM(container));

    // Hook Add Note
    const noteForm = container.querySelector("#add-note-form");
    noteForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const content = container.querySelector("#note-content").value;
      try {
        await API.post(`/crm/clients/${clientId}/notes`, { content });
        UI.toast("Interaction note saved.", "success");
        renderClientDetails(container, clientId); // Refresh
      } catch (err) {
        UI.toast(err.message || "Failed to save note", "error");
      }
    });

  } catch (err) {
    container.innerHTML = `<div class="card" style="border-color:hsl(var(--danger)/0.5); padding:2rem; text-align:center;"><h3>Error opening profile</h3><p>${err.message}</p></div>`;
  }
}
