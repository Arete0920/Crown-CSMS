/**
 * BoardCompassCard — Crown Compass 2.0
 *
 * Renders assessed metrics and explicit unavailable states, plus highlights
 * and watchlist narrative snippets.
 *
 * Props:
 *   compass  — BoardExecutiveMetric object from /api/v1/signals/board/compass/
 *              { as_of_date, enrollment_health, financial_health, culture_health,
 *                mission_health, retention_risk, highlights, watchlist }
 */
import { Box, Chip, Divider, Grid, LinearProgress, Typography } from "@mui/material";
import BoardCard from "./BoardCard.jsx";

function ScoreBar({ label, value, percentage = false }) {
  const assessed = typeof value === "number" && Number.isFinite(value) && value >= 0 && value <= 100;
  if (!assessed) {
    return (
      <Box sx={{ mb: 2, display: "flex", justifyContent: "space-between" }}>
        <Typography variant="body2">{label}</Typography>
        <Chip size="small" label="Not assessed" />
      </Box>
    );
  }
  const v = value;
  // A raw percentage is not a validated institutional health grade.
  let color = "primary";
  if (!percentage) {
    if (v >= 80) color = "success";
    else if (v < 50) color = "error";
  }

  return (
    <Box sx={{ mb: 2 }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
        <Typography variant="body2">{label}</Typography>
        <Chip size="small" label={percentage ? `${v}%` : `${v}/100`} />
      </Box>
      <LinearProgress variant="determinate" value={v} color={color} />
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
            label="Aftercare students flagged high risk"
            value={compass.retention_risk}
            percentage
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
