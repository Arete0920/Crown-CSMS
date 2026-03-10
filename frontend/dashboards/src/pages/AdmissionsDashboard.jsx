import React from 'react';
import { Grid, Stack, Typography } from '@mui/material';
import AdmissionsSnapshotCard from '../components/dashboard/admissions/AdmissionsSnapshotCard';
import AdmissionsPipelinePanel from '../components/dashboard/admissions/AdmissionsPipelinePanel';
import AdmissionsYieldCard from '../components/dashboard/admissions/AdmissionsYieldCard';

export default function AdmissionsDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Admissions Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Funnel health, application progress, mission-fit review, and deposit conversion.
        </Typography>
      </div>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <AdmissionsSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <AdmissionsPipelinePanel />
        </Grid>
        <Grid item xs={12}>
          <AdmissionsYieldCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
