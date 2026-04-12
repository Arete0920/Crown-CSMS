import { useMemo, useState } from "react";

import { downloadCsv } from "../utils/downloadCsv.js";
import { authenticatedFetch } from "../utils/authClient.js";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import CrownCard from "../components/crown/CrownCard.jsx";
import CrownMetricCard from "../components/crown/CrownMetricCard.jsx";
import { CrownGrid, Col } from "../components/crown/CrownGrid.jsx";
import ErrorBanner from "../components/ui/ErrorBanner.jsx";
import { KpiStrip } from "../components/dashboard/KpiFlipCard.jsx";

/*
  Crown2026 � Billing Dashboard (0101 UI)
  - Export Center for 0093�0096
  - Manual Record Payment (0102)
  - Open invoice lookup (0102)

  Explicit assumptions:
  - Frontend is served from same origin as API OR you have a proxy configured.
  - Auth is handled by browser session cookie (credentials included).
  - Tenant scoping enforced server-side; if missing school context, API returns 403.

  Note: This repo uses UUIDs for household/account/charge IDs.
*/

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

// Dev-mode regression guard: catch missing API_BASE before it breaks exports.
// Skip this warning under tests to avoid noisy stderr that obscures true failures.
if (import.meta.env.DEV && import.meta.env.MODE !== "test" && !API_BASE) {
  console.warn("?? BillingDashboard: API_BASE is empty. Exports will fail. Set VITE_API_BASE_URL in .env.local");
}

function formatMoney(x) {
  if (x == null) return "";
  const n = Number(x);
  if (Number.isNaN(n)) return String(x);
  return n.toFixed(2);
}

