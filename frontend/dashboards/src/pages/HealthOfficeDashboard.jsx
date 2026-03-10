import React from 'react';
import { Grid, Stack, Typography } from '@mui/material';
import HealthOfficeSnapshotCard from '../components/dashboard/healthoffice/HealthOfficeSnapshotCard';
import HealthOfficeAlertsPanel from '../components/dashboard/healthoffice/HealthOfficeAlertsPanel';
import HealthOfficeQueueCard from '../components/dashboard/healthoffice/HealthOfficeQueueCard';

export default function HealthOfficeDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Health Office Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Nurse visits, medications, medical document follow-up, and care plan readiness.
        </Typography>
      </div>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <HealthOfficeSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <HealthOfficeAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <HealthOfficeQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
