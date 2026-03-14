import { useEffect, useMemo, useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import ErrorBanner from "../components/ui/ErrorBanner.jsx";
import { getInvoices } from "../api/finance";
import { csvEscape, downloadTextFile } from "../lib/export/csv";
import Drawer from "../components/Drawer";

export default function FinanceInvoicesList() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [colSort, setColSort] = useState({ key: "due_on", dir: "desc" });
  const [showDelinquentOnly, setShowDelinquentOnly] = useState(false);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    let mounted = true;

    async function fetchData() {
      try {
        setLoading(true);
        const invoices = await getInvoices();
        const normalized = invoices.map((inv) => ({
          id: inv.id,
          household_id: inv.household_id || null,
          household_name: inv.household_name || "(No household)",
          total_amount: parseFloat(inv.total_amount) || 0,
          paid_amount: parseFloat(inv.paid_amount) || 0,
          balance_due: parseFloat(inv.balance_due) || 0,
          credit_amount: parseFloat(inv.credit_amount) || 0,
          due_on: inv.due_on || null,
          days_past_due: Number.isFinite(inv.days_past_due)
            ? inv.days_past_due
            : 0,
          aging_bucket: inv.aging_bucket || "current",
          is_delinquent: !!inv.is_delinquent,
          is_reversed: !!inv.is_reversed,
          created_at: inv.created_at,
          updated_at: inv.updated_at,
        }));

        if (mounted) {
          setData(normalized);
          setError(null);
        }
      } catch (err) {
        console.error("Failed to fetch invoices:", err);
        if (mounted) {
          setError(err.message || "Failed to load invoices");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    fetchData();
    return () => {
      mounted = false;
    };
  }, []);

  const visibleRows = useMemo(() => {
    if (!showDelinquentOnly) return data;
    return data.filter((row) => row.is_delinquent);
  }, [data, showDelinquentOnly]);

  const summary = useMemo(() => {
    const delinquentRows = data.filter((row) => row.is_delinquent);
    return {
      delinquentCount: delinquentRows.length,
      delinquentBalance: delinquentRows.reduce(
        (sum, row) => sum + row.balance_due,
        0,
      ),
      credits: data.reduce((sum, row) => sum + row.credit_amount, 0),
      reversedCount: data.filter((row) => row.is_reversed).length,
    };
  }, [data]);

  const sortedRows = useMemo(() => {
    if (!visibleRows.length) return [];

    const { key, dir } = colSort;
    const sorted = [...visibleRows];

    sorted.sort((a, b) => {
      let aVal = a[key];
      let bVal = b[key];

      if (key === "due_on" || key === "created_at") {
        aVal = aVal ? new Date(aVal).getTime() : 0;
        bVal = bVal ? new Date(bVal).getTime() : 0;
      }

      if (
        [
          "total_amount",
          "paid_amount",
          "balance_due",
          "credit_amount",
          "days_past_due",
        ].includes(key)
      ) {
        aVal = typeof aVal === "number" ? aVal : 0;
        bVal = typeof bVal === "number" ? bVal : 0;
      }

      if (key === "household_name") {
        aVal = String(aVal || "").toLowerCase();
        bVal = String(bVal || "").toLowerCase();
        return dir === "asc"
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }

      if (aVal < bVal) return dir === "asc" ? -1 : 1;
      if (aVal > bVal) return dir === "asc" ? 1 : -1;
      return 0;
    });

    return sorted;
  }, [visibleRows, colSort]);

  function handleSort(key) {
    setColSort((prev) => ({
      key,
      dir: prev.key === key && prev.dir === "asc" ? "desc" : "asc",
    }));
  }

  function handleExport() {
    if (!sortedRows.length) return;

    const headers = [
      "Payer",
      "Total Amount",
      "Paid",
      "Balance Due",
      "Credit",
      "Days Past Due",
      "Aging Bucket",
      "Reversed",
      "Due Date",
      "Created",
    ];
    const rows = [headers];

    sortedRows.forEach((inv) => {
      rows.push([
        csvEscape(inv.household_name),
        String(inv.total_amount.toFixed(2)),
        String(inv.paid_amount.toFixed(2)),
        String(inv.balance_due.toFixed(2)),
        String(inv.credit_amount.toFixed(2)),
        String(inv.days_past_due),
        inv.aging_bucket,
        inv.is_reversed ? "yes" : "no",
        inv.due_on || "",
        inv.created_at || "",
      ]);
    });

    const csvContent = rows.map((r) => r.join(",")).join("\n");
    downloadTextFile(csvContent, "invoices.csv");
  }

  function formatDate(isoString) {
    if (!isoString) return "";
    try {
      return new Date(isoString).toLocaleDateString();
    } catch {
      return "";
    }
  }

  function formatCurrency(num) {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(num || 0);
  }

  if (loading) {
    return (
      <CrownLayout title="Finance" subtitle="Invoice history and exports">
        <p>Loading...</p>
      </CrownLayout>
    );
  }

  if (error) {
    return (
      <CrownLayout title="Finance" subtitle="Invoice history and exports">
        <ErrorBanner title="Failed to load invoices" message={error} />
      </CrownLayout>
    );
  }

  if (data.length === 0) {
    return (
      <CrownLayout title="Finance" subtitle="Invoice history and exports">
        <div style={{ marginTop: "1rem", color: "var(--crown-muted)" }}>
          No invoices yet
        </div>
      </CrownLayout>
    );
  }

  return (
    <CrownLayout title="Finance" subtitle="Invoice history and exports">
      <div
        style={{
          marginBottom: "1rem",
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
          flexWrap: "wrap",
        }}
      >
        <button className="crown-btn" onClick={handleExport}>
          Export CSV
        </button>
        <button
          className="crown-btn"
          onClick={() => setShowDelinquentOnly((v) => !v)}
          style={{
            background: showDelinquentOnly
              ? "var(--crown-danger-bg)"
              : undefined,
            color: showDelinquentOnly ? "var(--crown-danger)" : undefined,
          }}
        >
          {showDelinquentOnly ? "Showing Delinquent" : "Show Delinquent Only"}
        </button>
        <div
          style={{
            marginLeft: "auto",
            display: "flex",
            gap: "0.75rem",
            fontSize: "0.8rem",
            color: "var(--crown-muted)",
          }}
        >
          <span>
            Delinquent:{" "}
            <strong style={{ color: "var(--crown-danger)" }}>
              {summary.delinquentCount}
            </strong>
          </span>
          <span>
            Past Due:{" "}
            <strong>{formatCurrency(summary.delinquentBalance)}</strong>
          </span>
          <span>
            Credits: <strong>{formatCurrency(summary.credits)}</strong>
          </span>
          <span>
            Reversals: <strong>{summary.reversedCount}</strong>
          </span>
        </div>
      </div>

      <div style={{ overflowX: "auto" }}>
        <table
          style={{
            borderCollapse: "collapse",
            width: "100%",
            fontSize: "0.875rem",
          }}
        >
          <thead>
            <tr style={{ background: "var(--crown-surface-2)" }}>
              <th
                onClick={() => handleSort("household_name")}
                style={{
                  textAlign: "left",
                  padding: "0.75rem",
                  borderBottom: "1px solid var(--crown-border)",
                  cursor: "pointer",
                  userSelect: "none",
                  position: "sticky",
                  top: 0,
                  background: "var(--crown-surface-2)",
                  zIndex: 10,
                }}
              >
                Payer{" "}
                {colSort.key === "household_name" &&
                  (colSort.dir === "asc" ? "↑" : "↓")}
              </th>
              <th
                onClick={() => handleSort("total_amount")}
                style={{
                  textAlign: "right",
                  padding: "0.75rem",
                  borderBottom: "1px solid var(--crown-border)",
                  cursor: "pointer",
                  userSelect: "none",
                  position: "sticky",
                  top: 0,
                  background: "var(--crown-surface-2)",
                  zIndex: 10,
                }}
              >
                Total{" "}
                {colSort.key === "total_amount" &&
                  (colSort.dir === "asc" ? "↑" : "↓")}
              </th>
              <th
                onClick={() => handleSort("paid_amount")}
                style={{
                  textAlign: "right",
                  padding: "0.75rem",
                  borderBottom: "1px solid var(--crown-border)",
                  cursor: "pointer",
                  userSelect: "none",
                  position: "sticky",
                  top: 0,
                  background: "var(--crown-surface-2)",
                  zIndex: 10,
                }}
              >
                Paid{" "}
                {colSort.key === "paid_amount" &&
                  (colSort.dir === "asc" ? "↑" : "↓")}
              </th>
              <th
                onClick={() => handleSort("balance_due")}
                style={{
                  textAlign: "right",
                  padding: "0.75rem",
                  borderBottom: "1px solid var(--crown-border)",
                  cursor: "pointer",
                  userSelect: "none",
                  position: "sticky",
                  top: 0,
                  background: "var(--crown-surface-2)",
                  zIndex: 10,
                }}
              >
                Balance Due{" "}
                {colSort.key === "balance_due" &&
                  (colSort.dir === "asc" ? "↑" : "↓")}
              </th>
              <th
                onClick={() => handleSort("days_past_due")}
                style={{
                  textAlign: "right",
                  padding: "0.75rem",
                  borderBottom: "1px solid var(--crown-border)",
                  cursor: "pointer",
                  userSelect: "none",
                  position: "sticky",
                  top: 0,
                  background: "var(--crown-surface-2)",
                  zIndex: 10,
                }}
              >
                Days Past Due{" "}
                {colSort.key === "days_past_due" &&
                  (colSort.dir === "asc" ? "↑" : "↓")}
              </th>
              <th
                onClick={() => handleSort("due_on")}
                style={{
                  textAlign: "left",
                  padding: "0.75rem",
                  borderBottom: "1px solid var(--crown-border)",
                  cursor: "pointer",
                  userSelect: "none",
                  position: "sticky",
                  top: 0,
                  background: "var(--crown-surface-2)",
                  zIndex: 10,
                }}
              >
                Due Date{" "}
                {colSort.key === "due_on" &&
                  (colSort.dir === "asc" ? "↑" : "↓")}
              </th>
              <th
                onClick={() => handleSort("created_at")}
                style={{
                  textAlign: "left",
                  padding: "0.75rem",
                  borderBottom: "1px solid var(--crown-border)",
                  cursor: "pointer",
                  userSelect: "none",
                  position: "sticky",
                  top: 0,
                  background: "var(--crown-surface-2)",
                  zIndex: 10,
                }}
              >
                Created{" "}
                {colSort.key === "created_at" &&
                  (colSort.dir === "asc" ? "↑" : "↓")}
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedRows.map((inv) => (
              <tr
                key={inv.id}
                onClick={() => setSelected(inv)}
                style={{
                  cursor: "pointer",
                  borderBottom: "1px solid var(--crown-border)",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "var(--crown-surface-2)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "var(--crown-surface)";
                }}
              >
                <td style={{ padding: "0.75rem" }}>{inv.household_name}</td>
                <td style={{ padding: "0.75rem", textAlign: "right" }}>
                  {formatCurrency(inv.total_amount)}
                </td>
                <td style={{ padding: "0.75rem", textAlign: "right" }}>
                  {formatCurrency(inv.paid_amount)}
                </td>
                <td style={{ padding: "0.75rem", textAlign: "right" }}>
                  {formatCurrency(inv.balance_due)}
                </td>
                <td
                  style={{
                    padding: "0.75rem",
                    textAlign: "right",
                    color: inv.is_delinquent
                      ? "var(--crown-danger)"
                      : undefined,
                  }}
                >
                  {inv.days_past_due > 0 ? inv.days_past_due : "-"}
                </td>
                <td style={{ padding: "0.75rem" }}>
                  {inv.due_on ? formatDate(inv.due_on) : "(No due date)"}
                  {inv.is_reversed && (
                    <span
                      style={{
                        marginLeft: "0.5rem",
                        fontSize: "0.75rem",
                        color: "var(--crown-muted)",
                      }}
                    >
                      (reversed)
                    </span>
                  )}
                </td>
                <td style={{ padding: "0.75rem" }}>
                  {formatDate(inv.created_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selected && (
        <Drawer onClose={() => setSelected(null)} width={460}>
          <div style={{ padding: "1.5rem" }}>
            <h2
              style={{
                marginTop: 0,
                marginBottom: "1.5rem",
                fontSize: "1.25rem",
              }}
            >
              Invoice Details
            </h2>

            <div style={{ marginBottom: "1.5rem" }}>
              <h3
                style={{
                  fontSize: "0.875rem",
                  color: "var(--crown-muted)",
                  marginBottom: "0.5rem",
                }}
              >
                Family
              </h3>
              <div>{selected.household_name}</div>
            </div>

            <div style={{ marginBottom: "1.5rem" }}>
              <h3
                style={{
                  fontSize: "0.875rem",
                  color: "var(--crown-muted)",
                  marginBottom: "0.5rem",
                }}
              >
                Amounts
              </h3>
              <div>
                <strong>Total:</strong> {formatCurrency(selected.total_amount)}
              </div>
              <div>
                <strong>Paid:</strong> {formatCurrency(selected.paid_amount)}
              </div>
              <div>
                <strong>Balance Due:</strong>{" "}
                {formatCurrency(selected.balance_due)}
              </div>
              <div>
                <strong>Credits:</strong>{" "}
                {formatCurrency(selected.credit_amount)}
              </div>
            </div>

            <div style={{ marginBottom: "1.5rem" }}>
              <h3
                style={{
                  fontSize: "0.875rem",
                  color: "var(--crown-muted)",
                  marginBottom: "0.5rem",
                }}
              >
                Delinquency & Reversal
              </h3>
              <div>
                <strong>Delinquent:</strong>{" "}
                {selected.is_delinquent ? "Yes" : "No"}
              </div>
              <div>
                <strong>Days Past Due:</strong> {selected.days_past_due}
              </div>
              <div>
                <strong>Aging Bucket:</strong> {selected.aging_bucket}
              </div>
              <div>
                <strong>Reversed:</strong> {selected.is_reversed ? "Yes" : "No"}
              </div>
            </div>

            <div style={{ marginBottom: "1.5rem" }}>
              <h3
                style={{
                  fontSize: "0.875rem",
                  color: "var(--crown-muted)",
                  marginBottom: "0.5rem",
                }}
              >
                Dates
              </h3>
              <div>
                <strong>Due:</strong>{" "}
                {selected.due_on ? formatDate(selected.due_on) : "(Not set)"}
              </div>
              <div>
                <strong>Created:</strong> {formatDate(selected.created_at)}
              </div>
              <div>
                <strong>Updated:</strong> {formatDate(selected.updated_at)}
              </div>
            </div>

            <details style={{ fontSize: "0.875rem" }}>
              <summary
                style={{ cursor: "pointer", color: "var(--crown-muted)" }}
              >
                Identifiers
              </summary>
              <div
                style={{
                  marginTop: "0.5rem",
                  fontFamily: "monospace",
                  fontSize: "0.75rem",
                }}
              >
                <div>
                  <strong>Invoice ID:</strong> {selected.id}
                </div>
                <div>
                  <strong>Household ID:</strong>{" "}
                  {selected.household_id || "(none)"}
                </div>
              </div>
            </details>
          </div>
        </Drawer>
      )}
    </CrownLayout>
  );
}
