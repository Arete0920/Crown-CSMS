import React from 'react';
import { Grid, Stack } from '@mui/material';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import GradebookSnapshotCard from '../components/dashboard/gradebook/GradebookSnapshotCard.jsx';
import GradebookAlertsPanel from '../components/dashboard/gradebook/GradebookAlertsPanel.jsx';
import TeacherPostingQueueCard from '../components/dashboard/gradebook/TeacherPostingQueueCard.jsx';

export default function GradebookDashboard() {
  return (
    <CrownLayout
      title="Gradebook Dashboard"
      subtitle="Assignment completion, grading health, academic risk, and teacher posting status"
    >
      <Stack spacing={3}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <GradebookSnapshotCard />
          </Grid>
          <Grid item xs={12} md={8}>
            <GradebookAlertsPanel />
          </Grid>
          <Grid item xs={12}>
            <TeacherPostingQueueCard />
          </Grid>
        </Grid>
      </Stack>
    </CrownLayout>
  );
}
