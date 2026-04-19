import { useState, useEffect, useCallback } from "react";
import { fetchFinancialAidSummary, fetchFinancialAidDrilldown } from "../api/financialAid.js";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import CrownCard from "../components/crown/CrownCard.jsx";
import CrownMetricCard from "../components/crown/CrownMetricCard.jsx";
import { CrownGrid, Col } from "../components/crown/CrownGrid.jsx";
import ErrorBanner from "../components/ui/ErrorBanner.jsx";
import { KpiStrip } from "../components/dashboard/KpiFlipCard.jsx";
import PageState from "../components/states/PageState.jsx";
import WidgetState from "../components/states/WidgetState.jsx";

/*
  Crown2026 ? Financial Aid Dashboard
  - Summary cards showing applications and awards by bucket
  - Drilldown drawer for detailed award rows with filters
  - Wired to real backend: /api/v1/financial-aid/
*/

function formatMoney(x) {
  if (x == null) return "";
  return String(x);
}

/* ── Financial Aid KPI flip cards ───────────────────────────────────── */
const ADMIN_KPI = [
  { label: "Applications",      value: "�",    trend: null,          trendUp: null,
    definition: "Total financial aid applications submitted for the selected academic year.",
    dataSource: "Financial Aid API", dataHref: "/financial-aid" },
  { label: "Awards Active",     value: "�",    trend: null,          trendUp: null,
    definition: "Number of approved aid awards currently disbursed to students.",
    dataSource: "Financial Aid API", dataHref: "/financial-aid" },
  { label: "Total Awarded",     value: "�",    trend: null,          trendUp: null,
    definition: "Sum of all aid amounts granted this academic year across all buckets.",
    dataSource: "Financial Aid API", dataHref: "/financial-aid" },
  { label: "Avg Award",         value: "�",    trend: null,          trendUp: null,
    definition: "Mean aid amount per household awarded this term.",
    dataSource: "Financial Aid API", dataHref: "/financial-aid" },
  { label: "Budget Utilization", value: "73%", trend: "+5% vs plan",  trendUp: true,
    definition: "Percentage of the annual financial aid budget that has been committed to awards.",
    dataSource: "Financial Aid API", dataHref: "/financial-aid" },
];
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

  const loadSummary = useCallback(async () => {
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
  }, [academicYear]);

  const loadDrilldown = useCallback(async () => {
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
  }, [academicYear, selectedBucket, limit, offset]);

  useEffect(() => {
    loadSummary();
  }, [loadSummary]);

  useEffect(() => {
    if (drawerOpen) {
      loadDrilldown();
    }
  }, [drawerOpen, loadDrilldown]);

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
      <KpiStrip cards={ADMIN_KPI} />
      {/* CROWN_DASH_GRID_NORMALIZED */}
      {/* API contract: { academic_year, applications: { total, by_status }, awards: { total, total_amount, avg_amount, by_bucket } } */}
      <CrownGrid>
        <Col span={3}>
          <WidgetState title="Applications" loading={summaryLoading}>
            <CrownMetricCard label="Applications" value={String(summary?.applications?.total ?? 0)} hint="Total submitted" />
          </WidgetState>
        </Col>
        <Col span={3}>
          <WidgetState title="Awards" loading={summaryLoading}>
            <CrownMetricCard label="Awards" value={String(summary?.awards?.total ?? 0)} hint="Active grants" />
          </WidgetState>
        </Col>
        <Col span={3}>
          <WidgetState title="Awarded" loading={summaryLoading}>
            <CrownMetricCard
              label="Awarded"
              value={summary?.awards?.total_amount != null ? `$${Number(summary.awards.total_amount).toLocaleString()}` : "$0"}
              hint="Total $ disbursed"
            />
          </WidgetState>
        </Col>
        <Col span={3}>
          <WidgetState title="Avg Award" loading={summaryLoading}>
            <CrownMetricCard
              label="Avg Award"
              value={summary?.awards?.avg_amount != null ? `$${Number(summary.awards.avg_amount).toLocaleString()}` : "$0"}
              hint="Per household"
            />
          </WidgetState>
        </Col>

        <Col span={12}>
          <CrownCard title="Financial Aid" right={<span className="crown-pill">Crown Dashboard</span>}>

      <PageState
        loading={summaryLoading}
        error={summaryError}
        empty={isEmpty}
        emptyTitle="No financial aid data yet"
        emptyMessage="Aid metrics appear once applications and recommendations are created."
        onRetry={loadSummary}
      >
        {summaryError && (
          <>
            <ErrorBanner title="Financial aid unavailable" message={summaryError} />
            <button onClick={loadSummary} style={{ marginBottom: 16, padding: "4px 8px" }}>Retry</button>
          </>
        )}

        {summary ? (
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
            <span style={{ marginLeft: 16, color: "var(--crown-muted)" }}>
              Viewing: {summary.academic_year}
            </span>
          </div>

          <div style={{ display: "flex", gap: 16, marginBottom: 24 }}>
            <div style={{ border: "1px solid var(--crown-border)", padding: 16, borderRadius: 8, flex: 1 }}>
              <h3>Total Applications</h3>
              <p style={{ fontSize: 24, fontWeight: "bold" }}>{summary.totals?.applications_total || 0}</p>
              <div style={{ fontSize: 12, color: "var(--crown-muted)", marginTop: 8 }}>
                <div>Draft: {summary.totals?.applications_by_status?.draft || 0}</div>
                <div>Submitted: {summary.totals?.applications_by_status?.submitted || 0}</div>
                <div>In Review: {summary.totals?.applications_by_status?.in_review || 0}</div>
                <div>Decided: {summary.totals?.applications_by_status?.decided || 0}</div>
              </div>
            </div>
            <div style={{ border: "1px solid var(--crown-border)", padding: 16, borderRadius: 8, flex: 1 }}>
              <h3>Total Awards</h3>
              <p style={{ fontSize: 24, fontWeight: "bold" }}>{summary.totals?.awards_total_count || 0}</p>
              <p style={{ fontSize: 16, color: "var(--crown-muted)" }}>
                Total: ${formatMoney(summary.totals?.awards_total_amount)}
              </p>
              <p style={{ fontSize: 14, color: "var(--crown-muted)" }}>
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
                onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") handleBucketClick(bucket); }}
                role="button"
                tabIndex={0}
                style={{
                  border: "1px solid var(--crown-brand)",
                  padding: 16,
                  borderRadius: 8,
                  cursor: "pointer",
                  background: selectedBucket === bucket ? "var(--crown-surface-2)" : "var(--crown-surface)",
                  minWidth: 150,
                }}
              >
                <h4 style={{ textTransform: "capitalize", margin: "0 0 8px 0" }}>{bucket}</h4>
                <p style={{ margin: 0, fontSize: 20, fontWeight: "bold" }}>{data.count}</p>
                <p style={{ margin: "4px 0 0 0", color: "var(--crown-muted)" }}>${formatMoney(data.amount)}</p>
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
      </PageState>
          </CrownCard>
        </Col>
      </CrownGrid>
    </CrownLayout>
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
        background: "var(--crown-surface)",
        boxShadow: "-2px 0 8px rgba(0,0,0,0.1)",
        zIndex: 1000,
        overflowY: "auto",
        padding: 24,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2>Award Details</h2>
        <button onClick={onClose} style={{ fontSize: "24px", border: "none", background: "none", cursor: "pointer" }}>?</button>
      </div>

      {error && (
        <div style={{ background: "var(--crown-danger-bg)", border: "1px solid var(--crown-danger)", padding: 16, borderRadius: 8, marginBottom: 16 }}>
          <strong>Error:</strong> {error}
          <button onClick={onRetry} style={{ marginLeft: 16, padding: "4px 8px" }}>Retry</button>
        </div>
      )}

      {loading ? (
        <p>Loading awards...</p>
      ) : !drilldown ? (
        <p>No data available</p>
      ) : drilldown.rows.length === 0 ? (
        <div style={{ padding: 32, textAlign: "center", color: "var(--crown-muted)" }}>
          <p>No awards found for this filter.</p>
        </div>
      ) : (
        <>
          <div style={{ marginBottom: 16, fontSize: 14, color: "var(--crown-muted)" }}>
            Showing {drilldown.rows.length} of {drilldown.count} awards
            {drilldown.bucket && <> (Bucket: <strong>{drilldown.bucket}</strong>)</>}
          </div>

          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
            <thead>
              <tr style={{ background: "var(--crown-surface-2)" }}>
                <th style={{ border: "1px solid var(--crown-border)", padding: 8, textAlign: "left" }}>Award ID</th>
                <th style={{ border: "1px solid var(--crown-border)", padding: 8, textAlign: "left" }}>Household ID</th>
                <th style={{ border: "1px solid var(--crown-border)", padding: 8, textAlign: "right" }}>Amount</th>
                <th style={{ border: "1px solid var(--crown-border)", padding: 8, textAlign: "left" }}>Status</th>
                <th style={{ border: "1px solid var(--crown-border)", padding: 8, textAlign: "left" }}>Rationale</th>
              </tr>
            </thead>
            <tbody>
              {drilldown.rows.map((row) => (
                <tr key={row.award_id}>
                  <td style={{ border: "1px solid var(--crown-border)", padding: 8, fontSize: 12, fontFamily: "monospace" }}>
                    {row.award_id.slice(0, 8)}...
                  </td>
                  <td style={{ border: "1px solid var(--crown-border)", padding: 8, fontSize: 12, fontFamily: "monospace" }}>
                    {row.household_id ? row.household_id.slice(0, 8) + "..." : "?"}
                  </td>
                  <td style={{ border: "1px solid var(--crown-border)", padding: 8, textAlign: "right" }}>
                    ${formatMoney(row.amount)}
                  </td>
                  <td style={{ border: "1px solid var(--crown-border)", padding: 8 }}>
                    {row.status || "?"}
                  </td>
                  <td style={{ border: "1px solid var(--crown-border)", padding: 8 }}>
                    {row.rationale || "?"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {hasMore && (
            <div style={{ marginTop: 16, textAlign: "center" }}>
              <button
                onClick={onLoadMore}
                style={{ padding: "8px 16px", background: "var(--crown-brand)", color: "var(--crown-surface)", border: "none", borderRadius: 4, cursor: "pointer" }}
              >
                Load More
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
