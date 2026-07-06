import { API } from "../api.js";
import { UI } from "../ui.js";

export async function renderProjects(container) {
  container.innerHTML = `<div style="display:flex; justify-content:center; align-items:center; height:50vh;"><span style="color:hsl(var(--text-muted));">Fetching boards...</span></div>`;

  try {
    const projects = await API.get("/projects");
    if (projects.length === 0) {
      container.innerHTML = `
        <div class="breadcrumb">Workspace / Projects</div>
        <div class="content-header">
          <h1>Project Kanban Boards</h1>
        </div>
        <div class="card" style="text-align:center; padding:3rem;">
          <h3 style="margin-bottom:1rem;">No active projects</h3>
          <button class="btn btn-primary btn-sm" id="create-first-project-btn">Create Project Board</button>
        </div>
      `;
      container.querySelector("#create-first-project-btn").addEventListener("click", () => triggerCreateProject(container));
      return;
    }
    
    // Choose first project by default for visualization
    const activeProject = projects[0];
    const tasks = await API.get(`/projects/${activeProject.id}/tasks`);
    renderKanban(container, projects, activeProject, tasks);

  } catch (err) {
    container.innerHTML = `<div class="card" style="border-color:hsl(var(--danger)/0.5); padding:2rem; text-align:center;"><h3>Error loading boards</h3><p>${err.message}</p></div>`;
  }
}

