import { API } from "../api.js";
import { UI } from "../ui.js";

export async function renderAutomation(container) {
  container.innerHTML = `<div style="display:flex; justify-content:center; align-items:center; height:50vh;"><span style="color:hsl(var(--text-muted));">Fetching workflows...</span></div>`;

  try {
    const workflows = await API.get("/automation/workflows");
    if (workflows.length === 0) {
      container.innerHTML = `
        <div class="breadcrumb">Workspace / Automation</div>
        <div class="content-header">
          <h1>Automation workflows</h1>
        </div>
        <div class="card" style="text-align:center; padding:3rem;">
          <h3 style="margin-bottom:1rem;">No active workflows</h3>
          <button class="btn btn-primary btn-sm" id="create-first-flow-btn">Create Workflow</button>
        </div>
      `;
      return;
    }
    
    // Select first workflow by default
    const activeFlow = workflows[0];
    const logs = await API.get(`/automation/workflows/${activeFlow.id}/logs`);
    renderBuilder(container, workflows, activeFlow, logs);

  } catch (err) {
    container.innerHTML = `<div class="card" style="border-color:hsl(var(--danger)/0.5); padding:2rem; text-align:center;"><h3>Error loading automation center</h3><p>${err.message}</p></div>`;
  }
}

function renderBuilder(container, workflows, activeFlow, logs) {
  container.innerHTML = `
    <div class="breadcrumb">Automation / Workflows / ${activeFlow.name}</div>
    <div class="content-header">
      <div style="display:flex; align-items:center; gap:12px;">
        <select class="form-control" id="workflow-selector" style="width:auto; font-size:1.15rem; font-weight:700; border:none; padding:0; background:transparent; font-family:var(--font-display); letter-spacing:-0.02em; cursor:pointer;">
          ${workflows.map(w => `<option value="${w.id}" ${w.id === activeFlow.id ? "selected" : ""}>${w.name}</option>`).join('')}
        </select>
      </div>
      
      <button class="btn btn-primary btn-sm" id="test-workflow-btn">
        ⚡ Test Workflow (Simulate)
      </button>
    </div>

    <div style="display:grid; grid-template-columns: 2fr 1fr; gap:1.5rem; height:75vh;">
      <!-- Workflow Graph Builder -->
      <div class="card" style="display:flex; flex-direction:column; justify-content:space-between; position:relative; overflow-y:auto;">
        <div>
          <h3>Visual Pipeline Flow</h3>
          <p style="font-size:0.8rem; color:hsl(var(--text-muted)); margin-bottom:1.5rem;">Visual representation of the workflow compilation nodes.</p>
          
          <div class="workflow-builder" id="nodes-canvas-container">
            ${activeFlow.steps.map((step, idx) => `
              <div class="workflow-node" id="node-${step.id}">
                <div class="workflow-node-icon">${idx === 0 ? "⚡" : "★"}</div>
                <div class="workflow-node-info">
                  <span class="workflow-node-title">${step.name}</span>
                  <span class="workflow-node-type">${step.type}</span>
                </div>
              </div>
              ${idx < activeFlow.steps.length - 1 ? `<div class="workflow-arrow" id="arrow-${step.id}"></div>` : ""}
            `).join('')}
          </div>
        </div>
      </div>

      <!-- Execution Logs Panel -->
      <div class="card" style="display:flex; flex-direction:column; height:100%; box-sizing:border-box;">
        <h3>Simulation Execution Logs</h3>
        <p style="font-size:0.75rem; color:hsl(var(--text-muted)); margin-bottom:1rem;">Real-time timeline analysis records.</p>
        
        <div style="flex-grow:1; overflow-y:auto; display:flex; flex-direction:column; gap:0.75rem;" id="execution-logs-container">
          ${logs.length === 0 
            ? `<span style="font-size:0.85rem; color:hsl(var(--text-muted));">No execution history logged. Click 'Test Workflow' to run.</span>`
            : logs.map(log => `
              <div style="padding:1rem; border:1px solid hsl(var(--border)/0.5); border-radius:var(--radius-md); font-size:0.8rem; background-color:hsl(var(--bg-sidebar)/0.3);" class="log-item-card" data-log-id="${log.id}">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                  <strong style="color:hsl(${log.status === 'success' ? '--success' : '--danger'});">${log.status.toUpperCase()}</strong>
                  <span style="font-size:0.7rem; color:hsl(var(--text-muted));">${new Date(log.created_at).toLocaleTimeString()}</span>
                </div>
                <span style="font-size:0.75rem; color:hsl(var(--text-secondary)); display:block; text-overflow:ellipsis; overflow:hidden; white-space:nowrap;">
                  Trigger payload: ${JSON.stringify(log.trigger_data)}
                </span>
              </div>
            `).join('')
          }
        </div>
      </div>
    </div>
  `;

  // Hooks selector swap
  container.querySelector("#workflow-selector").addEventListener("change", async (e) => {
    const id = parseInt(e.target.value);
    const flow = workflows.find(w => w.id === id);
    const refreshedLogs = await API.get(`/automation/workflows/${id}/logs`);
    renderBuilder(container, workflows, flow, refreshedLogs);
  });

  // Hook Test simulation button
  container.querySelector("#test-workflow-btn").addEventListener("click", () => {
    UI.modal("Trigger Automation Test", `
      <div class="form-group">
        <label class="form-label">Contact Name</label>
        <input type="text" class="form-control" name="name" value="Bruce Wayne" required>
      </div>
      <div class="form-group">
        <label class="form-label">Company Email</label>
        <input type="email" class="form-control" name="email" value="bruce@wayne.corp" required>
      </div>
      <div class="form-group">
        <label class="form-label">Company Size (Employees)</label>
        <input type="number" class="form-control" name="employees" value="120" required>
      </div>
    `, async (values) => {
      if (!values.name || !values.email || !values.employees) {
        throw new Error("All fields required");
      }
      
      const payload = {
        name: values.name,
        email: values.email,
        company: values.email.split('@')[1].split('.')[0],
        employees: parseInt(values.employees)
      };

      // Trigger node highlighting simulation on visual graph
      triggerVisualSimulation(container, activeFlow.steps);
      
      try {
        const result = await API.post(`/automation/workflows/${activeFlow.id}/execute`, { trigger_data: payload });
        UI.toast("Simulation executed successfully.", "success");
        
        // Reload builder after execution
        setTimeout(async () => {
          const refreshedLogs = await API.get(`/automation/workflows/${activeFlow.id}/logs`);
          renderBuilder(container, workflows, activeFlow, refreshedLogs);
          
          // Open detail window of this new execution
          renderLogDetailModal(result);
        }, activeFlow.steps.length * 400 + 200);

      } catch (err) {
        UI.toast(err.message || "Execution error", "error");
      }
    });
  });

  // Hook log item detail clicks
  const logCards = container.querySelectorAll(".log-item-card");
  logCards.forEach(card => {
    card.addEventListener("click", () => {
      const logId = parseInt(card.getAttribute("data-log-id"));
      const executionLog = logs.find(l => l.id === logId);
      if (executionLog) {
        renderLogDetailModal(executionLog);
      }
    });
  });
}

