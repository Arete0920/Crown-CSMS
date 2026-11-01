import { useEffect, useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import DashboardSection from "../components/layout/DashboardSection.jsx";
import { fetchSummerCampBoardSummary } from "../api/summerCampApi.js";

const cardStyle = {
  border: "1px solid var(--crown-border)",
  borderRadius: 6,
  padding: "12px 14px",
  background: "var(--crown-surface)",
};

const valueStyle = {
  fontSize: 24,
  fontWeight: 700,
  marginTop: 6,
  marginBottom: 4,
};

function linkedChargesLabel(value) {
  // Ledger links record assessed obligations. They are not proof of payment,
  // settlement or cash receipts. Never fabricate a zero for missing data.
  if (!Number.isSafeInteger(value) || value < 0) return "Not available";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value / 100);
}

function MetricCard({ label, value }) {
  return (
    <div style={cardStyle}>
      <div style={{ color: "var(--crown-muted)", fontSize: 12 }}>{label}</div>
      <div style={valueStyle}>{value}</div>
    </div>
  );
}

export default function SummerCampDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await fetchSummerCampBoardSummary();
        if (!cancelled) {
          setSummary(data);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) setError(e.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <CrownLayout title="Summer Camp Dashboard">
      <DashboardSection title="Summer Camp Board Summary">
        <p>These are school-scoped registration and linked-charge records, not payment or settlement totals.</p>
        {loading && <span role="status">Loading...</span>}
        {error && (
          <div role="alert" style={{ color: "var(--crown-danger)", background: "var(--crown-danger-bg)", padding: "10px 14px", borderRadius: 4 }}>
            {error}
          </div>
        )}
        {!loading && !error && summary && (
          <>
            <div style={{ marginBottom: 12, color: "var(--crown-muted)", fontSize: 13 }}>
              Reporting date: {summary.as_of}
            </div>
            <div
              style={{
                display: "grid",
                gap: 10,
                gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
              }}
            >
              <MetricCard label="Registered Campers" value={summary.registered_campers} />
              <MetricCard label="Sessions" value={summary.sessions} />
              <MetricCard label="Waitlist Count" value={summary.waitlist_count} />
              <MetricCard label="Missing Forms" value={summary.missing_forms} />
              <MetricCard label="Health Reviews" value={summary.health_review_count} />
              <MetricCard label="Enrollments with balance due" value={summary.outstanding_balances} />
              <MetricCard label="Incidents MTD" value={summary.incidents_mtd} />
              <MetricCard
                label="Ledger-linked charges (not collected)"
                value={linkedChargesLabel(summary.gross_revenue_cents)}
              />
            </div>
          </>
        )}
      </DashboardSection>
    </CrownLayout>
  );
}
