import { API } from "../api.js";
import { UI } from "../ui.js";

export async function renderContentStudio(container) {
  container.innerHTML = `<div style="display:flex; justify-content:center; align-items:center; height:50vh;"><span style="color:hsl(var(--text-muted));">Opening Content Studio...</span></div>`;

  try {
    const savedContent = await API.get("/ai/content");
    renderStudio(container, savedContent);
  } catch (err) {
    container.innerHTML = `<div class="card" style="border-color:hsl(var(--danger)/0.5); padding:2rem; text-align:center;"><h3>Error loading Content Studio</h3><p>${err.message}</p></div>`;
  }
}

function renderStudio(container, savedContent) {
  container.innerHTML = `
    <div class="breadcrumb">Studio / Generator</div>
    <div class="content-header">
      <h1>Content Studio</h1>
    </div>

    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:1.5rem; height:75vh;">
      <!-- Left Config Form Panel -->
      <div class="card glass-card" style="display:flex; flex-direction:column; justify-content:space-between;">
        <form id="content-generator-form">
          <h3 style="margin-bottom:1.5rem; border-bottom:1px solid hsl(var(--border)/0.5); padding-bottom:0.5rem;">Orchestrate Campaign Copy</h3>
          
          <div class="form-group">
            <label class="form-label" for="gen-title">Campaign Name</label>
            <input type="text" id="gen-title" class="form-control" placeholder="Acme Launch Outbound" required>
          </div>

          <div class="form-group">
            <label class="form-label" for="gen-channel">Distribution Channel</label>
            <select id="gen-channel" class="form-control">
              <option value="linkedin">LinkedIn Post</option>
              <option value="email">Cold Email Variant</option>
              <option value="blog">Blog Outline / Intro</option>
              <option value="ad_copy">Paid Advertisement Copy</option>
              <option value="hooks">Outbound Attention Hooks</option>
              <option value="landing_page">Landing Page Taglines</option>
            </select>
          </div>

          <div class="form-group">
            <label class="form-label" for="gen-prompt">Writing Instructions & Guidelines</label>
            <textarea id="gen-prompt" class="form-control" rows="5" placeholder="Focus on automated qualifying benefits. Limit length to 3 sequences. Accentuate product velocity." required style="resize:none;"></textarea>
          </div>

          <div class="form-group">
            <label class="form-label" for="gen-tone">Voice Tone</label>
            <select id="gen-tone" class="form-control">
              <option value="persuasive" selected>Persuasive (Venture Pitch)</option>
              <option value="professional">Professional (Executive summary)</option>
              <option value="casual">Casual (Build in Public)</option>
              <option value="witty">Witty (Engagement driver)</option>
            </select>
          </div>
          
          <button type="submit" class="btn btn-primary" style="width:100%; font-weight:600;" id="studio-submit-btn">Generate Studio Copy</button>
        </form>
      </div>

      <!-- Right Output & History Panel -->
      <div style="display:flex; flex-direction:column; gap:1.5rem; overflow-y:auto;">
        <!-- Generator Result Panel -->
        <div class="card" style="flex-grow:1; display:flex; flex-direction:column; justify-content:space-between; min-height:300px;">
          <div>
            <h3 style="margin-bottom:0.25rem;">Editor Output</h3>
            <p style="font-size:0.75rem; color:hsl(var(--text-muted)); margin-bottom:1rem;">Copy generator outputs appear here.</p>
            
            <div style="background-color:hsl(var(--bg-sidebar)/0.5); border:1px solid hsl(var(--border)/0.5); border-radius:var(--radius-md); padding:1rem; font-size:0.875rem; min-height:180px; white-space:pre-line;" id="studio-output-area">
              <span style="color:hsl(var(--text-muted));">Ready to generate. Configure specifications on the left and submit.</span>
            </div>
          </div>
          
          <button class="btn btn-secondary btn-sm" style="align-self:flex-end; display:none;" id="copy-studio-btn">Copy to Clipboard</button>
        </div>

        <!-- History Listing Panel -->
        <div class="card" style="max-height:250px; overflow-y:auto;">
          <h3 style="margin-bottom:1rem; font-size:1rem;">Saved studio drafts</h3>
          <div style="display:flex; flex-direction:column; gap:0.5rem;" id="studio-history-container">
            ${savedContent.length === 0 
              ? `<span style="font-size:0.8rem; color:hsl(var(--text-muted));">No items saved yet.</span>`
              : savedContent.map(gc => `
                <div style="padding:0.75rem; border:1px solid hsl(var(--border)/0.5); border-radius:var(--radius-md); cursor:pointer; font-size:0.8rem; display:flex; justify-content:between; align-items:center;" class="history-item" data-id="${gc.id}">
                  <div>
                    <strong style="display:block; color:hsl(var(--text-primary));">${gc.title}</strong>
                    <span style="font-size:0.7rem; color:hsl(var(--text-muted));">${gc.channel.toUpperCase()} | ${new Date(gc.created_at).toLocaleDateString()}</span>
                  </div>
                  <span style="color:hsl(var(--primary)); font-weight:600;">➔</span>
                </div>
              `).join('')
            }
          </div>
        </div>
      </div>
    </div>
  `;

  // Submit action handler
  const form = container.querySelector("#content-generator-form");
  const submitBtn = container.querySelector("#studio-submit-btn");
  const outputArea = container.querySelector("#studio-output-area");
  const copyBtn = container.querySelector("#copy-studio-btn");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    submitBtn.innerText = "Orchestrating copy...";
    submitBtn.disabled = true;

    const title = container.querySelector("#gen-title").value;
    const channel = container.querySelector("#gen-channel").value;
    const prompt = container.querySelector("#gen-prompt").value;
    const tone = container.querySelector("#gen-tone").value;

    try {
      const data = await API.post("/ai/generate", { title, channel, prompt, tone });
      
      outputArea.innerHTML = data.content;
      copyBtn.style.display = "inline-flex";
      
      UI.toast("Copy generated & saved.", "success");
      
      // Reload History lists
      const refreshedContent = await API.get("/ai/content");
      renderHistoryItems(container, refreshedContent);
    } catch (err) {
      UI.toast(err.message || "Failed to generate copy", "error");
    } finally {
      submitBtn.innerText = "Generate Studio Copy";
      submitBtn.disabled = false;
    }
  });

  // Copy to clipboard helper
  copyBtn.addEventListener("click", () => {
    navigator.clipboard.writeText(outputArea.innerText);
    UI.toast("Copied to clipboard.", "success");
  });

  // History load click handler
  hookHistoryClicks(container, savedContent);
}