/* â”€â”€ Billing / Accounts-Receivable KPI flip cards â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
const ADMIN_KPI = [
  { label: "Collection Rate",   value: "93.1%", trend: "+6.0% vs last yr", trendUp: true,
    definition: "Percentage of total billed tuition and fees collected as of today.",
    dataSource: "Billing Module", dataHref: "/billing" },
  { label: "Outstanding AR",    value: "$42,880", trend: null,             trendUp: null,
    definition: "Total unpaid balances across all households with open invoices.",
    dataSource: "Billing Module", dataHref: "/billing" },
  { label: "Invoices Overdue",  value: "23",    trend: "+3 vs last wk",   trendUp: false,
    definition: "Invoices past their due date that have not been paid or placed on a plan.",
    dataSource: "Billing Module", dataHref: "/billing" },
  { label: "Payment Plans",     value: "18",    trend: null,               trendUp: null,
    definition: "Number of households currently enrolled in an active installment payment plan.",
    dataSource: "Billing Module", dataHref: "/billing" },
];
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
  const [paymentReference, setPaymentReference] = useState("");
  const [paymentSource, setPaymentSource] = useState("manual");
  const [accountId, setAccountId] = useState("");

  // Allocation builder: choose charge_ids + amounts from open items
  const [allocs, setAllocs] = useState({}); // { [chargeIdUuid]: amountString }

  // Demo household loader
  const [loadingDemoHousehold, setLoadingDemoHousehold] = useState(false);

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

  async function loadDemoHousehold() {
    setLoadingDemoHousehold(true);
    try {
      const data = await fetchJson(`${API_BASE}/api/households/?page_size=1`);
      if (data?.results?.[0]?.id) {
        setHouseholdId(data.results[0].id);
        // Optional: show household name in a toast/alert
        const name = data.results[0].name || data.results[0].id;
        console.log(`Loaded demo household: ${name}`);
      } else {
        alert("No households found in system. Run seed data first.");
      }
    } catch (e) {
      alert(`Failed to load demo household: ${e.message}`);
    } finally {
      setLoadingDemoHousehold(false);
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

  function dollarsToCents(val) {
    const n = Number(val);
    if (!Number.isFinite(n)) return 0;
    return Math.round(n * 100);
  }

  function formatApiError(status, bodyText, bodyJson) {
    if (status === 403) return "You don�t have permission to record payments (finance role required).";
    if (status === 409) return "Duplicate reference: this payment reference was already recorded.";
    if (status === 400) {
      const detail =
        (bodyJson && (bodyJson.detail || bodyJson.error)) ||
        (typeof bodyText === "string" && bodyText.trim()) ||
        "Validation error.";
      return `Validation error: ${detail}`;
    }
    const detail =
      (bodyJson && (bodyJson.detail || bodyJson.error)) ||
      (typeof bodyText === "string" && bodyText.trim()) ||
      "";
    return detail ? `Payment failed (${status}): ${detail}` : `Payment failed (${status}).`;
  }

  function resolveSelectedOpenItems(openItemsList, allocsMap) {
    const selectedChargeIds = Object.keys(allocsMap || {});
    if (selectedChargeIds.length === 0) {
      return {
        selectedChargeIds: [],
        singleInvoiceId: null,
        singleChargeId: null,
        error: "Select at least one open item to apply this payment to.",
      };
    }

    if (selectedChargeIds.length === 1) {
      const singleChargeId = selectedChargeIds[0];
      const match = (openItemsList || []).find((it) => it.ledger_charge_id === singleChargeId);
      if (!match || !match.invoice_id) {
        return {
          selectedChargeIds,
          singleInvoiceId: null,
          singleChargeId,
          error: "Could not resolve invoice_id for the selected open item. Reload Open Invoices and try again.",
        };
      }
      return { selectedChargeIds, singleInvoiceId: match.invoice_id, singleChargeId, error: null };
    }

    return { selectedChargeIds, singleInvoiceId: null, singleChargeId: null, error: null };
  }

  async function recordPayment() {
    setPayError("");
    setPayOk("");

    if (!householdIdUuid) {
      setPayError("Enter a valid household_id first.");
      return;
    }

    // 0111: /api/billing/payments/record/ supports multi-allocation.
    // We restore the original workflow: multiple open items can be checked.
    const { selectedChargeIds, singleInvoiceId, singleChargeId, error } = resolveSelectedOpenItems(openItems, allocs);
    if (error) {
      setPayError(error);
      return;
    }

    const paymentAmountCents = dollarsToCents(paymentAmount);
    if (!paymentAmountCents || paymentAmountCents <= 0) {
      setPayError("Enter a valid payment amount > 0.");
      return;
    }

    const basePayload = {
      amount_cents: paymentAmountCents,
      method: (paymentSource || "manual").trim() || "manual",
      reference: (paymentReference || "").trim(),
      received_on: paymentDate || null,
    };

    let payload = basePayload;
    let invoiceIdForOptimistic = null;

    if (selectedChargeIds.length === 1) {
      // Fallback to 0109 behavior (single invoice): keeps existing response handling and optimistic refresh.
      const selectedAllocationDollars = (allocs && singleChargeId ? allocs[singleChargeId] : "") || "";
      const amountCents = dollarsToCents(selectedAllocationDollars || paymentAmount);
      if (!amountCents || amountCents <= 0) {
        setPayError("Enter a valid amount > 0.");
        return;
      }

      payload = {
        ...basePayload,
        invoice_id: singleInvoiceId,
        amount_cents: amountCents,
      };
      invoiceIdForOptimistic = singleInvoiceId;
    } else {
      // Multi-allocation: one payment ? many ledger charges.
      const allocations = selectedChargeIds.map((chargeId) => {
        const dollars = (allocs && allocs[chargeId] != null ? String(allocs[chargeId]) : "").trim();
        const cents = dollars ? dollarsToCents(dollars) : 0;
        return { ledger_charge_id: chargeId, amount_cents: Number.isFinite(cents) ? cents : 0 };
      });

      const sumAllocCents = allocations.reduce((acc, a) => acc + (Number(a.amount_cents) || 0), 0);

      if (sumAllocCents === 0) {
        // Auto-fill: if user left allocations blank, allocate full payment to the first selected item.
        allocations[0].amount_cents = paymentAmountCents;
      } else if (sumAllocCents !== paymentAmountCents) {
        setPayError(
          `Allocation total must equal payment amount. Allocated $${(sumAllocCents / 100).toFixed(2)} but payment is $${(
            paymentAmountCents / 100
          ).toFixed(2)}.`
        );
        return;
      }

      payload = {
        ...basePayload,
        household_id: householdIdUuid,
        allocations,
      };
    }

    setPayBusy(true);
    try {
      // 0109: JWT-first via authenticatedFetch (0104); cookies still included.
      const resp = await authenticatedFetch(`${API_BASE}/api/billing/payments/record/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(payload),
      });

      let bodyText = "";
      let bodyJson = null;
      try {
        bodyText = await resp.text();
      } catch {
        bodyText = "";
      }

      try {
        bodyJson = bodyText ? JSON.parse(bodyText) : null;
      } catch {
        bodyJson = null;
      }

      if (!resp.ok) {
        throw new Error(formatApiError(resp.status, bodyText, bodyJson));
      }

      const data = bodyJson || {};
      const paymentId = data.payment_id;
      setPayOk(paymentId ? `Payment recorded: ${paymentId}` : "Payment recorded.");

      // Optimistic refresh (single-invoice flow only): update the selected row balance immediately, then re-fetch.
      if (invoiceIdForOptimistic) {
        const appliedCents = Number(data.applied_amount_cents || 0);
        if (Number.isFinite(appliedCents) && appliedCents > 0) {
          setOpenItems((prev) =>
            (prev || []).map((it) => {
              if (it.invoice_id !== invoiceIdForOptimistic) return it;
              const bal = Number(it.balance);
              if (!Number.isFinite(bal)) return it;
              const nextBalance = Math.max(0, bal - appliedCents / 100);
              return { ...it, balance: String(nextBalance.toFixed(2)) };
            })
          );
        }
      }

      await loadOpenInvoices();
    } catch (e) {
      setPayError(String(e?.message || e));
    } finally {
      setPayBusy(false);
    }
  }

  return (
    <CrownLayout title="Billing" subtitle="Invoices, payments, and export center">
      <KpiStrip cards={ADMIN_KPI} />
      {/* CROWN_DASH_GRID_NORMALIZED */}
      <CrownGrid>
        <Col span={3}><CrownMetricCard label="Status" value="Healthy" hint="All systems nominal" /></Col>
        <Col span={3}><CrownMetricCard label="Today" value="Live" hint="Demo surface active" /></Col>
        <Col span={3}><CrownMetricCard label="Security" value="Enforced" hint="Tenant + RBAC gates" /></Col>
        <Col span={3}><CrownMetricCard label="Data" value="Seeded" hint="Realistic demo records" /></Col>

        <Col span={12}>
          <CrownCard title="Billing" right={<span className="crown-pill">Crown Dashboard</span>}>

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

        <button
          className="crown-btn"
          onClick={loadDemoHousehold}
          disabled={loadingDemoHousehold}
          title="Load first household from database"
        >
          {loadingDemoHousehold ? "Loading..." : "Use Demo Household"}
        </button>

        <button className="crown-btn" onClick={loadOpenInvoices} disabled={openBusy}>
          {openBusy ? "Loading..." : "Load Open Invoices"}
        </button>

        <div style={{ marginLeft: "auto" }} />
      </div>

      {openError ? <ErrorBanner title="Open invoices error" message={openError} /> : null}

      {/* Billing Ops */}
      <div style={{ border: "1px solid var(--crown-border)", borderRadius: 10, padding: 14, marginBottom: 16 }}>
        <h3 style={{ margin: "0 0 10px" }}>Billing Ops</h3>

        {/* Exports */}
        <div style={{ display: "flex", gap: 10, alignItems: "end", flexWrap: "wrap", marginBottom: 14 }}>
          <div>
            <label style={{ display: "block", fontSize: 12, opacity: 0.8 }}>Export Year</label>
            <input value={exportYear} onChange={(e) => setExportYear(e.target.value)} style={{ padding: 8, width: 120 }} />
          </div>

          <button
            className="crown-btn"
            disabled={exportBusy}
            onClick={() => handleDownload("/api/exports/statements.csv", "statements.csv")}
          >
            Statements CSV
          </button>

          <button
            className="crown-btn"
            disabled={exportBusy}
            onClick={() => handleDownload("/api/exports/statement-lines.csv", "statement_lines.csv")}
          >
            Statement Lines CSV
          </button>

          <button
            className="crown-btn"
            disabled={exportBusy}
            onClick={() =>
              handleDownload(
                `/api/exports/year-end/tuition-paid.csv?year=${encodeURIComponent(exportYear)}`,
                `tuition_paid_${exportYear}.csv`
              )
            }
          >
            Tuition Paid CSV
          </button>

          <button
            className="crown-btn"
            disabled={exportBusy}
            onClick={() => handleDownload("/api/exports/accounting/payments-qb.csv", "payments_qb.csv")}
          >
            Payments (QB) CSV
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
              <tr style={{ textAlign: "left", borderBottom: "1px solid var(--crown-border)" }}>
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
                  <tr key={`${it.invoice_id}-${cid}`} style={{ borderBottom: "1px solid var(--crown-border)" }}>
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
                    <td style={{ padding: 8 }}>{it.charge?.description ? `${cid} � ${it.charge.description}` : cid || "-"}</td>
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
      <div style={{ border: "1px solid var(--crown-border)", borderRadius: 10, padding: 14 }}>
        <h3 style={{ margin: "0 0 10px" }}>Record Payment</h3>

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

        {payError ? <ErrorBanner title="Payment error" message={payError} /> : null}
        {payOk ? <div style={{ color: "var(--crown-ok)", marginBottom: 8 }}>{payOk}</div> : null}

        <button className="crown-btn crown-btn-primary" onClick={recordPayment} disabled={payBusy}>
          {payBusy ? "Posting..." : "Post Payment"}
        </button>

        <div style={{ marginTop: 10, fontSize: 12, opacity: 0.75 }}>
          Tip: Load Open Invoices first, then check items and enter allocation amounts (defaults to balance).
        </div>
      </div>
          </CrownCard>
        </Col>
      </CrownGrid>
    </CrownLayout>
  );
}
