import { API } from "../api.js";
import { UI } from "../ui.js";
import { sectionLabel } from "../diagnostic-ui.js";

const EVIDENCE_HINT_KEY = "afk_evidence_hint";

const KIND_LABELS = {
  invoices: "Invoices",
  leads: "Lead export",
  transactions: "Transactions",
  customers: "Customer list",
};

const UPLOAD_GUIDE = {
  invoices: "Invoice export with dates, amounts, and discount columns (Zoho, Tally, Excel).",
  leads: "CRM or spreadsheet with lead status, source, and outcome columns.",
  transactions: "Payment or order history with customer and amount fields.",
  customers: "Client list with repeat purchase or contract dates if available.",
};

export function navigateToEvidence(kind) {
  if (kind) sessionStorage.setItem(EVIDENCE_HINT_KEY, kind);
  window.location.hash = "#evidence";
}

export async function renderEvidence(container) {
  const hint = sessionStorage.getItem(EVIDENCE_HINT_KEY);
  const hintLabel = KIND_LABELS[hint] || null;
  const hintGuide = UPLOAD_GUIDE[hint] || null;
  if (hint) sessionStorage.removeItem(EVIDENCE_HINT_KEY);

  container.innerHTML = `
    <div class="diag-page diag-page--embedded">
      <div class="diag-health-inner">
        <div class="diag-hero" style="margin-bottom:1.25rem;">
          <p class="diag-hero-kicker">Evidence Engine</p>
          <h1>Where revenue clarity begins</h1>
          <p>Upload invoice exports, CRM lead lists, and client spreadsheets. AFK proposes column meanings — you confirm. Nothing is guessed silently.</p>
        </div>

        ${hintLabel ? `
        <div class="diag-panel is-warn" style="margin-bottom:1rem;">
          ${sectionLabel("Recommended for your diagnosis")}
          <p class="diag-section-body" style="margin-bottom:0.35rem;"><strong>Upload ${hintLabel}</strong></p>
          <p class="diag-muted-sm">${hintGuide || ""}</p>
        </div>` : ""}

        <div class="diag-upload-zone ${hintLabel ? "is-highlight" : ""}" id="ev-upload">
          <input type="file" id="ev-file" accept=".csv,.tsv,.xlsx" style="display:none;">
          <p class="diag-muted" style="margin-bottom:0.85rem;">CSV, TSV, or Excel · up to 5 MB / 5,000 rows</p>
          <button type="button" class="diag-btn-primary" id="ev-pick">Upload a file</button>
          <p class="diag-muted-sm" style="margin-top:0.85rem;">Works with Zoho, Tally, HubSpot exports, or plain spreadsheets.</p>
          <span id="ev-status" class="diag-muted-sm" style="display:block;margin-top:0.75rem;"></span>
        </div>

        <div id="ev-mapping"></div>
        <div id="ev-list" class="diag-block"></div>
      </div>
    </div>`;

  const fileInput = container.querySelector("#ev-file");
  const uploadZone = container.querySelector("#ev-upload");

  container.querySelector("#ev-pick").addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", () => upload(fileInput.files[0], container));

  ["dragenter", "dragover"].forEach((evt) => {
    uploadZone.addEventListener(evt, (e) => {
      e.preventDefault();
      uploadZone.classList.add("is-dragover");
    });
  });
  ["dragleave", "drop"].forEach((evt) => {
    uploadZone.addEventListener(evt, (e) => {
      e.preventDefault();
      uploadZone.classList.remove("is-dragover");
    });
  });
  uploadZone.addEventListener("drop", (e) => {
    const file = e.dataTransfer?.files?.[0];
    if (file) upload(file, container);
  });

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
      method: "POST",
      body: fd,
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Upload failed (${res.status})`);
    }
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
    ["date", "Date"], ["amount", "Amount (Rs)"], ["discount", "Discount"], ["customer", "Customer / company"],
    ["email", "Email"], ["phone", "Phone"], ["status", "Status / stage"], ["source", "Lead source"],
    ["product", "Product / service"], ["quantity", "Quantity"], ["invoice_id", "Invoice / order ID"],
    ["notes", "Notes"], ["ignore", "Ignore this column"],
  ];
  const typeOptions = ["invoices", "transactions", "leads", "customers", "unknown"];

  const colRows = data.columns.map((c) => `
    <div class="diag-ev-map-row">
      <div>
        <div style="font-weight:600;font-size:0.9rem;">${c.header || "(unnamed column)"}</div>
        <div class="diag-stat-label">e.g. ${c.samples.slice(0, 2).join(" · ") || "—"}</div>
      </div>
      <select class="diag-select" data-col="${c.index}">
        ${fieldOptions.map(([v, l]) => `<option value="${v}" ${v === c.proposed ? "selected" : ""}>${l}</option>`).join("")}
      </select>
      <div style="text-align:right;">
        ${c.needs_confirmation
          ? `<span class="diag-evidence is-medium">Confirm</span>`
          : `<span class="diag-evidence is-high">${Math.round(c.confidence * 100)}% sure</span>`}
        <div class="diag-stat-label" style="max-width:22ch;margin-top:0.25rem;">${c.reason}</div>
      </div>
    </div>`).join("");

  host.innerHTML = `
    <div class="diag-panel diag-block">
      ${sectionLabel("Confirm what AFK detected")}
      <p class="diag-section-body" style="margin-bottom:0.5rem;"><strong>${data.filename}</strong> · ${data.row_count} rows</p>
      <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:1rem;flex-wrap:wrap;">
        <span class="diag-muted-sm">This looks like</span>
        <select class="diag-select" id="ev-type" style="max-width:220px;">
          ${typeOptions.map((t) => `<option value="${t}" ${t === data.detected_type.type ? "selected" : ""}>${t}</option>`).join("")}
        </select>
        <span class="diag-stat-label">${data.detected_type.reason}</span>
      </div>
      ${colRows}
      <div class="diag-treatment-actions">
        <button type="button" class="diag-btn-primary" id="ev-confirm">Confirm & add to evidence</button>
        <button type="button" class="diag-btn-secondary" id="ev-cancel">Discard</button>
      </div>
    </div>`;

  host.querySelector("#ev-cancel").addEventListener("click", async () => {
    try { await API.delete(`/intelligence/evidence/datasets/${data.dataset_id}`); } catch { /* best effort */ }
    host.innerHTML = "";
    await refreshList(container);
  });

  host.querySelector("#ev-confirm").addEventListener("click", async () => {
    const mapping = {};
    host.querySelectorAll("[data-col]").forEach((el) => { mapping[el.dataset.col] = el.value; });
    const btn = host.querySelector("#ev-confirm");
    btn.disabled = true;
    btn.textContent = "Adding…";
    try {
      const res = await API.post(`/intelligence/evidence/datasets/${data.dataset_id}/confirm`, {
        mapping,
        dataset_type: host.querySelector("#ev-type").value,
      });
      UI.toast(`${res.records_stored} records added as ${res.dataset_type} evidence.`, "success");
      host.innerHTML = "";
      await refreshList(container);
    } catch (e) {
      UI.toast(`Could not confirm: ${e.message}`, "error");
      btn.disabled = false;
      btn.textContent = "Confirm & add to evidence";
    }
  });
}

async function refreshList(container) {
  const host = container.querySelector("#ev-list");
  let list = [];
  try { list = await API.get("/intelligence/evidence/datasets"); } catch { return; }

  if (!list.length) {
    host.innerHTML = `
      ${sectionLabel("Evidence on record")}
      <p class="diag-muted-sm">No evidence uploaded yet. Diagnosis currently runs on audit answers alone — confidence is capped at 40% per dimension.</p>`;
    return;
  }

  host.innerHTML = `
    ${sectionLabel("Evidence on record")}
    ${list.map((d) => `
      <div class="diag-ev-row">
        <div>
          <span style="font-weight:600;font-size:0.9rem;">${d.filename}</span>
          <span class="diag-stat-label" style="margin-left:0.5rem;">${d.dataset_type}</span>
        </div>
        <span class="diag-stat-label">${d.row_count} rows</span>
        <span class="diag-status-pill ${d.status === "confirmed" ? "is-confirmed" : "is-pending"}">${d.status}</span>
        <button type="button" class="diag-btn-secondary" data-del="${d.id}" style="font-size:0.75rem;padding:0.35rem 0.65rem;">Remove</button>
      </div>`).join("")}`;

  host.querySelectorAll("[data-del]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        await API.delete(`/intelligence/evidence/datasets/${btn.dataset.del}`);
        UI.toast("Evidence removed.", "success");
        await refreshList(container);
      } catch (e) {
        UI.toast(`Could not remove: ${e.message}`, "error");
      }
    });
  });
}