import React from "react";
import { Box, Typography, Paper } from "@mui/material";

export default function SeatingChart({ seatingChart, students }) {
  const byId = React.useMemo(() => {
    const m = new Map();
    (students || []).forEach((s) => m.set(String(s.id), s.name));
    return m;
  }, [students]);

  const layout = seatingChart?.layout || {};
  const rows = layout.rows || 0;
  const cols = layout.cols || 0;

  const seatMap = React.useMemo(() => {
    const m = new Map();
    (layout.seats || []).forEach((s) => m.set(`${s.r}:${s.c}`, s.student_id));
    return m;
  }, [layout.seats]);

  if (!rows || !cols) {
    return <Typography variant="body2" sx={{ opacity: 0.8 }}>No seating chart.</Typography>;
  }

  return (
    <Box>
      <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>
        Seating Chart
      </Typography>

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))`,
          gap: 1,
        }}
      >
        {Array.from({ length: rows * cols }).map((_, idx) => {
          const r = Math.floor(idx / cols);
          const c = idx % cols;
          const sid = seatMap.get(`${r}:${c}`);
          const name = sid ? (byId.get(String(sid)) || "Student") : "—";
          return (
            <Paper
              key={`${r}-${c}`}
              variant="outlined"
              sx={{ p: 1, borderRadius: 2, minHeight: 54, display: "flex", alignItems: "center" }}
            >
              <Typography variant="caption" sx={{ opacity: sid ? 1 : 0.5 }}>
                {name}
              </Typography>
            </Paper>
          );
        })}
      </Box>
    </Box>
  );
}
