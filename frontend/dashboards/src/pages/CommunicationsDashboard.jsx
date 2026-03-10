import React from 'react';
import { Grid, Stack } from '@mui/material';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CommunicationsSnapshotCard from '../components/dashboard/communications/CommunicationsSnapshotCard.jsx';
import CommunicationsAlertsPanel from '../components/dashboard/communications/CommunicationsAlertsPanel.jsx';
import OutreachQueueCard from '../components/dashboard/communications/OutreachQueueCard.jsx';

export default function CommunicationsDashboard() {
  return (
    <CrownLayout
      title="Communications Dashboard"
      subtitle="Family threads, staff messaging, escalations, and outreach operations"
    >
      <Stack spacing={3}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <CommunicationsSnapshotCard />
          </Grid>
          <Grid item xs={12} md={8}>
            <CommunicationsAlertsPanel />
          </Grid>
          <Grid item xs={12}>
            <OutreachQueueCard />
          </Grid>
        </Grid>
      </Stack>
    </CrownLayout>
  );
}
