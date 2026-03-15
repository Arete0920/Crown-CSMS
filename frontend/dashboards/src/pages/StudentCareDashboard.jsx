import React from 'react';
import { Grid, Stack } from '@mui/material';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import StudentCareSnapshotCard from '../components/dashboard/studentcare/StudentCareSnapshotCard.jsx';
import StudentCareAlertsPanel from '../components/dashboard/studentcare/StudentCareAlertsPanel.jsx';
import InterventionQueueCard from '../components/dashboard/studentcare/InterventionQueueCard.jsx';

export default function StudentCareDashboard() {
  return (
    <CrownLayout
      title="Student Care Dashboard"
      subtitle="Care cases, discipline patterns, attendance-linked concerns, and intervention follow-up"
    >
      <Stack spacing={3}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <StudentCareSnapshotCard />
          </Grid>
          <Grid item xs={12} md={8}>
            <StudentCareAlertsPanel />
          </Grid>
          <Grid item xs={12}>
            <InterventionQueueCard />
          </Grid>
        </Grid>
      </Stack>
    </CrownLayout>
  );
}
