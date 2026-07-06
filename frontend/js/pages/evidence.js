import { API } from "../api.js";
import { UI } from "../ui.js";

// Evidence — upload business data, confirm what AFK detected.
// The system proposes; the founder confirms. Uncertain columns are flagged.

const L = `style="font-size:0.7rem;letter-spacing:0.14em;text-transform:uppercase;color:hsl(var(--text-muted));margin-bottom:0.5rem;"`;

export async function renderEvidence(container) {
  container.innerHTML = `
    <div style="max-width:880px;margin:0 auto;">
      <div style="padding:2.5rem 0 1.5rem;">
        <div ${L}>Evidence</div>
        <h1 style="font-size:1.8rem;font-weight:600;">Evidence — where revenue clarity begins.</h1>
        <p style="color:hsl(var(--text-muted));margin-top:0.5rem;line-height:1.6;max-width:62ch;">
          For agencies and consultancies: upload invoice exports (with discounts), CRM lead lists, and client spreadsheets.
          CSV or Excel from Zoho, Tally, HubSpot, or plain sheets. AFK proposes column meanings — you confirm. Nothing is guessed silently.
        </p>
      </div>
      <div id="ev-upload" style="border:1px dashed hsl(var(--border));border-radius:12px;padding:2rem;text-align:center;margin-bottom:2rem;">
        <input type="file" id="ev-file" accept=".csv,.tsv,.xlsx" style="display:none;">
        <p style="color:hsl(var(--text-muted));margin-bottom:1rem;">CSV, TSV, or Excel · up to 5 MB / 5,000 rows</p>
        <button class="btn btn-primary" id="ev-pick">Upload a file</button>
        <span id="ev-status" style="display:block;margin-top:0.75rem;font-size:0.85rem;color:hsl(var(--text-muted));"></span>
      </div>
      <div id="ev-mapping"></div>
      <div id="ev-list"></div>
    </div>`;

  const fileInput = container.querySelector("#ev-file");
  container.querySelector("#ev-pick").addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", () => upload(fileInput.files[0], container));
  await refreshList(container);
}

