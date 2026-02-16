import React, { useEffect, useMemo, useState } from "react";
import { Card, CardContent, Typography, Divider, Stack, LinearProgress, Box } from "@mui/material";
import { fetchCurriculumPacingSummary } from "../api/curriculum";

export default function CurriculumPacingCard({ baseUrl, token, schoolId }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    let alive = true;
    setErr("");
    setData(null);

    fetchCurriculumPacingSummary({ baseUrl, token, schoolId })
      .then((json) => alive && setData(json))
      .catch((e) => alive && setErr(e?.message || String(e)));

    return () => { alive = false; };
  }, [baseUrl, token, schoolId]);

  const rows = useMemo(() => data?.results || [], [data]);

  const asOf = rows?.[0]?.pacing?.as_of || null;

  return (
    <Card variant="outlined">
      <CardContent>
        <Stack spacing={1.5}>
          <Typography variant="h6">Curriculum Pacing</Typography>
          <Typography variant="body2" color="text.secondary">
            {asOf ? `As of ${asOf}` : "As of today"}
          </Typography>
          <Divider />

          {err ? (
            <Typography variant="body2" color="error">{err}</Typography>
          ) : !data ? (
            <Typography variant="body2" color="text.secondary">Loading…</Typography>
          ) : rows.length === 0 ? (
            <Typography variant="body2" color="text.secondary">No active courses found.</Typography>
          ) : (
            <Stack spacing={1.25}>
              {rows.map((c) => {
                const pct = c?.pacing?.pct_due ?? 0;
                const due = c?.pacing?.due_lessons ?? 0;
                const total = c?.pacing?.total_lessons ?? 0;
                return (
                  <Box key={c.course_id}>
                    <Stack direction="row" justifyContent="space-between" alignItems="baseline">
                      <Typography variant="subtitle2">
                        {c.code} — {c.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {pct}% ({due}/{total})
                      </Typography>
                    </Stack>
                    <LinearProgress variant="determinate" value={pct} />
                  </Box>
                );
              })}
            </Stack>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}
