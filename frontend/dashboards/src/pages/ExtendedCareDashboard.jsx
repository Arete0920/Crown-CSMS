import { Grid, Stack, Typography } from '@mui/material';
import ExtendedCareSnapshotCard from '../components/dashboard/extendedcare/ExtendedCareSnapshotCard';
import ExtendedCareAlertsPanel from '../components/dashboard/extendedcare/ExtendedCareAlertsPanel';
import ExtendedCareQueueCard from '../components/dashboard/extendedcare/ExtendedCareQueueCard';

export default function ExtendedCareDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Extended Care Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Student roster, attendance, pickups, staffing, balances, and daily care readiness.
        </Typography>
      </div>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <ExtendedCareSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <ExtendedCareAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <ExtendedCareQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
