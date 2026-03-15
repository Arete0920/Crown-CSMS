import React from 'react';
import { Grid, Stack, Typography } from '@mui/material';
import AdvancementSnapshotCard from '../components/dashboard/advancement/AdvancementSnapshotCard';
import AdvancementCampaignPanel from '../components/dashboard/advancement/AdvancementCampaignPanel';
import AdvancementPipelineCard from '../components/dashboard/advancement/AdvancementPipelineCard';

export default function AdvancementDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Advancement Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Giving health, campaign momentum, donor retention, church partnerships, and next actions.
        </Typography>
      </div>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <AdvancementSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <AdvancementCampaignPanel />
        </Grid>
        <Grid item xs={12}>
          <AdvancementPipelineCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