function renderHistoryItems(container, contents) {
  const containerHistory = container.querySelector("#studio-history-container");
  containerHistory.innerHTML = contents.map(gc => `
    <div style="padding:0.75rem; border:1px solid hsl(var(--border)/0.5); border-radius:var(--radius-md); cursor:pointer; font-size:0.8rem; display:flex; justify-content:between; align-items:center;" class="history-item" data-id="${gc.id}">
      <div>
        <strong style="display:block; color:hsl(var(--text-primary));">${gc.title}</strong>
        <span style="font-size:0.7rem; color:hsl(var(--text-muted));">${gc.channel.toUpperCase()} | ${new Date(gc.created_at).toLocaleDateString()}</span>
      </div>
      <span style="color:hsl(var(--primary)); font-weight:600;">➔</span>
    </div>
  `).join('');
  
  hookHistoryClicks(container, contents);
}

function hookHistoryClicks(container, contents) {
  const items = container.querySelectorAll(".history-item");
  const outputArea = container.querySelector("#studio-output-area");
  const copyBtn = container.querySelector("#copy-studio-btn");
  
  items.forEach(item => {
    item.addEventListener("click", () => {
      const id = parseInt(item.getAttribute("data-id"));
      const gc = contents.find(c => c.id === id);
      if (gc) {
        outputArea.innerHTML = gc.content;
        copyBtn.style.display = "inline-flex";
        UI.toast(`Draft '${gc.title}' loaded.`, "success");
      }
    });
  });
}
