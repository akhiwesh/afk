import { API } from "../api.js";
import { UI } from "../ui.js";

const ASSISTANTS = [
  { type: "marketing_strategist", name: "Marketing Strategist", desc: "Outbound & GTM calendar planner" },
  { type: "sales_advisor", name: "Sales Advisor", desc: "Outreach emails & closing advice" },
  { type: "business_consultant", name: "Business Consultant", desc: "Business models & economics feedback" },
  { type: "content_creator", name: "Content Creator", desc: "Social hooks & scripts generator" },
  { type: "seo_expert", name: "SEO Expert", desc: "Search intent keyword planner" },
  { type: "copywriter", name: "Copywriter", desc: "High conversion landing page structures" },
  { type: "research_analyst", name: "Research Analyst", desc: "Industry overview syntheses" },
  { type: "automation_engineer", name: "Automation Engineer", desc: "Qualifying schemas and trigger models" },
  { type: "prompt_engineer", name: "Prompt Engineer", desc: "System constraints prompt mapping" },
  { type: "growth_advisor", name: "Growth Advisor", desc: "Virality acquisition loop architectures" }
];

export async function renderAI(container) {
  container.innerHTML = `
    <div class="breadcrumb">Workspace / AI Studio</div>
    <div class="content-header">
      <h1>AI Workspace Assistants</h1>
      <button class="btn btn-secondary btn-sm" id="export-chat-btn" disabled>Export Conversation</button>
    </div>

    <div class="ai-workspace">
      <!-- Left sidebar: Assistants selectors -->
      <div class="assistant-sidebar">
        <div style="padding:1rem; border-bottom:1px solid hsl(var(--border)); font-weight:600; font-size:0.85rem; color:hsl(var(--text-muted));">SELECT ASSISTANT</div>
        <div class="assistant-list">
          ${ASSISTANTS.map(ast => `
            <div class="assistant-item" data-type="${ast.type}">
              <div class="assistant-avatar">${ast.name.split(' ').map(n => n[0]).join('')}</div>
              <div class="assistant-info">
                <span class="assistant-name">${ast.name}</span>
                <span class="assistant-role-desc">${ast.desc}</span>
              </div>
            </div>
          `).join('')}
        </div>
      </div>

      <!-- Right chat thread workspace -->
      <div class="chat-area">
        <div style="padding:1.5rem; border-bottom:1px solid hsl(var(--border)); font-size:0.9rem; font-weight:600; background-color:hsl(var(--bg-sidebar)/0.2);" id="active-assistant-header">
          Select an AI assistant on the left to start collaborating.
        </div>
        
        <div class="chat-history" id="chat-messages-container">
          <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; color:hsl(var(--text-muted)); gap:8px;">
            <svg style="width:36px; height:36px;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path d="M12 18.5a6.5 6.5 0 100-13 6.5 6.5 0 000 13z"/><path d="M12 10.5v4M10 12.5h4"/>
            </svg>
            <span style="font-size:0.85rem;">No active assistant thread.</span>
          </div>
        </div>
        
        <form class="chat-input-container" id="chat-input-form" style="display:none;">
          <input type="text" class="form-control" id="chat-message-field" placeholder="Ask details or request a prompt outline..." required autocomplete="off">
          <button type="submit" class="btn btn-primary" style="padding:0.5rem 1.5rem;">Send</button>
        </form>
      </div>
    </div>
  `;

  let activeConv = null;

  // Hook assistant items
  const items = container.querySelectorAll(".assistant-item");
  items.forEach(item => {
    item.addEventListener("click", async () => {
      items.forEach(i => i.classList.remove("active"));
      item.classList.add("active");
      
      const type = item.getAttribute("data-type");
      const name = item.querySelector(".assistant-name").innerText;
      
      await loadConversation(container, type, name);
    });
  });

  async function loadConversation(container, type, name) {
    // Show spinner in chat area
    const msgContainer = container.querySelector("#chat-messages-container");
    msgContainer.innerHTML = `<div style="display:flex; justify-content:center; align-items:center; height:100%;"><span style="color:hsl(var(--text-muted));">Fetching conversation...</span></div>`;
    
    // Check if there's already an active conversation in DB for this assistant type
    try {
      const conversations = await API.get("/ai/conversations");
      activeConv = conversations.find(c => c.assistant_type === type);
      
      if (!activeConv) {
        // Create new conversation
        activeConv = await API.post("/ai/conversations", {
          title: `${name} Thread`,
          assistant_type: type
        });
      }

      // Enable export button
      const exportBtn = container.querySelector("#export-chat-btn");
      exportBtn.disabled = false;
      
      // Load Messages
      const messages = await API.get(`/ai/conversations/${activeConv.id}/messages`);
      renderMessages(container, messages, name);
      
      // Show Form
      const form = container.querySelector("#chat-input-form");
      form.style.display = "flex";
      
      // Update Header
      container.querySelector("#active-assistant-header").innerText = `Collaborating with ${name}`;

    } catch (e) {
      UI.toast("Failed to initialize conversation thread.", "error");
    }
  }

  function renderMessages(container, messages, assistantName) {
    const msgContainer = container.querySelector("#chat-messages-container");
    
    if (messages.length === 0) {
      msgContainer.innerHTML = `
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; color:hsl(var(--text-muted)); font-size:0.85rem; padding:2rem; text-align:center;">
          <span>Start by writing a message below. Ask the ${assistantName} to generate outlines, strategize solutions, or review tasks.</span>
        </div>
      `;
      return;
    }

    msgContainer.innerHTML = messages.map(m => `
      <div class="chat-msg ${m.role === 'user' ? 'chat-msg-user' : ''}">
        <div class="assistant-avatar" style="${m.role === 'user' ? 'background-color:hsl(var(--border)); color:hsl(var(--text-primary));' : ''}">
          ${m.role === 'user' ? 'ME' : assistantName.split(' ').map(n => n[0]).join('')}
        </div>
        <div class="chat-bubble">
          ${m.content}
        </div>
      </div>
    `).join('');
    
    msgContainer.scrollTop = msgContainer.scrollHeight;
  }

  // Hook Send Message Form
  const inputForm = container.querySelector("#chat-input-form");
  inputForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!activeConv) return;
    
    const inputField = container.querySelector("#chat-message-field");
    const content = inputField.value.trim();
    if (!content) return;
    
    inputField.value = "";
    
    // Optimistic user render to make it feel fast
    const msgContainer = container.querySelector("#chat-messages-container");
    const tempDiv = document.createElement("div");
    tempDiv.className = "chat-msg chat-msg-user";
    tempDiv.innerHTML = `
      <div class="assistant-avatar" style="background-color:hsl(var(--border)); color:hsl(var(--text-primary));">ME</div>
      <div class="chat-bubble">${content}</div>
    `;
    msgContainer.appendChild(tempDiv);
    msgContainer.scrollTop = msgContainer.scrollHeight;

    try {
      const response = await API.post(`/ai/conversations/${activeConv.id}/messages`, { content });
      
      // Full re-render of conversation messages
      const activeItem = container.querySelector(".assistant-item.active");
      const assistantName = activeItem.querySelector(".assistant-name").innerText;
      const messages = await API.get(`/ai/conversations/${activeConv.id}/messages`);
      renderMessages(container, messages, assistantName);
    } catch (err) {
      UI.toast(err.message || "Failed to send message", "error");
    }
  });

  // Hook Export Chat Action
  container.querySelector("#export-chat-btn").addEventListener("click", async () => {
    if (!activeConv) return;
    try {
      const messages = await API.get(`/ai/conversations/${activeConv.id}/messages`);
      const txt = messages.map(m => `[${m.role.toUpperCase()}] ${new Date(m.created_at).toLocaleString()}\n${m.content}\n\n`).join('');
      
      const blob = new Blob([txt], { type: "text/plain" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `${activeConv.title.replace(' ', '_')}_Export.txt`;
      link.click();
      UI.toast("Conversation thread downloaded.", "success");
    } catch (e) {
      UI.toast("Failed to export chat thread.", "error");
    }
  });
}
