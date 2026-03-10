import React from 'react';
import { Grid, Stack, Typography } from '@mui/material';
import LibraryMediaSnapshotCard from '../components/dashboard/librarymedia/LibraryMediaSnapshotCard';
import LibraryMediaAlertsPanel from '../components/dashboard/librarymedia/LibraryMediaAlertsPanel';
import LibraryMediaQueueCard from '../components/dashboard/librarymedia/LibraryMediaQueueCard';

export default function LibraryMediaDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Library / Media Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Circulation, resource requests, media support, scheduling conflicts, and readiness.
        </Typography>
      </div>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <LibraryMediaSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <LibraryMediaAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <LibraryMediaQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
