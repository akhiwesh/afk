import { API } from "../api.js";
import { UI } from "../ui.js";

// The Analyst — one AI, grounded in the org's evidence.
// Renders structured answers; honest about deterministic vs LLM mode.

export async function renderAnalyst(container) {
  container.innerHTML = `
    <div style="max-width:760px;margin:0 auto;display:flex;flex-direction:column;height:calc(100vh - 4rem);">
      <div style="padding:2.5rem 0 1rem;">
        <div style="font-size:0.7rem;letter-spacing:0.14em;text-transform:uppercase;color:hsl(var(--text-muted));margin-bottom:0.5rem;">The Analyst</div>
        <h1 style="font-size:1.6rem;font-weight:600;">Ask why. Get evidence.</h1>
        <p style="color:hsl(var(--text-muted));font-size:0.85rem;margin-top:0.4rem;">Every answer states what it believes, why, its confidence, and what's missing.</p>
      </div>
      <div id="analyst-thread" style="flex:1;overflow-y:auto;padding:0.5rem 0;"></div>
      <div style="padding:1rem 0 1.5rem;display:flex;gap:0.6rem;">
        <input class="input" id="analyst-input" placeholder="e.g. Why isn't revenue growing?" style="flex:1;" maxlength="2000">
        <button class="btn btn-primary" id="analyst-send">Ask</button>
      </div>
    </div>`;

  const thread = container.querySelector("#analyst-thread");
  const input = container.querySelector("#analyst-input");
  const send = container.querySelector("#analyst-send");

  const bubble = (html, who) => {
    const d = document.createElement("div");
    d.style.cssText = who === "you"
      ? "align-self:flex-end;background:hsl(var(--primary)/0.12);border:1px solid hsl(var(--primary)/0.3);border-radius:12px;padding:0.7rem 1rem;margin:0.4rem 0;max-width:85%;margin-left:auto;"
      : "border:1px solid hsl(var(--border));border-radius:12px;padding:1rem 1.2rem;margin:0.4rem 0;max-width:95%;line-height:1.65;";
    d.innerHTML = html;
    thread.appendChild(d);
    thread.scrollTop = thread.scrollHeight;
    return d;
  };

  const format = (text) => text
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/^(What I believe:|Why I believe it:|Confidence:|Missing information:|Suggested next question:)/gm,
      '<strong style="display:block;margin-top:0.75rem;font-size:0.75rem;letter-spacing:0.1em;text-transform:uppercase;color:hsl(var(--text-muted));">$1</strong>')
    .replace(/^— (.*)$/gm, '<em style="display:block;margin-top:0.9rem;font-size:0.78rem;color:hsl(var(--text-muted));">— $1</em>')
    .replace(/\n/g, "<br>");

  async function ask() {
    const q = input.value.trim();
    if (!q) return;
    input.value = "";
    bubble(q.replace(/</g, "&lt;"), "you");
    const pending = bubble('<span style="color:hsl(var(--text-muted));">Analyzing evidence…</span>', "analyst");
    send.disabled = true;
    try {
      const res = await API.post("/intelligence/analyst", { question: q });
      pending.innerHTML = format(res.answer);
    } catch (e) {
      pending.innerHTML = `<span style="color:hsl(var(--danger,0 84% 60%));">The Analyst could not respond: ${e.message}</span>`;
    } finally {
      send.disabled = false;
      input.focus();
    }
  }

  send.addEventListener("click", ask);
  input.addEventListener("keydown", (e) => { if (e.key === "Enter") ask(); });
  input.focus();
}
