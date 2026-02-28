import { Grid, Alert, Chip } from "@mui/material";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import DashboardSection from "../components/layout/DashboardSection.jsx";
import BoardKpiTile from "../components/board/BoardKpiTile.jsx";
import BoardCard from "../components/board/BoardCard.jsx";
import BoardTrendChart from "../components/board/BoardTrendChart.jsx";
import BoardSimpleTable from "../components/board/BoardSimpleTable.jsx";
import { useBoardExecutiveData } from "../hooks/useBoardExecutiveData.js";

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

/* ── Risk status chip colors ─────────────────────────────────────────── */
const STATUS_COLOR = {
  Stable: "success",
  Watch:  "warning",
  Risk:   "error",
};

/* ── Column definitions ──────────────────────────────────────────────── */
const riskColumns = [
  { key: "area",   label: "Area" },
  {
    key: "status",
    label: "Status",
    render: (r) => (
      <Chip
        size="small"
        label={r.status}
        color={STATUS_COLOR[r.status] || "default"}
        sx={{ fontWeight: 600 }}
      />
    ),
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

  return (
    <CrownLayout
      title="Board Executive Dashboard"
      subtitle={`Read-only governance view${live ? " · LIVE" : " · DEMO data"}`}
    >
      {error && (
        <Alert severity="warning" sx={{ mb: 2 }}>{error}</Alert>
      )}
      {loading && (
        <Alert severity="info" sx={{ mb: 2 }}>Loading latest board metrics…</Alert>
      )}

      {/* ── Executive Snapshot ───────────────────────────────────────── */}
      <DashboardSection title="Executive Snapshot">
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <BoardKpiTile
              label="Enrollment"
              value={data.kpis.enrollment}
              meta="Current student count"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <BoardKpiTile
              label="Net Tuition"
              value={currency(data.kpis.netTuition)}
              meta="YTD recognized"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <BoardKpiTile
              label="Aid Awarded"
              value={currency(data.kpis.aidAwarded)}
              meta="YTD total awards"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <BoardKpiTile
              label="Attendance"
              value={`${data.kpis.attendancePct}%`}
              meta="Rolling 30 days"
            />
          </Grid>
        </Grid>
      </DashboardSection>

      {/* ── Trends ───────────────────────────────────────────────────── */}
      <DashboardSection title="Trends">
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <BoardCard
              title="Enrollment Trend"
              subtitle="Last 5 reporting periods"
              right={<Chip size="small" label={live ? "LIVE" : "DEMO"} color={live ? "success" : "default"} />}
            >
              <BoardTrendChart data={data.trends.enrollment} yKey="value" />
            </BoardCard>
          </Grid>
          <Grid item xs={12} md={6}>
            <BoardCard
              title="Net Tuition Trend"
              subtitle="Last 5 reporting periods"
              right={<Chip size="small" label="USD" />}
            >
              <BoardTrendChart
                data={data.trends.netTuition}
                yKey="value"
                format="currency"
              />
            </BoardCard>
          </Grid>
        </Grid>
      </DashboardSection>

      {/* ── Crown Compass ────────────────────────────────────────────── */}
      <DashboardSection title="Crown Compass">
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <BoardCard
              title="Risk &amp; Watchlist"
              subtitle="Board-level attention items"
            >
              <BoardSimpleTable columns={riskColumns} rows={data.risk} />
            </BoardCard>
          </Grid>
          <Grid item xs={12} md={6}>
            <BoardCard
              title="Top Drivers"
              subtitle="What is moving outcomes right now"
            >
              <BoardSimpleTable columns={driversColumns} rows={data.topDrivers} />
            </BoardCard>
          </Grid>
        </Grid>
      </DashboardSection>
    </CrownLayout>
  );
}
