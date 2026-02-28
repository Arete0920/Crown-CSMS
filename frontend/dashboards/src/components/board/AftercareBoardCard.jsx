import { useEffect, useState } from "react";
import { Box, Grid, CircularProgress, Alert } from "@mui/material";
import BoardCard from "./BoardCard.jsx";
import BoardKpiTile from "./BoardKpiTile.jsx";
import { getAftercareBoardSummary } from "../../api/aftercareApi.js";

/**
 * AftercareBoardCard — board-level governance summary.
 * Props: token (string), schoolId (string|number)
 * No PII. Renders enrollment, sessions MTD, late pickups, incidents, fee revenue.
 */
export default function AftercareBoardCard({ token, schoolId }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await getAftercareBoardSummary({ token, schoolId });
        setData(res);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [token, schoolId]);

  if (loading) return <Box sx={{ p: 2 }}><CircularProgress size={24} /></Box>;
  if (error) return <Alert severity="warning">Aftercare data unavailable: {error}</Alert>;
  if (!data) return null;

  return (
    <BoardCard title="Aftercare — Monthly Dashboard" subtitle={`As of ${data.as_of}`}>
      <Grid container spacing={2}>
        <Grid item xs={6} sm={4} md={2}>
          <BoardKpiTile label="Active Enrollment" value={data.active_enrollment} />
        </Grid>
        <Grid item xs={6} sm={4} md={2}>
          <BoardKpiTile label="Sessions MTD" value={data.sessions_mtd} />
        </Grid>
        <Grid item xs={6} sm={4} md={2}>
          <BoardKpiTile label="Late Pickups MTD" value={data.late_pickups_mtd} />
        </Grid>
        <Grid item xs={6} sm={4} md={2}>
          <BoardKpiTile label="Incidents MTD" value={data.incidents_mtd} />
        </Grid>
        <Grid item xs={6} sm={4} md={2}>
          <BoardKpiTile
            label="Late Fee Revenue MTD"
            value={`$${data.late_fee_revenue_mtd.toFixed(2)}`}
          />
        </Grid>
      </Grid>
    </BoardCard>
  );
}
