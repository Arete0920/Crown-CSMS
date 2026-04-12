import React, { useEffect, useState } from "react";
import { Card, CardContent, Chip, Grid, Typography } from "@mui/material";
import releaseApi from "../../lib/releaseApi";

type Payload = {
  total_w002: number;
  budget_current_max: number;
  budget_pass: boolean;
  budget_next_target: number;
};

export default function SchemaStatusWidget() {
  const [payload, setPayload] = useState<Payload | null>(null);

  useEffect(() => {
    fetch("/audit-artifacts/release-verify/schema_w002_summary.json")
      .then((res) => res.json())
      .then((data) => setPayload(data))
      .catch(() => setPayload(null));
  }, []);

  return (
    <Card sx={{ borderRadius: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom data-testid="schema-status-title">
          Schema W002 Status
        </Typography>
        {!payload ? (
          <Typography variant="body2" data-testid="schema-status-unavailable">
            Schema summary unavailable
          </Typography>
        ) : (
          <>
            <Grid container justifyContent="space-between" alignItems="center" sx={{ py: 0.75 }}>
              <Grid item><Typography variant="body2">Current W002</Typography></Grid>
              <Grid item><Typography variant="body2" data-testid="schema-status-count">{payload.total_w002}</Typography></Grid>
            </Grid>
            <Grid container justifyContent="space-between" alignItems="center" sx={{ py: 0.75 }}>
              <Grid item><Typography variant="body2">Budget Max</Typography></Grid>
              <Grid item><Typography variant="body2" data-testid="schema-status-budget">{payload.budget_current_max}</Typography></Grid>
            </Grid>
            <Grid container justifyContent="space-between" alignItems="center" sx={{ py: 0.75 }}>
              <Grid item><Typography variant="body2">Gate</Typography></Grid>
              <Grid item>
                <Chip
                  size="small"
                  label={payload.budget_pass ? "GREEN" : "OPEN"}
                  color={payload.budget_pass ? "success" : "warning"}
                  data-testid="schema-status-gate"
                />
              </Grid>
            </Grid>
            <Typography variant="caption" display="block" sx={{ pt: 1.0 }} data-testid="schema-status-next-target">
              Next target: {payload.budget_next_target}
            </Typography>
          </>
        )}
      </CardContent>
    </Card>
  );
}