import { useState, useEffect } from "react";
import { fetchFinancialAidSummary, fetchFinancialAidDrilldown } from "../api/financialAid.js";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import CrownCard from "../components/crown/CrownCard.jsx";
import CrownMetricCard from "../components/crown/CrownMetricCard.jsx";
import { CrownGrid, Col } from "../components/crown/CrownGrid.jsx";

/*
  Crown2026 – Financial Aid Dashboard
  - Summary cards showing applications and awards by bucket
  - Drilldown drawer for detailed award rows with filters
  - Wired to real backend: /api/v1/financial-aid/
*/

function formatMoney(x) {
  if (x == null) return "";
  return String(x);
}

export function FinancialAidDashboard() {
  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [summaryError, setSummaryError] = useState("");

  const [drilldown, setDrilldown] = useState(null);
  const [drilldownLoading, setDrilldownLoading] = useState(false);
  const [drilldownError, setDrilldownError] = useState("");

  const [academicYear, setAcademicYear] = useState("");
  const [selectedBucket, setSelectedBucket] = useState("");
  const [limit] = useState(25);
  const [offset, setOffset] = useState(0);

  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    loadSummary();
  }, [academicYear]);

  useEffect(() => {
    if (drawerOpen) {
      loadDrilldown();
    }
  }, [drawerOpen, selectedBucket, offset]);

  async function loadSummary() {
    setSummaryLoading(true);
    setSummaryError("");
    try {
      const data = await fetchFinancialAidSummary({ academicYear });
      setSummary(data);
    } catch (e) {
      setSummaryError(e.message);
    } finally {
      setSummaryLoading(false);
    }
  }

  async function loadDrilldown() {
    setDrilldownLoading(true);
    setDrilldownError("");
    try {
      const data = await fetchFinancialAidDrilldown({
        academicYear,
        bucket: selectedBucket || undefined,
        limit,
        offset,
      });
      setDrilldown(data);
    } catch (e) {
      setDrilldownError(e.message);
    } finally {
      setDrilldownLoading(false);
    }
  }

  const handleBucketClick = (bucket) => {
    setSelectedBucket(bucket);
    setOffset(0);
    setDrawerOpen(true);
  };

  const handleLoadMore = () => {
    setOffset(offset + limit);
  };

  const isEmpty = summary && summary.totals?.applications_total === 0 && summary.totals?.awards_total_count === 0;

  return (
    <CrownLayout title="Financial Aid" subtitle="Award summaries and application drilldown">
      {/* CROWN_DASH_GRID_NORMALIZED */}
      <CrownGrid>
        <Col span={3}><CrownMetricCard label="Applications" value={summaryLoading ? "…" : String(summary?.totals?.applications_total ?? "—")} hint="Total submitted" /></Col>
        <Col span={3}><CrownMetricCard label="Awards" value={summaryLoading ? "…" : String(summary?.totals?.awards_total_count ?? "—")} hint="Active grants" /></Col>
        <Col span={3}><CrownMetricCard label="Awarded" value={summaryLoading ? "…" : (summary?.totals?.awards_total_amount != null ? `$${Number(summary.totals.awards_total_amount).toLocaleString()}` : "—")} hint="Total $ disbursed" /></Col>
        <Col span={3}><CrownMetricCard label="Avg Award" value={summaryLoading ? "…" : (summary?.totals?.avg_award_amount != null ? `$${Number(summary.totals.avg_award_amount).toLocaleString()}` : "—")} hint="Per household" /></Col>

        <Col span={12}>
          <CrownCard title="Financial Aid" right={<span className="crown-pill">Crown Dashboard</span>}>

      {summaryError && (
        <div style={{ background: "#fee", border: "1px solid #c33", padding: 16, borderRadius: 8, marginBottom: 16 }}>
          <strong>Error loading summary:</strong> {summaryError}
          <button onClick={loadSummary} style={{ marginLeft: 16, padding: "4px 8px" }}>Retry</button>
        </div>
      )}

      {summaryLoading ? (
        <p>Loading summary...</p>
      ) : isEmpty ? (
        <div style={{ padding: 32, textAlign: "center", color: "#666" }}>
          <p>No financial aid data available for the selected academic year.</p>
        </div>
      ) : summary ? (
        <>
          <div style={{ marginBottom: 24 }}>
            <label>
              Academic Year:
              <select
                value={academicYear}
                onChange={(e) => setAcademicYear(e.target.value)}
                style={{ marginLeft: 8, padding: "4px 8px" }}
              >
                <option value="">Latest</option>
                <option value="2025-2026">2025-2026</option>
                <option value="2026-2027">2026-2027</option>
              </select>
            </label>
            <span style={{ marginLeft: 16, color: "#666" }}>
              Viewing: {summary.academic_year}
            </span>
          </div>

          <div style={{ display: "flex", gap: 16, marginBottom: 24 }}>
            <div style={{ border: "1px solid #ccc", padding: 16, borderRadius: 8, flex: 1 }}>
              <h3>Total Applications</h3>
              <p style={{ fontSize: 24, fontWeight: "bold" }}>{summary.totals?.applications_total || 0}</p>
              <div style={{ fontSize: 12, color: "#666", marginTop: 8 }}>
                <div>Draft: {summary.totals?.applications_by_status?.draft || 0}</div>
                <div>Submitted: {summary.totals?.applications_by_status?.submitted || 0}</div>
                <div>In Review: {summary.totals?.applications_by_status?.in_review || 0}</div>
                <div>Decided: {summary.totals?.applications_by_status?.decided || 0}</div>
              </div>
            </div>
            <div style={{ border: "1px solid #ccc", padding: 16, borderRadius: 8, flex: 1 }}>
              <h3>Total Awards</h3>
              <p style={{ fontSize: 24, fontWeight: "bold" }}>{summary.totals?.awards_total_count || 0}</p>
              <p style={{ fontSize: 16, color: "#666" }}>
                Total: ${formatMoney(summary.totals?.awards_total_amount)}
              </p>
              <p style={{ fontSize: 14, color: "#666" }}>
                Avg: ${formatMoney(summary.totals?.avg_award_amount)}
              </p>
            </div>
          </div>

          <h2>Awards by Bucket</h2>
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 24 }}>
            {summary.awards_by_bucket && Object.entries(summary.awards_by_bucket).map(([bucket, data]) => (
              <div
                key={bucket}
                onClick={() => handleBucketClick(bucket)}
                style={{
                  border: "1px solid #007bff",
                  padding: 16,
                  borderRadius: 8,
                  cursor: "pointer",
                  background: selectedBucket === bucket ? "#e7f3ff" : "white",
                  minWidth: 150,
                }}
              >
                <h4 style={{ textTransform: "capitalize", margin: "0 0 8px 0" }}>{bucket}</h4>
                <p style={{ margin: 0, fontSize: 20, fontWeight: "bold" }}>{data.count}</p>
                <p style={{ margin: "4px 0 0 0", color: "#666" }}>${formatMoney(data.amount)}</p>
              </div>
            ))}
          </div>
        </>
      ) : null}

      {drawerOpen && (
        <DrilldownDrawer
          drilldown={drilldown}
          loading={drilldownLoading}
          error={drilldownError}
          onClose={() => setDrawerOpen(false)}
          onRetry={loadDrilldown}
          onLoadMore={handleLoadMore}
          hasMore={drilldown && offset + drilldown.rows.length < drilldown.count}
        />
      )}
    </div>
  );
}

