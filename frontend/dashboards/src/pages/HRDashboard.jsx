import React from 'react';
import { Grid, Stack, Typography } from '@mui/material';
import HRSnapshotCard from '../components/dashboard/hr/HRSnapshotCard';
import HRAlertsPanel from '../components/dashboard/hr/HRAlertsPanel';
import HRWorkQueueCard from '../components/dashboard/hr/HRWorkQueueCard';

export default function HRDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          HR Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Staffing readiness, onboarding, compliance, reviews, and absence coverage.
        </Typography>
      </div>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <HRSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <HRAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <HRWorkQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
