import React from 'react';
import { Grid, Stack, Typography } from '@mui/material';
import VolunteerSnapshotCard from '../components/dashboard/volunteermanagement/VolunteerSnapshotCard';
import VolunteerAlertsPanel from '../components/dashboard/volunteermanagement/VolunteerAlertsPanel';
import VolunteerQueueCard from '../components/dashboard/volunteermanagement/VolunteerQueueCard';

export default function VolunteerManagementDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Volunteer Management Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Volunteer supply, clearances, event coverage, hour tracking, and coordination workload.
        </Typography>
      </div>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <VolunteerSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <VolunteerAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <VolunteerQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