function DrilldownDrawer({ drilldown, loading, error, onClose, onRetry, onLoadMore, hasMore }) {
  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        right: 0,
        width: "80%",
        height: "100%",
        background: "white",
        boxShadow: "-2px 0 8px rgba(0,0,0,0.1)",
        zIndex: 1000,
        overflowY: "auto",
        padding: 24,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2>Award Details</h2>
        <button onClick={onClose} style={{ fontSize: "24px", border: "none", background: "none", cursor: "pointer" }}>×</button>
      </div>

      {error && (
        <div style={{ background: "#fee", border: "1px solid #c33", padding: 16, borderRadius: 8, marginBottom: 16 }}>
          <strong>Error:</strong> {error}
          <button onClick={onRetry} style={{ marginLeft: 16, padding: "4px 8px" }}>Retry</button>
        </div>
      )}

      {loading ? (
        <p>Loading awards...</p>
      ) : !drilldown ? (
        <p>No data available</p>
      ) : drilldown.rows.length === 0 ? (
        <div style={{ padding: 32, textAlign: "center", color: "#666" }}>
          <p>No awards found for this filter.</p>
        </div>
      ) : (
        <>
          <div style={{ marginBottom: 16, fontSize: 14, color: "#666" }}>
            Showing {drilldown.rows.length} of {drilldown.count} awards
            {drilldown.bucket && <> (Bucket: <strong>{drilldown.bucket}</strong>)</>}
          </div>

          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
            <thead>
              <tr style={{ background: "#f5f5f5" }}>
                <th style={{ border: "1px solid #ddd", padding: 8, textAlign: "left" }}>Award ID</th>
                <th style={{ border: "1px solid #ddd", padding: 8, textAlign: "left" }}>Household ID</th>
                <th style={{ border: "1px solid #ddd", padding: 8, textAlign: "right" }}>Amount</th>
                <th style={{ border: "1px solid #ddd", padding: 8, textAlign: "left" }}>Status</th>
                <th style={{ border: "1px solid #ddd", padding: 8, textAlign: "left" }}>Rationale</th>
              </tr>
            </thead>
            <tbody>
              {drilldown.rows.map((row) => (
                <tr key={row.award_id}>
                  <td style={{ border: "1px solid #ddd", padding: 8, fontSize: 12, fontFamily: "monospace" }}>
                    {row.award_id.slice(0, 8)}...
                  </td>
                  <td style={{ border: "1px solid #ddd", padding: 8, fontSize: 12, fontFamily: "monospace" }}>
                    {row.household_id ? row.household_id.slice(0, 8) + "..." : "—"}
                  </td>
                  <td style={{ border: "1px solid #ddd", padding: 8, textAlign: "right" }}>
                    ${formatMoney(row.amount)}
                  </td>
                  <td style={{ border: "1px solid #ddd", padding: 8 }}>
                    {row.status || "—"}
                  </td>
                  <td style={{ border: "1px solid #ddd", padding: 8 }}>
                    {row.rationale || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {hasMore && (
            <div style={{ marginTop: 16, textAlign: "center" }}>
              <button
                onClick={onLoadMore}
                style={{ padding: "8px 16px", background: "#007bff", color: "white", border: "none", borderRadius: 4, cursor: "pointer" }}
              >
                Load More
              </button>
            </div>
          )}
        </>
      )}
          </CrownCard>
        </Col>
      </CrownGrid>
    </CrownLayout>
  );
}
