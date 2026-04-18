import { Grid, Stack, Typography } from '@mui/material';
import FacilitiesSnapshotCard from '../components/dashboard/facilities/FacilitiesSnapshotCard';
import FacilitiesAlertsPanel from '../components/dashboard/facilities/FacilitiesAlertsPanel';
import FacilitiesQueueCard from '../components/dashboard/facilities/FacilitiesQueueCard';

export default function FacilitiesDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Facilities Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Work orders, repairs, inspections, room readiness, and event setup status.
        </Typography>
      </div>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <FacilitiesSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <FacilitiesAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <FacilitiesQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
