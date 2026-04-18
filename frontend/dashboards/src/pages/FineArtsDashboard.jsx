import { Grid, Stack, Typography } from '@mui/material';
import FineArtsSnapshotCard from '../components/dashboard/finearts/FineArtsSnapshotCard';
import FineArtsAlertsPanel from '../components/dashboard/finearts/FineArtsAlertsPanel';
import FineArtsQueueCard from '../components/dashboard/finearts/FineArtsQueueCard';

export default function FineArtsDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Fine Arts Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Programs, performances, rehearsals, equipment readiness, and production follow-up.
        </Typography>
      </div>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <FineArtsSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <FineArtsAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <FineArtsQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