function triggerVisualSimulation(container, steps) {
  steps.forEach((step, idx) => {
    setTimeout(() => {
      const nodeEl = container.querySelector(`#node-${step.id}`);
      if (nodeEl) {
        nodeEl.classList.add("running");
        // Scroll node into view if needed
        nodeEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }, idx * 400);

    setTimeout(() => {
      const nodeEl = container.querySelector(`#node-${step.id}`);
      if (nodeEl) {
        nodeEl.classList.remove("running");
      }
    }, (idx + 1) * 400);
  });
}

function renderLogDetailModal(log) {
  const stepsTimeline = log.steps || log.execution_steps;
  const triggerData = log.trigger_data;
  
  const contentHtml = `
    <div style="font-size:0.85rem; display:flex; flex-direction:column; gap:12px; max-height:400px; overflow-y:auto; padding-right:8px;">
      <div>
        <span style="font-size:0.75rem; color:hsl(var(--text-muted)); text-transform:uppercase; font-weight:600;">Trigger Payload</span>
        <pre style="background-color:hsl(var(--bg-sidebar)); padding:8px; border-radius:var(--radius-sm); border:1px solid hsl(var(--border)/0.5); overflow-x:auto; margin:4px 0 0 0; font-size:0.75rem;">${JSON.stringify(triggerData, null, 2)}</pre>
      </div>

      <div>
        <span style="font-size:0.75rem; color:hsl(var(--text-muted)); text-transform:uppercase; font-weight:600; display:block; margin-bottom:8px;">Execution Steps Timeline</span>
        <div style="display:flex; flex-direction:column; gap:8px;">
          ${stepsTimeline.map(step => `
            <div style="padding:8px 12px; border:1px solid hsl(var(--border)/0.4); border-radius:var(--radius-sm); background-color:hsl(var(--bg-sidebar)/0.2);">
              <div style="display:flex; justify-content:space-between; align-items:center; font-weight:600; margin-bottom:4px; font-size:0.8rem;">
                <span>${step.name} (${step.type.replace('action_', '')})</span>
                <span style="color:hsl(${step.status === 'success' ? '--success' : '--danger'});">${step.status.toUpperCase()}</span>
              </div>
              <pre style="margin:4px 0 0 0; font-size:0.7rem; color:hsl(var(--text-secondary)); white-space:pre-wrap; overflow-x:auto;">${JSON.stringify(step.output, null, 2)}</pre>
            </div>
          `).join('')}
        </div>
      </div>
    </div>
  `;

  UI.modal("Execution Analysis Detailed Logs", contentHtml, () => Promise.resolve());
}
