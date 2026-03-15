import React from 'react';
import { Grid, Stack, Typography } from '@mui/material';
import DataMigrationSnapshotCard from '../components/dashboard/datamigration/DataMigrationSnapshotCard';
import DataMigrationAlertsPanel from '../components/dashboard/datamigration/DataMigrationAlertsPanel';
import DataMigrationQueueCard from '../components/dashboard/datamigration/DataMigrationQueueCard';

export default function DataMigrationDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Data Migration Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Import quality, mapping validation, cutover readiness, and migration execution risk.
        </Typography>
      </div>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <DataMigrationSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <DataMigrationAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <DataMigrationQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