async function upload(file, container) {
  if (!file) return;
  const status = container.querySelector("#ev-status");
  status.textContent = `Reading ${file.name}…`;
  const fd = new FormData();
  fd.append("file", file);
  try {
    const token = localStorage.getItem("access_token");
    const res = await fetch("/api/intelligence/evidence/upload", {
      method: "POST", body: fd,
      headers: token ? { "Authorization": `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `Upload failed (${res.status})`);
    const data = await res.json();
    status.textContent = "";
    renderMapping(container, data);
  } catch (e) {
    status.textContent = "";
    UI.toast(`Upload failed: ${e.message}`, "error");
  }
}

function renderMapping(container, data) {
  const host = container.querySelector("#ev-mapping");
  const fieldOptions = [
    ["date","Date"],["amount","Amount (₹)"],["discount","Discount"],["customer","Customer / company"],
    ["email","Email"],["phone","Phone"],["status","Status / stage"],["source","Lead source"],
    ["product","Product / service"],["quantity","Quantity"],["invoice_id","Invoice / order ID"],
    ["notes","Notes"],["ignore","Ignore this column"]];
  const typeOptions = ["invoices","transactions","leads","customers","unknown"];

  const colRows = data.columns.map(c => `
    <div style="display:grid;grid-template-columns:1.2fr 1fr auto;gap:1rem;align-items:center;padding:0.7rem 0;border-bottom:1px solid hsl(var(--border));">
      <div>
        <div style="font-weight:600;font-size:0.9rem;">${c.header || "(unnamed column)"}</div>
        <div style="font-size:0.72rem;color:hsl(var(--text-muted));">e.g. ${c.samples.slice(0,2).join(" · ") || "—"}</div>
      </div>
      <select class="input" data-col="${c.index}">
        ${fieldOptions.map(([v,l]) => `<option value="${v}" ${v===c.proposed?"selected":""}>${l}</option>`).join("")}
      </select>
      <div style="text-align:right;">
        ${c.needs_confirmation
          ? `<span style="font-size:0.72rem;color:hsl(38 92% 55%);">Please confirm</span>`
          : `<span style="font-size:0.72rem;color:hsl(var(--success));">${Math.round(c.confidence*100)}% sure</span>`}
        <div style="font-size:0.68rem;color:hsl(var(--text-muted));max-width:22ch;">${c.reason}</div>
      </div>
    </div>`).join("");

  host.innerHTML = `
    <div style="border:1px solid hsl(var(--border));border-radius:12px;padding:1.5rem;margin-bottom:2rem;">
      <div ${L}>Confirm what AFK detected</div>
      <p style="font-size:0.9rem;margin-bottom:0.5rem;"><strong>${data.filename}</strong> · ${data.row_count} rows</p>
      <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:1rem;">
        <span style="font-size:0.85rem;color:hsl(var(--text-muted));">This looks like</span>
        <select class="input" id="ev-type" style="max-width:200px;">
          ${typeOptions.map(t => `<option value="${t}" ${t===data.detected_type.type?"selected":""}>${t}</option>`).join("")}
        </select>
        <span style="font-size:0.72rem;color:hsl(var(--text-muted));">${data.detected_type.reason}</span>
      </div>
      ${colRows}
      <div style="display:flex;gap:0.75rem;margin-top:1.25rem;">
        <button class="btn btn-primary" id="ev-confirm">Confirm & add to evidence</button>
        <button class="btn btn-secondary" id="ev-cancel">Discard</button>
      </div>
    </div>`;

  host.querySelector("#ev-cancel").addEventListener("click", async () => {
    try { await API.delete(`/intelligence/evidence/datasets/${data.dataset_id}`); } catch (e) {}
    host.innerHTML = "";
    await refreshList(container);
  });

  host.querySelector("#ev-confirm").addEventListener("click", async () => {
    const mapping = {};
    host.querySelectorAll("[data-col]").forEach(el => { mapping[el.dataset.col] = el.value; });
    const btn = host.querySelector("#ev-confirm");
    btn.disabled = true; btn.textContent = "Adding…";
    try {
      const res = await API.post(`/intelligence/evidence/datasets/${data.dataset_id}/confirm`,
        { mapping, dataset_type: host.querySelector("#ev-type").value });
      UI.toast(`${res.records_stored} records added as ${res.dataset_type} evidence.`, "success");
      host.innerHTML = "";
      await refreshList(container);
    } catch (e) {
      UI.toast(`Could not confirm: ${e.message}`, "error");
      btn.disabled = false; btn.textContent = "Confirm & add to evidence";
    }
  });
}

async function refreshList(container) {
  const host = container.querySelector("#ev-list");
  let list = [];
  try { list = await API.get("/intelligence/evidence/datasets"); } catch (e) { return; }
  if (!list.length) {
    host.innerHTML = `<p style="color:hsl(var(--text-muted));font-size:0.85rem;padding-bottom:3rem;">No evidence uploaded yet. The diagnosis currently runs on audit answers alone.</p>`;
    return;
  }
  host.innerHTML = `
    <div ${L}>Evidence on record</div>
    ${list.map(d => `
      <div style="display:grid;grid-template-columns:1fr auto auto auto;gap:1rem;align-items:center;padding:0.85rem 0;border-bottom:1px solid hsl(var(--border));">
        <div><span style="font-weight:600;font-size:0.9rem;">${d.filename}</span>
          <span style="font-size:0.75rem;color:hsl(var(--text-muted));margin-left:0.5rem;">${d.dataset_type}</span></div>
        <span style="font-size:0.8rem;color:hsl(var(--text-muted));">${d.row_count} rows</span>
        <span style="font-size:0.75rem;color:${d.status === "confirmed" ? "hsl(var(--success))" : "hsl(38 92% 55%)"};">${d.status}</span>
        <button class="btn btn-secondary btn-sm" data-del="${d.id}">Remove</button>
      </div>`).join("")}
    <div style="padding-bottom:3rem;"></div>`;
  host.querySelectorAll("[data-del]").forEach(btn => btn.addEventListener("click", async () => {
    try {
      await API.delete(`/intelligence/evidence/datasets/${btn.dataset.del}`);
      UI.toast("Evidence removed.", "success");
      await refreshList(container);
    } catch (e) { UI.toast(`Could not remove: ${e.message}`, "error"); }
  }));
}
