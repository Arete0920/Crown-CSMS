import { Grid, Stack, Typography } from '@mui/material';
import AthleticsDirectorSnapshotCard from '../components/dashboard/athleticsdirector/AthleticsDirectorSnapshotCard';
import AthleticsDirectorAlertsPanel from '../components/dashboard/athleticsdirector/AthleticsDirectorAlertsPanel';
import AthleticsDirectorQueueCard from '../components/dashboard/athleticsdirector/AthleticsDirectorQueueCard';

export default function AthleticsDirectorDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Athletics Director Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Team operations, eligibility, transportation, compliance, and event readiness.
        </Typography>
      </div>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <AthleticsDirectorSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <AthleticsDirectorAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <AthleticsDirectorQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
