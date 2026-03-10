import React from 'react';
import { Grid, Stack, Typography } from '@mui/material';
import CurriculumPDSnapshotCard from '../components/dashboard/curriculumpd/CurriculumPDSnapshotCard';
import CurriculumPDAlertsPanel from '../components/dashboard/curriculumpd/CurriculumPDAlertsPanel';
import CurriculumPDQueueCard from '../components/dashboard/curriculumpd/CurriculumPDQueueCard';

export default function CurriculumPDDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Curriculum / PD Hub Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Curriculum reviews, teacher professional development, resource support, and follow-up workload.
        </Typography>
      </div>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <CurriculumPDSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <CurriculumPDAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <CurriculumPDQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
