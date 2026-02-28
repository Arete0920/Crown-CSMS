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

/* ── Auth helpers (matches Crown sessionStorage pattern) ─────────────── */
function getSession() {
  try {
    return {
      token:    sessionStorage.getItem("crown.jwt.access") || "",
      schoolId: sessionStorage.getItem("crown.school.id")  || "",
    };
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
const STATUS_BG   = { Stable: "#e8f5e9", Watch: "#fffde7", Risk:  "#ffebee" };
const STATUS_TEXT = { Stable: "#1b5e20", Watch: "#f57f17", Risk:  "#b71c1c" };

function StatusBadge({ label }) {
  const s = {
    display: "inline-block", padding: "2px 10px", borderRadius: 12,
    fontSize: 12, fontWeight: 600,
    background: STATUS_BG[label]   || "#f5f5f5",
    color:      STATUS_TEXT[label] || "#333",
  };
  return <span style={s}>{label}</span>;
}

function LiveBadge({ live }) {
  const s = { display: "inline-block", padding: "2px 8px", borderRadius: 12, fontSize: 11, fontWeight: 600, background: live ? "#e8f5e9" : "#f5f5f5", color: live ? "#1b5e20" : "#888" };
  return <span style={s}>{live ? "LIVE" : "DEMO"}</span>;
}

function TextBadge({ label }) {
  const s = { display: "inline-block", padding: "2px 8px", borderRadius: 12, fontSize: 11, fontWeight: 600, background: "#f5f5f5", color: "#888" };
  return <span style={s}>{label}</span>;
}

function WarnBanner({ children }) {
  return <div style={{ padding: "12px 16px", marginBottom: 16, background: "#fff3e0", borderLeft: "4px solid #ef6c00", borderRadius: 4 }}>{children}</div>;
}

function InfoBanner({ children }) {
  return <div style={{ padding: "12px 16px", marginBottom: 16, background: "#e3f2fd", borderLeft: "4px solid #1565c0", borderRadius: 4 }}>{children}</div>;
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
