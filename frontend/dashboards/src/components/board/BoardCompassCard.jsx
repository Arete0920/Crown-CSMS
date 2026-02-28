/**
 * BoardCompassCard — Crown Compass 2.0
 *
 * Renders deterministic composite health indexes (0..100) as labeled progress
 * bars, plus highlights and watchlist narrative snippets.
 *
 * Props:
 *   compass  — BoardExecutiveMetric object from /api/v1/signals/board/compass/
 *              { as_of_date, enrollment_health, financial_health, culture_health,
 *                mission_health, retention_risk, highlights, watchlist }
 */
import { Box, Chip, Divider, Grid, LinearProgress, Typography } from "@mui/material";
import BoardCard from "./BoardCard.jsx";

function ScoreBar({ label, value, invert = false }) {
  const v = typeof value === "number" ? value : 0;
  const displayed = invert ? 100 - v : v;

  let color = "primary";
  if (displayed >= 80) color = "success";
  else if (displayed < 50) color = "error";

  return (
    <Box sx={{ mb: 2 }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
        <Typography variant="body2">{label}</Typography>
        <Chip size="small" label={`${displayed}/100`} />
      </Box>
      <LinearProgress variant="determinate" value={displayed} color={color} />
    </Box>
  );
}

export default function BoardCompassCard({ compass }) {
  if (!compass) return null;

  return (
    <BoardCard title="Crown Compass 2.0" subtitle={`As of ${compass.as_of_date}`}>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <ScoreBar label="Enrollment Health"  value={compass.enrollment_health} />
          <ScoreBar label="Financial Health"   value={compass.financial_health} />
          <ScoreBar label="Culture Health"     value={compass.culture_health} />
          <ScoreBar label="Mission Health"     value={compass.mission_health} />
          <ScoreBar
            label="Retention Risk (lower = better)"
            value={compass.retention_risk}
            invert
          />
        </Grid>

        <Grid item xs={12} md={6}>
          {compass.highlights?.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
                Highlights
              </Typography>
              {compass.highlights.map((h, i) => (
                <Typography key={i} variant="body2" sx={{ mt: 0.5 }}>
                  • {h}
                </Typography>
              ))}
            </Box>
          )}

          <Divider sx={{ my: 1 }} />

          {compass.watchlist?.length > 0 && (
            <Box>
              <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
                Watchlist
              </Typography>
              {compass.watchlist.map((w, i) => (
                <Typography key={i} variant="body2" color="error.main" sx={{ mt: 0.5 }}>
                  • {w}
                </Typography>
              ))}
            </Box>
          )}
        </Grid>
      </Grid>
    </BoardCard>
  );
}
