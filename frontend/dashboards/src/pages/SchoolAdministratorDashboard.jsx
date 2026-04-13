import { Grid, Stack, Typography } from '@mui/material';
import AdminSnapshotCard from '../components/dashboard/admin/AdminSnapshotCard';
import AdminPriorityPanel from '../components/dashboard/admin/AdminPriorityPanel';
import AdminOperationalReadinessCard from '../components/dashboard/admin/AdminOperationalReadinessCard';

export default function SchoolAdministratorDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          School Administrator Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Executive operational view of enrollment, tuition, intervention pressure, and school-wide priorities.
        </Typography>
      </div>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <AdminSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <AdminPriorityPanel />
        </Grid>
        <Grid item xs={12}>
          <AdminOperationalReadinessCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
