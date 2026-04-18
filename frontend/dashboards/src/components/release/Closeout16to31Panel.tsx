import React, { useEffect, useState } from "react";
import { Card, CardContent, Chip, Grid, Typography } from "@mui/material";
import axios from "axios";

type LiveMetrics = {
  backend_python_files: number;
  frontend_tsx_files: number;
  workflow_files: number;
  release_docs: number;
  mock_or_seed_hits: number;
  green: boolean;
};

type Payload = {
  discipline_escalation: boolean;
  transcript_export: boolean;
  report_card_export: boolean;
  graduation_readiness: boolean;
  live_metrics: LiveMetrics;
  board_report_export: boolean;
  sms_surface: boolean;
};

const Row = ({ label, ok }: { label: string; ok: boolean }) => (
  <Grid container alignItems="center" justifyContent="space-between" sx={{ py: 0.75 }}>
    <Grid item>
      <Typography variant="body2">{label}</Typography>
    </Grid>
    <Grid item>
      <Chip size="small" color={ok ? "success" : "warning"} label={ok ? "GREEN" : "OPEN"} />
    </Grid>
  </Grid>
);

export default function Closeout16to31Panel() {
  const [payload, setPayload] = useState<Payload | null>(null);

  useEffect(() => {
    axios.get("/api/v1/release-closeout/status/").then((res) => setPayload(res.data)).catch(() => {
      setPayload(null);
    });
  }, []);

  return (
    <Card sx={{ borderRadius: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>Release Closeout 16â€“31</Typography>
        {!payload ? (
          <Typography variant="body2">Endpoint unavailable. Wire routes and re-run ship candidate.</Typography>
        ) : (
          <>
            <Row label="Discipline escalation" ok={payload.discipline_escalation} />
            <Row label="Transcript export" ok={payload.transcript_export} />
            <Row label="Report-card export" ok={payload.report_card_export} />
            <Row label="Graduation readiness" ok={payload.graduation_readiness} />
            <Row label="Board report export" ok={payload.board_report_export} />
            <Row label="SMS surface" ok={payload.sms_surface} />
            <Row label="Live metrics clean" ok={payload.live_metrics.green} />
            <Typography variant="caption" display="block" sx={{ pt: 1.5 }}>
              Mock/Seed hits: {payload.live_metrics.mock_or_seed_hits}
            </Typography>
          </>
        )}
      </CardContent>
    </Card>
  );
}