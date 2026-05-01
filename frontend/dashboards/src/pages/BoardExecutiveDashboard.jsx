import { useEffect, useState } from "react";
import { CrownGrid, Col } from "../components/crown/CrownGrid.jsx";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import DashboardSection from "../components/layout/DashboardSection.jsx";
import BoardKpiTile from "../components/board/BoardKpiTile.jsx";
import BoardCard from "../components/board/BoardCard.jsx";
import BoardTrendChart from "../components/board/BoardTrendChart.jsx";
import BoardSimpleTable from "../components/board/BoardSimpleTable.jsx";
import { useBoardExecutiveData } from "../hooks/useBoardExecutiveData.js";
import { fetchBoardCompass, fetchBoardRiskCounts } from "../api/signalsApi.js";
import BoardCompassCard from "../components/board/BoardCompassCard.jsx";
import AftercareBoardCard from "../components/board/AftercareBoardCard.jsx";
import { KpiStrip } from "../components/dashboard/KpiFlipCard.jsx";

/* ── Auth helpers (matches Crown sessionStorage pattern) ─────────────── */
function getSession() {
  try {
    const token = sessionStorage.getItem("crown.jwt.access") || "";
    // sessionStorage clears on tab close; fall back to localStorage so a page
    // refresh during a session doesn't blank the board widgets.
    const schoolId =
      sessionStorage.getItem("crown.school.id") ||
      localStorage.getItem("crown.school.id") ||
      localStorage.getItem("schoolId") ||
      "";
    return { token, schoolId };
  } catch { return { token: "", schoolId: "" }; }
}

/* ── Formatting ──────────────────────────────────────────────────────── */
function currency(n) {
  if (typeof n !== "number") return n;
  return n.toLocaleString(undefined, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  });
}

/* ── Status badge (no MUI Chip) ─────────────────────────────────────── */
const STATUS_BG   = { Stable: 'var(--crown-ok-bg)',   Watch: 'var(--crown-warn-bg)',   Risk: 'var(--crown-danger-bg)' };
const STATUS_TEXT = { Stable: 'var(--crown-ok)',      Watch: 'var(--crown-warn)',       Risk: 'var(--crown-danger)'    };

function StatusBadge({ label }) {
  const s = {
    display: "inline-block", padding: "2px 10px", borderRadius: 12,
    fontSize: 12, fontWeight: 600,
    background: STATUS_BG[label]   || 'var(--crown-surface-2)',
    color:      STATUS_TEXT[label] || 'var(--crown-muted)',
  };
  return <span style={s}>{label}</span>;
}

function LiveBadge({ live }) {
  const s = { display: "inline-block", padding: "2px 8px", borderRadius: 12, fontSize: 11, fontWeight: 600,
    background: live ? 'var(--crown-ok-bg)' : 'var(--crown-surface-2)',
    color: live ? 'var(--crown-ok)' : 'var(--crown-muted)' };
  return <span style={s}>{live ? "LIVE" : "DEMO"}</span>;
}

function TextBadge({ label }) {
  const s = { display: "inline-block", padding: "2px 8px", borderRadius: 12, fontSize: 11, fontWeight: 600,
    background: 'var(--crown-surface-2)', color: 'var(--crown-muted)' };
  return <span style={s}>{label}</span>;
}

function WarnBanner({ children }) {
  return <div style={{ padding: "12px 16px", marginBottom: 16, background: 'var(--crown-warn-bg)', borderLeft: '4px solid var(--crown-warn)', borderRadius: 4 }}>{children}</div>;
}

function InfoBanner({ children }) {
  return <div style={{ padding: "12px 16px", marginBottom: 16, background: 'var(--crown-surface-2)', borderLeft: '4px solid var(--crown-brand)', borderRadius: 4 }}>{children}</div>;
}

/* ── Column definitions ──────────────────────────────────────────────── */
const riskColumns = [
  { key: "area",   label: "Area" },
  {
    key: "status",
    label: "Status",
    render: (r) => <StatusBadge label={r.status} />,
  },
  { key: "note", label: "Note" },
];

const driversColumns = [
  { key: "metric", label: "Metric" },
  { key: "value",  label: "Value",  align: "right" },
  { key: "note",   label: "Note" },
];