function renderKanban(container, projects, activeProject, tasks) {
  container.innerHTML = `
    <div class="breadcrumb">Projects / Boards / ${activeProject.name}</div>
    <div class="content-header">
      <div style="display:flex; align-items:center; gap:12px;">
        <select class="form-control" id="project-board-selector" style="width:auto; font-size:1.15rem; font-weight:700; border:none; padding:0; background:transparent; font-family:var(--font-display); letter-spacing:-0.02em; cursor:pointer;">
          ${projects.map(p => `<option value="${p.id}" ${p.id === activeProject.id ? "selected" : ""}>${p.name}</option>`).join('')}
        </select>
        <button class="btn btn-secondary btn-sm" id="new-project-btn" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;">+ New Board</button>
      </div>
      
      <button class="btn btn-primary btn-sm" id="add-task-btn">
        <span style="font-weight:700; font-size:1.1rem; line-height:0; display:inline-block;">+</span> Add Task
      </button>
    </div>

    <!-- Kanban Board Container -->
    <div class="kanban-board">
      ${["todo", "in_progress", "review", "done"].map(status => {
        const columnTasks = tasks.filter(t => t.status === status);
        return `
          <div class="kanban-column" data-status="${status}">
            <div class="kanban-column-header">
              <span class="kanban-column-title">
                <span style="width:8px; height:8px; border-radius:50%; background-color:${
                  status === 'todo' ? '#6b7280' : 
                  status === 'in_progress' ? 'hsl(var(--primary))' : 
                  status === 'review' ? 'hsl(var(--warning))' : 'hsl(var(--success))'
                }; display:inline-block;"></span>
                ${status.replace('_', ' ')}
              </span>
              <span class="kanban-column-count">${columnTasks.length}</span>
            </div>
            
            <div class="column-droppable-area" style="min-height:50vh; display:flex; flex-direction:column; gap:0.75rem; padding-top:0.5rem;">
              ${columnTasks.map(task => `
                <div class="kanban-card" draggable="true" data-id="${task.id}">
                  <div class="kanban-card-title">${task.title}</div>
                  ${task.description ? `<div class="kanban-card-desc">${task.description}</div>` : ""}
                  
                  <div class="kanban-card-meta">
                    <span class="priority-badge priority-${task.priority}">
                      ${task.priority}
                    </span>
                    ${task.assignee 
                      ? `<div class="avatar" style="width:20px; height:20px; font-size:0.6rem;" title="${task.assignee.full_name}">${task.assignee.full_name.split(' ').map(n => n[0]).join('')}</div>`
                      : `<div class="avatar" style="width:20px; height:20px; font-size:0.6rem; background-color:hsl(var(--border)); color:hsl(var(--text-muted));" title="Unassigned">?</div>`
                    }
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        `;
      }).join('')}
    </div>
  `;

  // Hooks Board Selector
  container.querySelector("#project-board-selector").addEventListener("change", async (e) => {
    const projectId = e.target.value;
    renderTargetProject(container, projects, parseInt(projectId));
  });

  // Hook new project creation button
  container.querySelector("#new-project-btn").addEventListener("click", () => triggerCreateProject(container));

  // Hook Add Task
  container.querySelector("#add-task-btn").addEventListener("click", async () => {
    // Get team members list to assign to task
    let users = [];
    try {
      users = await API.get("/admin/users");
    } catch(e) {
      // Fallback in case of mock user details
      users = [{id: 1, full_name: "Alex Mercer"}];
    }
    
    UI.modal("Add Kanban Task", `
      <div class="form-group">
        <label class="form-label">Task Title</label>
        <input type="text" class="form-control" name="title" required placeholder="Outline launch sequence">
      </div>
      <div class="form-group">
        <label class="form-label">Description</label>
        <textarea class="form-control" name="description" placeholder="Provide extra requirements..."></textarea>
      </div>
      <div class="form-group">
        <label class="form-label">Priority</label>
        <select class="form-control" name="priority">
          <option value="low">Low</option>
          <option value="medium" selected>Medium</option>
          <option value="high">High</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">Assignee</label>
        <select class="form-control" name="assignee_id">
          <option value="">Unassigned</option>
          ${users.map(u => `<option value="${u.id}">${u.full_name}</option>`).join('')}
        </select>
      </div>
    `, async (values) => {
      if (!values.title) throw new Error("Task title is required");
      if (values.assignee_id === "") values.assignee_id = null;
      else values.assignee_id = parseInt(values.assignee_id);
      
      await API.post(`/projects/${activeProject.id}/tasks`, values);
      UI.toast("Task added successfully.", "success");
      
      // Reload active project board
      renderTargetProject(container, projects, activeProject.id);
    });
  });

  // Drag and Drop implementation
  const cards = container.querySelectorAll(".kanban-card");
  const drops = container.querySelectorAll(".kanban-column");

  cards.forEach(card => {
    card.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/plain", card.getAttribute("data-id"));
      card.style.opacity = "0.5";
    });
    card.addEventListener("dragend", () => {
      card.style.opacity = "1";
    });
  });

  drops.forEach(drop => {
    const area = drop.querySelector(".column-droppable-area");
    area.addEventListener("dragover", (e) => {
      e.preventDefault();
      drop.style.borderColor = "hsl(var(--primary))";
    });
    
    area.addEventListener("dragleave", () => {
      drop.style.borderColor = "hsl(var(--border) / 0.5)";
    });

    area.addEventListener("drop", async (e) => {
      e.preventDefault();
      drop.style.borderColor = "hsl(var(--border) / 0.5)";
      
      const taskId = e.dataTransfer.getData("text/plain");
      const targetStatus = drop.getAttribute("data-status");

      try {
        await API.put(`/projects/tasks/${taskId}`, { status: targetStatus });
        UI.toast(`Task stage updated to ${targetStatus.replace('_', ' ')}`, "success");
        
        // Reload Board state
        const refreshedTasks = await API.get(`/projects/${activeProject.id}/tasks`);
        renderKanban(container, projects, activeProject, refreshedTasks);
      } catch (err) {
        UI.toast(err.message || "Failed to update task", "error");
      }
    });
  });
}

async function renderTargetProject(container, projects, projectId) {
  try {
    const activeProject = projects.find(p => p.id === projectId);
    const tasks = await API.get(`/projects/${projectId}/tasks`);
    renderKanban(container, projects, activeProject, tasks);
  } catch (e) {
    UI.toast("Error swapping boards.", "error");
  }
}

function triggerCreateProject(container) {
  UI.modal("Create New Project Board", `
    <div class="form-group">
      <label class="form-label">Project Name</label>
      <input type="text" class="form-control" name="name" required placeholder="Stark Marketing Outreach">
    </div>
    <div class="form-group">
      <label class="form-label">Description</label>
      <textarea class="form-control" name="description" placeholder="Describe the focus of this board..."></textarea>
    </div>
  `, async (values) => {
    if (!values.name) throw new Error("Board name is required");
    await API.post("/projects", values);
    UI.toast("Project Board created.", "success");
    renderProjects(container); // Reload CRM workspace
  });
}
