import React, { useEffect, useState } from "react";
import { Card, CardContent, Chip, Grid, Typography } from "@mui/material";
import releaseApi from "../../lib/releaseApi";

type StatusPayload = {
  discipline_escalation: boolean;
  transcript_export: boolean;
  report_card_export: boolean;
  graduation_readiness: boolean;
  board_report_export: boolean;
  sms_surface: boolean;
  live_metrics: {
    green: boolean;
    mock_or_seed_hits: number;
  };
};

function Row({ label, value, testId }: { label: string; value: boolean; testId: string }) {
  return (
    <Grid container justifyContent="space-between" alignItems="center" sx={{ py: 0.75 }}>
      <Grid item>
        <Typography variant="body2">{label}</Typography>
      </Grid>
      <Grid item>
        <Chip
          size="small"
          label={value ? "GREEN" : "OPEN"}
          color={value ? "success" : "warning"}
          data-testid={testId}
        />
      </Grid>
    </Grid>
  );
}

export default function ReleaseStatusMatrix() {
  const [payload, setPayload] = useState<StatusPayload | null>(null);

  useEffect(() => {
    releaseApi.get("/api/v1/release-closeout/status/")
      .then((res) => setPayload(res.data))
      .catch((err) => {
        console.error("ReleaseStatusMatrix failed to load release status", err);
        setPayload(null);
      });
  }, []);

  return (
    <Card sx={{ borderRadius: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom data-testid="release-status-title">
          Release Status Matrix
        </Typography>
        {!payload ? (
          <Typography variant="body2" data-testid="release-status-unavailable">
            Release status endpoint unavailable
          </Typography>
        ) : (
          <>
            <Row label="Discipline escalation" value={payload.discipline_escalation} testId="release-status-discipline" />
            <Row label="Transcript export" value={payload.transcript_export} testId="release-status-transcript" />
            <Row label="Report card export" value={payload.report_card_export} testId="release-status-report-card" />
            <Row label="Graduation readiness" value={payload.graduation_readiness} testId="release-status-graduation" />
            <Row label="Board report export" value={payload.board_report_export} testId="release-status-board" />
            <Row label="SMS surface" value={payload.sms_surface} testId="release-status-sms" />
            <Row label="Live metrics clean" value={payload.live_metrics.green} testId="release-status-metrics" />
            <Typography variant="caption" sx={{ pt: 1.5, display: "block" }} data-testid="release-status-mock-seed-hits">
              Mock/Seed hits: {payload.live_metrics.mock_or_seed_hits}
            </Typography>
          </>
        )}
      </CardContent>
    </Card>
  );
}