/* ── Page ────────────────────────────────────────────────────────────── */
/* Board Executive / Strategic Command KPI flip cards */
const ADMIN_KPI = [
  { label: "Net Tuition Rev",    value: "$6.8M",  trend: "+10% vs last yr",  trendUp: true,
    definition: "Gross tuition billings minus total aid awarded, year-to-date. Key indicator of financial sustainability.",
    dataSource: "Billing Module", dataHref: "/billing" },
  { label: "Staff Retention",    value: "87.2%",  trend: "+1.2% vs last yr", trendUp: true,
    definition: "Percentage of staff retained from start of year to today. Reflects culture and compensation health.",
    dataSource: "HR Module", dataHref: "/human-resources" },
  { label: "Cash Runway",        value: "6.5 mo", trend: "+0.4 mo",          trendUp: true,
    definition: "Months of operating expenses currently covered by unrestricted cash and liquid reserves.",
    dataSource: "Finance Module", dataHref: "/finance" },
  { label: "Yield Rate",         value: "11.2%",  trend: "-2.3%",            trendUp: false,
    definition: "Percentage of prospective-student inquiries that converted to enrolled students.",
    dataSource: "Admissions Pipeline", dataHref: "/admissions" },
  { label: "Re-enrollment Rate", value: "87.2%",  trend: "+41.6%",           trendUp: true,
    definition: "Percentage of currently-enrolled families who have completed re-enrollment for the next year.",
    dataSource: "Enrollment Module", dataHref: "/admissions" },
];
export default function BoardExecutiveDashboard() {
  const { token, schoolId } = getSession();
  const { data, loading, live, error } = useBoardExecutiveData({ token, schoolId });

  const [compass, setCompass] = useState(null);
  const [riskCounts, setRiskCounts] = useState(null);

  useEffect(() => {
    let dead = false;
    async function load() {
      const [c, r] = await Promise.all([
        fetchBoardCompass({ token, schoolId }),
        fetchBoardRiskCounts({ token, schoolId }),
      ]);
      if (!dead) {
        setCompass(c);
        setRiskCounts(r);
      }
    }
    load();
    return () => { dead = true; };
  }, [token, schoolId]);

  return (
    <CrownLayout
      title="Board Executive Dashboard"
      subtitle={`Read-only governance view${live ? " · LIVE" : " · DEMO data"}`}
    >
      <KpiStrip cards={ADMIN_KPI} />
      {error && (
        <WarnBanner>{error}</WarnBanner>
      )}
      {loading && (
        <InfoBanner>Loading latest board metrics…</InfoBanner>
      )}

      {/* ── Executive Snapshot ───────────────────────────────────────── */}
      <DashboardSection title="Executive Snapshot">
        <CrownGrid>
          <Col span={3}>
            <BoardKpiTile label="Enrollment" value={data.kpis.enrollment} meta="Current student count" />
          </Col>
          <Col span={3}>
            <BoardKpiTile label="Net Tuition" value={currency(data.kpis.netTuition)} meta="YTD recognized" />
          </Col>
          <Col span={3}>
            <BoardKpiTile label="Aid Awarded" value={currency(data.kpis.aidAwarded)} meta="YTD total awards" />
          </Col>
          <Col span={3}>
            <BoardKpiTile label="Attendance" value={`${data.kpis.attendancePct}%`} meta="Rolling 30 days" />
          </Col>
        </CrownGrid>
      </DashboardSection>

      {/* ── Trends ───────────────────────────────────────────────────── */}
      <DashboardSection title="Trends">
        <CrownGrid>
          <Col span={6}>
            <BoardCard title="Enrollment Trend" subtitle="Last 5 reporting periods" right={<LiveBadge live={live} />}>
              <BoardTrendChart data={data.trends.enrollment} yKey="value" />
            </BoardCard>
          </Col>
          <Col span={6}>
            <BoardCard title="Net Tuition Trend" subtitle="Last 5 reporting periods" right={<TextBadge label="USD" />}>
              <BoardTrendChart data={data.trends.netTuition} yKey="value" format="currency" />
            </BoardCard>
          </Col>
        </CrownGrid>
      </DashboardSection>

      {/* ── Crown Compass — demo signals (DEMO fallback data) ─────── */}
      <DashboardSection title="Crown Compass — Signals">
        <CrownGrid>
          <Col span={6}>
            <BoardCard title="Risk &amp; Watchlist" subtitle="Board-level attention items">
              <BoardSimpleTable columns={riskColumns} rows={data.risk} />
            </BoardCard>
          </Col>
          <Col span={6}>
            <BoardCard title="Top Drivers" subtitle="What is moving outcomes right now">
              <BoardSimpleTable columns={driversColumns} rows={data.topDrivers} />
            </BoardCard>
          </Col>
        </CrownGrid>
      </DashboardSection>

      {/* ── Crown Compass 2.0 — live composite indexes ────────────── */}
      {compass && (
        <DashboardSection title="Crown Compass 2.0">
          <CrownGrid>
            <Col span={12}>
              <BoardCompassCard compass={compass} />
            </Col>
          </CrownGrid>
        </DashboardSection>
      )}

      {/* ── Student Risk Distribution ─────────────────────────────── */}
      {riskCounts && (
        <DashboardSection title="Student Risk Distribution">
          <CrownGrid>
            <Col span={4}>
              <BoardKpiTile label="Low Risk" value={riskCounts.low} meta={`As of ${riskCounts.as_of_date}`} />
            </Col>
            <Col span={4}>
              <BoardKpiTile label="Medium Risk" value={riskCounts.med} meta="Needs monitoring" />
            </Col>
            <Col span={4}>
              <BoardKpiTile label="High Risk" value={riskCounts.high} meta="Intervention priority" />
            </Col>
          </CrownGrid>
        </DashboardSection>
      )}
      <DashboardSection title="Programs">
        <CrownGrid>
          <Col span={12}>
            <AftercareBoardCard token={token} schoolId={schoolId} />
          </Col>
        </CrownGrid>
      </DashboardSection>
    </CrownLayout>
  );
}
