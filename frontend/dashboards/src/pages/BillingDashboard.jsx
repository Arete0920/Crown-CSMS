import React, { useMemo, useState } from "react";

import { downloadCsv } from "../utils/downloadCsv.js";
import { authenticatedFetch } from "../utils/authClient.js";

/*
  Crown2026 – Billing Dashboard (0101 UI)
  - Export Center for 0093–0096
  - Manual Record Payment (0102)
  - Open invoice lookup (0102)

  Explicit assumptions:
  - Frontend is served from same origin as API OR you have a proxy configured.
  - Auth is handled by browser session cookie (credentials included).
  - Tenant scoping enforced server-side; if missing school context, API returns 403.

  Note: This repo uses UUIDs for household/account/charge IDs.
*/

const API_BASE = ""; // same-origin; set to "http://127.0.0.1:8000" if running separately

function formatMoney(x) {
  if (x == null) return "";
  const n = Number(x);
  if (Number.isNaN(n)) return String(x);
  return n.toFixed(2);
}

export function BillingDashboard() {
  // MVP selector: Household ID typed in (UUID).
  const [householdId, setHouseholdId] = useState("");
  const householdIdUuid = useMemo(() => {
    const v = (householdId || "").trim();
    return v ? v : null;
  }, [householdId]);

  // Exports
  const [exportYear, setExportYear] = useState(new Date().getFullYear());
  const [exportBusy, setExportBusy] = useState(false);

  // Open invoices (0102)
  const [openBusy, setOpenBusy] = useState(false);
  const [openItems, setOpenItems] = useState([]);
  const [openError, setOpenError] = useState("");

  // Record payment (0102)
  const [payBusy, setPayBusy] = useState(false);
  const [payError, setPayError] = useState("");
  const [payOk, setPayOk] = useState("");
  const [paymentAmount, setPaymentAmount] = useState("25.00");
  const [paymentDate, setPaymentDate] = useState(() => {
    const d = new Date();
    return d.toISOString().slice(0, 10);
  });
  const [paymentReference, setPaymentReference] = useState("SMOKE-0101");
  const [paymentSource, setPaymentSource] = useState("manual");
  const [accountId, setAccountId] = useState("");

  // Allocation builder: choose charge_ids + amounts from open items
  const [allocs, setAllocs] = useState({}); // { [chargeIdUuid]: amountString }

  async function fetchJson(url, options = {}) {
    const res = await authenticatedFetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      credentials: "include",
    });
    const contentType = res.headers.get("content-type") || "";

    if (!res.ok) {
      let bodyText = "";
      try {
        bodyText = await res.text();
      } catch {
        bodyText = "";
      }

      if (res.status === 403) {
        throw new Error("403: Missing school context (tenant safety).");
      }
      if (contentType.includes("application/json")) {
        try {
          const j = JSON.parse(bodyText);
          throw new Error(j.detail || j.error || `HTTP ${res.status}`);
        } catch {
          throw new Error(`HTTP ${res.status}`);
        }
      }
      throw new Error(bodyText || `HTTP ${res.status}`);
    }

    return res.json();
  }

  async function handleDownload(path, filename) {
    setExportBusy(true);
    try {
      const result = await downloadCsv(`${API_BASE}${path}`, { filename });
      if (result?.status === 403) {
        alert("403: Missing school context (tenant safety). Downloaded error.csv");
      }
    } catch (e) {
      alert(String(e?.message || e));
    } finally {
      setExportBusy(false);
    }
  }

  async function loadOpenInvoices() {
    setOpenError("");
    setOpenItems([]);
    setAllocs({});
    setPayOk("");
    setPayError("");

    if (!householdIdUuid) {
      setOpenError("Enter a valid household_id first.");
      return;
    }

    setOpenBusy(true);
    try {
      const data = await fetchJson(
        `${API_BASE}/api/billing/households/${encodeURIComponent(householdIdUuid)}/open-invoices/`
      );
      setOpenItems(data.items || []);
      if ((data.items || []).length === 0) {
        setOpenError("No open items found (or everything is paid). ");
      }
    } catch (e) {
      setOpenError(String(e?.message || e));
    } finally {
      setOpenBusy(false);
    }
  }

  function toggleAlloc(chargeId, checked, suggestedAmount) {
    setAllocs((prev) => {
      const next = { ...prev };
      if (!checked) {
        delete next[chargeId];
      } else {
        next[chargeId] = next[chargeId] || String(suggestedAmount || "0.00");
      }
      return next;
    });
  }

  function setAllocAmount(chargeId, val) {
    setAllocs((prev) => ({ ...prev, [chargeId]: val }));
  }

  function buildAllocationsPayload() {
    const out = [];
    for (const [chargeId, amtStr] of Object.entries(allocs)) {
      const amount = (amtStr || "").trim();
      if (!chargeId) continue;
      if (!amount) continue;
      out.push({ charge_id: chargeId, amount });
    }
    return out;
  }

  async function recordPayment() {
    setPayError("");
    setPayOk("");

    if (!householdIdUuid) {
      setPayError("Enter a valid household_id first.");
      return;
    }

    const acct = (accountId || "").trim();
    if (!acct) {
      setPayError("account_id is required (UUID).");
      return;
    }

    const allocations = buildAllocationsPayload();
    const body = {
      household_id: householdIdUuid,
      payment_date: paymentDate,
      amount: paymentAmount,
      reference: paymentReference,
      source: paymentSource,
      account_id: acct,
      allocations,
    };

    setPayBusy(true);
    try {
      const res = await fetchJson(`${API_BASE}/api/billing/payments/`, {
        method: "POST",
        body: JSON.stringify(body),
      });
      setPayOk(`Payment created: ${res.payment_id}`);
      await loadOpenInvoices();
    } catch (e) {
      setPayError(String(e?.message || e));
    } finally {
      setPayBusy(false);
    }
  }

  return (
    <div
      style={{
        padding: 16,
        fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, Arial",
      }}
    >
      <h2 style={{ margin: "0 0 12px" }}>Billing Dashboard</h2>

      {/* Household selector */}
      <div style={{ display: "flex", gap: 12, alignItems: "end", marginBottom: 16, flexWrap: "wrap" }}>
        <div>
          <label style={{ display: "block", fontSize: 12, opacity: 0.8 }}>Household ID (UUID)</label>
          <input
            value={householdId}
            onChange={(e) => setHouseholdId(e.target.value)}
            placeholder="e.g., 00000000-0000-0000-0000-000000000000"
            style={{ padding: 8, minWidth: 360 }}
          />
        </div>

        <button onClick={loadOpenInvoices} disabled={openBusy} style={{ padding: "8px 12px" }}>
          {openBusy ? "Loading..." : "Load Open Invoices"}
        </button>

        <div style={{ marginLeft: "auto" }} />
      </div>

      {openError ? <div style={{ marginBottom: 12, color: "#b00020" }}>{openError}</div> : null}

      {/* Billing Ops */}
      <div style={{ border: "1px solid #ddd", borderRadius: 10, padding: 14, marginBottom: 16 }}>
        <h3 style={{ margin: "0 0 10px" }}>Billing Ops</h3>

        {/* Exports */}
        <div style={{ display: "flex", gap: 10, alignItems: "end", flexWrap: "wrap", marginBottom: 14 }}>
          <div>
            <label style={{ display: "block", fontSize: 12, opacity: 0.8 }}>Year (for 0095)</label>
            <input value={exportYear} onChange={(e) => setExportYear(e.target.value)} style={{ padding: 8, width: 120 }} />
          </div>

          <button
            disabled={exportBusy}
            onClick={() => handleDownload("/api/exports/statements.csv", "statements.csv")}
            style={{ padding: "8px 12px" }}
          >
            0093 Statements CSV
          </button>

          <button
            disabled={exportBusy}
            onClick={() => handleDownload("/api/exports/statement-lines.csv", "statement_lines.csv")}
            style={{ padding: "8px 12px" }}
          >
            0094 Statement Lines CSV
          </button>

          <button
            disabled={exportBusy}
            onClick={() =>
              handleDownload(
                `/api/exports/year-end/tuition-paid.csv?year=${encodeURIComponent(exportYear)}`,
                `tuition_paid_${exportYear}.csv`
              )
            }
            style={{ padding: "8px 12px" }}
          >
            0095 Tuition Paid CSV
          </button>

          <button
            disabled={exportBusy}
            onClick={() => handleDownload("/api/exports/accounting/payments-qb.csv", "payments_qb.csv")}
            style={{ padding: "8px 12px" }}
          >
            0096 Payments (QB) CSV
          </button>
        </div>

        <div style={{ fontSize: 12, opacity: 0.75 }}>
          If you see a 403 error: your account is authenticated but missing a school context (tenant safety).
        </div>
      </div>

      {/* Open items display */}
      <div style={{ marginBottom: 16 }}>
        <h3 style={{ margin: "0 0 10px" }}>Open Items</h3>
        {openItems.length === 0 ? (
          <div style={{ fontSize: 13, opacity: 0.8 }}>No items loaded.</div>
        ) : (
          <table style={{ borderCollapse: "collapse", width: "100%" }}>
            <thead>
              <tr style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>
                <th style={{ padding: 8 }}>Apply</th>
                <th style={{ padding: 8 }}>Due</th>
                <th style={{ padding: 8 }}>Invoice</th>
                <th style={{ padding: 8 }}>Charge</th>
                <th style={{ padding: 8 }}>Total</th>
                <th style={{ padding: 8 }}>Paid</th>
                <th style={{ padding: 8 }}>Balance</th>
                <th style={{ padding: 8 }}>Allocate Amount</th>
              </tr>
            </thead>
            <tbody>
              {openItems.map((it) => {
                const cid = it.ledger_charge_id;
                const checked = cid && Object.prototype.hasOwnProperty.call(allocs, cid);
                return (
                  <tr key={`${it.invoice_id}-${cid}`} style={{ borderBottom: "1px solid #eee" }}>
                    <td style={{ padding: 8 }}>
                      {cid ? (
                        <input
                          type="checkbox"
                          checked={!!checked}
                          onChange={(e) => toggleAlloc(cid, e.target.checked, it.balance)}
                        />
                      ) : (
                        "-"
                      )}
                    </td>
                    <td style={{ padding: 8 }}>{it.due_on}</td>
                    <td style={{ padding: 8 }}>{it.invoice_id}</td>
                    <td style={{ padding: 8 }}>{it.charge?.description ? `${cid} — ${it.charge.description}` : cid || "-"}</td>
                    <td style={{ padding: 8 }}>{formatMoney(it.total_amount)}</td>
                    <td style={{ padding: 8 }}>{formatMoney(it.paid_amount)}</td>
                    <td style={{ padding: 8 }}>{formatMoney(it.balance)}</td>
                    <td style={{ padding: 8 }}>
                      {cid ? (
                        <input
                          disabled={!checked}
                          value={allocs[cid] || ""}
                          onChange={(e) => setAllocAmount(cid, e.target.value)}
                          style={{ padding: 6, width: 120 }}
                        />
                      ) : (
                        "-"
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Record payment */}
      <div style={{ border: "1px solid #ddd", borderRadius: 10, padding: 14 }}>
        <h3 style={{ margin: "0 0 10px" }}>Record Payment (0102)</h3>

        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 10 }}>
          <div>
            <label style={{ display: "block", fontSize: 12, opacity: 0.8 }}>Amount</label>
            <input value={paymentAmount} onChange={(e) => setPaymentAmount(e.target.value)} style={{ padding: 8, width: 140 }} />
          </div>

          <div>
            <label style={{ display: "block", fontSize: 12, opacity: 0.8 }}>Payment Date</label>
            <input type="date" value={paymentDate} onChange={(e) => setPaymentDate(e.target.value)} style={{ padding: 8, width: 160 }} />
          </div>

          <div>
            <label style={{ display: "block", fontSize: 12, opacity: 0.8 }}>Reference</label>
            <input value={paymentReference} onChange={(e) => setPaymentReference(e.target.value)} style={{ padding: 8, width: 220 }} />
          </div>

          <div>
            <label style={{ display: "block", fontSize: 12, opacity: 0.8 }}>Source</label>
            <input value={paymentSource} onChange={(e) => setPaymentSource(e.target.value)} style={{ padding: 8, width: 140 }} />
          </div>

          <div>
            <label style={{ display: "block", fontSize: 12, opacity: 0.8 }}>Account ID (UUID)</label>
            <input value={accountId} onChange={(e) => setAccountId(e.target.value)} style={{ padding: 8, width: 360 }} />
          </div>
        </div>

        {payError ? <div style={{ color: "#b00020", marginBottom: 8 }}>{payError}</div> : null}
        {payOk ? <div style={{ color: "#0b6b0b", marginBottom: 8 }}>{payOk}</div> : null}

        <button onClick={recordPayment} disabled={payBusy} style={{ padding: "10px 14px" }}>
          {payBusy ? "Posting..." : "Post Payment"}
        </button>

        <div style={{ marginTop: 10, fontSize: 12, opacity: 0.75 }}>
          Tip: Load Open Invoices first, then check items and enter allocation amounts (defaults to balance).
        </div>
      </div>
    </div>
  );
}
