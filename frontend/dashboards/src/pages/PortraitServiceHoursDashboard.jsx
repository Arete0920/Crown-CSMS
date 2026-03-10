import React from 'react';
import { Grid, Stack, Typography } from '@mui/material';
import PortraitServiceSnapshotCard from '../components/dashboard/portraitservice/PortraitServiceSnapshotCard';
import PortraitServiceAlertsPanel from '../components/dashboard/portraitservice/PortraitServiceAlertsPanel';
import PortraitServiceQueueCard from '../components/dashboard/portraitservice/PortraitServiceQueueCard';

export default function PortraitServiceHoursDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Portrait / Service Hours Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Service-hour progress, portrait evidence, mentor review flow, and partner-site oversight.
        </Typography>
      </div>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <PortraitServiceSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <PortraitServiceAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <PortraitServiceQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
