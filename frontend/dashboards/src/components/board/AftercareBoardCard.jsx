import { useEffect, useState } from "react";
import { Box, Grid, CircularProgress, Alert } from "@mui/material";
import BoardCard from "./BoardCard.jsx";
import BoardKpiTile from "./BoardKpiTile.jsx";
import { getAftercareBoardSummary } from "../../api/aftercareApi.js";

function numericMetric(value) {
  if (value === null || value === undefined) return null;
  if (typeof value === "string" && value.trim() === "") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function metricValue(value) {
  const number = numericMetric(value);
  return number === null ? "Unavailable" : number;
}

export default function AftercareBoardCard({ token, schoolId }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const response = await getAftercareBoardSummary({ token, schoolId });
        if (!response || typeof response !== "object" || Array.isArray(response)) {
          throw new Error("Aftercare board data returned an invalid response.");
        }
        if (!cancelled) setData(response);
      } catch (e) {
        if (!cancelled) setError(e?.message || "Unable to load aftercare board data.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, [token, schoolId]);

  if (loading) return <Box sx={{ p: 2 }}><CircularProgress size={24} /></Box>;
  if (error) return <Alert severity="warning">Aftercare data unavailable: {error}</Alert>;
  if (!data) return null;

  const lateFeeRevenue = numericMetric(data.late_fee_revenue_mtd);

  return (
    <BoardCard title="Aftercare — Monthly Dashboard" subtitle={`As of ${data.as_of || "current period"}`}>
      <Grid container spacing={2}>
        <Grid item xs={6} sm={4} md={2}><BoardKpiTile label="Active Enrollment" value={metricValue(data.active_enrollment)} /></Grid>
        <Grid item xs={6} sm={4} md={2}><BoardKpiTile label="Sessions MTD" value={metricValue(data.sessions_mtd)} /></Grid>
        <Grid item xs={6} sm={4} md={2}><BoardKpiTile label="Late Pickups MTD" value={metricValue(data.late_pickups_mtd)} /></Grid>
        <Grid item xs={6} sm={4} md={2}><BoardKpiTile label="Incidents MTD" value={metricValue(data.incidents_mtd)} /></Grid>
        <Grid item xs={6} sm={4} md={2}>
          <BoardKpiTile label="Late Fee Revenue MTD" value={lateFeeRevenue === null ? "Unavailable" : `$${lateFeeRevenue.toFixed(2)}`} />
        </Grid>
      </Grid>
    </BoardCard>
  );
}
