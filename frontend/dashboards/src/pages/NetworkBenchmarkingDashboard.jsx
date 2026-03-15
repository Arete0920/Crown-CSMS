import React from 'react';
import { Grid, Stack, Typography } from '@mui/material';
import NetworkBenchmarkSnapshotCard from '../components/dashboard/networkbenchmarking/NetworkBenchmarkSnapshotCard';
import NetworkBenchmarkAlertsPanel from '../components/dashboard/networkbenchmarking/NetworkBenchmarkAlertsPanel';
import NetworkBenchmarkQueueCard from '../components/dashboard/networkbenchmarking/NetworkBenchmarkQueueCard';

export default function NetworkBenchmarkingDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Network Benchmarking Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Cross-school performance comparison, portfolio variance, strategic outliers, and support follow-up.
        </Typography>
      </div>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <NetworkBenchmarkSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <NetworkBenchmarkAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <NetworkBenchmarkQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
