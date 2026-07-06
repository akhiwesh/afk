import { API } from "../api.js";
import { UI } from "../ui.js";

export async function renderBilling(container) {
  container.innerHTML = `<div style="display:flex; justify-content:center; align-items:center; height:50vh;"><span style="color:hsl(var(--text-muted));">Fetching billing statement...</span></div>`;

  try {
    const invoices = await API.get("/finance/invoices");
    renderBillingPanel(container, invoices);
  } catch (err) {
    container.innerHTML = `<div class="card" style="border-color:hsl(var(--danger)/0.5); padding:2rem; text-align:center;"><h3>Error loading billing</h3><p>${err.message}</p></div>`;
  }
}

function renderBillingPanel(container, invoices) {
  container.innerHTML = `
    <div class="breadcrumb">Workspace / Billing</div>
    <div class="content-header">
      <h1>Subscription & Invoices</h1>
    </div>

    <!-- Active Subscription Details Card -->
    <div class="card glass-card" style="display:flex; justify-content:space-between; align-items:center; padding:1.75rem; margin-bottom:2rem; border-color:hsl(var(--border));">
      <div>
        <span style="font-size:0.75rem; color:hsl(var(--text-muted)); font-weight:600; text-transform:uppercase; letter-spacing:0.05em; display:block; margin-bottom:0.5rem;">Current Plan</span>
        <h2 style="margin:0 0 0.25rem 0; font-family:var(--font-display); font-size:1.75rem;">Scale SaaS Plan</h2>
        <p style="margin:0; font-size:0.85rem; color:hsl(var(--text-secondary));">Billed monthly. Renews automatically on August 1st, 2026.</p>
      </div>
      
      <div style="text-align:right;">
        <span style="font-size:1.5rem; font-weight:700; font-family:var(--font-display); color:hsl(var(--text-primary)); display:block; margin-bottom:0.5rem;">$149.00<span style="font-size:0.8rem; font-weight:400; color:hsl(var(--text-muted));">/mo</span></span>
        <button class="btn btn-secondary btn-sm" id="cancel-billing-btn">Manage Subscription</button>
      </div>
    </div>

    <!-- Invoices Table -->
    <h3 style="margin-bottom:1rem;">Invoices history</h3>
    <div class="card" style="padding:0; overflow:hidden;">
      <table style="width:100%; border-collapse:collapse; text-align:left; font-size:0.875rem;">
        <thead>
          <tr style="border-bottom:1px solid hsl(var(--border)); background-color:hsl(var(--bg-sidebar)/0.5);">
            <th style="padding:1rem;">Invoice Number</th>
            <th style="padding:1rem;">Billing Date</th>
            <th style="padding:1rem;">Amount</th>
            <th style="padding:1rem;">Status</th>
            <th style="padding:1rem; text-align:right;">Action</th>
          </tr>
        </thead>
        <tbody>
          ${invoices.length === 0 
            ? `<tr><td colspan="5" style="padding:2rem; text-align:center; color:hsl(var(--text-muted));">No invoices logged.</td></tr>`
            : invoices.map(inv => `
              <tr style="border-bottom:1px solid hsl(var(--border)/0.5);">
                <td style="padding:1rem; font-family:monospace; font-weight:600;">${inv.invoice_number}</td>
                <td style="padding:1rem; color:hsl(var(--text-secondary));">${new Date(inv.created_at).toLocaleDateString()}</td>
                <td style="padding:1rem; font-weight:500;">$${inv.amount.toFixed(2)}</td>
                <td style="padding:1rem;">
                  <span class="priority-badge ${inv.status === 'paid' ? 'priority-low' : 'priority-medium'}" style="font-size:0.65rem;">
                    ${inv.status.toUpperCase()}
                  </span>
                </td>
                <td style="padding:1rem; text-align:right;">
                  ${inv.status !== 'paid' 
                    ? `<button class="btn btn-primary btn-sm pay-invoice-btn" data-id="${inv.id}">Pay Now (Stripe Sim)</button>`
                    : `<span style="color:hsl(var(--text-muted)); font-size:0.8rem;">Paid ➔</span>`
                  }
                </td>
              </tr>
            `).join('')
          }
        </tbody>
      </table>
    </div>
  `;

  // Hook Pay Invoice Trigger
  const payBtns = container.querySelectorAll(".pay-invoice-btn");
  payBtns.forEach(btn => {
    btn.addEventListener("click", async () => {
      const id = btn.getAttribute("data-id");
      try {
        await API.post(`/finance/invoices/${id}/pay`);
        UI.toast("Simulated Stripe payment succeeded.", "success");
        renderBilling(container); // Reload
      } catch (err) {
        UI.toast(err.message || "Payment failed", "error");
      }
    });
  });

  // Manage subscription notification
  container.querySelector("#cancel-billing-btn").addEventListener("click", () => {
    UI.toast("Subscribed through Google Sandbox account. Management features disabled locally.", "success");
  });
}
