import { Grid, Stack } from '@mui/material';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import ActivitiesSnapshotCard from '../components/dashboard/activities/ActivitiesSnapshotCard.jsx';
import EligibilityAlertsPanel from '../components/dashboard/activities/EligibilityAlertsPanel.jsx';
import EventQueueCard from '../components/dashboard/activities/EventQueueCard.jsx';

export default function ActivitiesAthleticsDashboard() {
  return (
    <CrownLayout
      title="Activities and Athletics Dashboard"
      subtitle="Clubs, teams, eligibility, events, volunteers, and operational readiness"
    >
      <Stack spacing={3}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <ActivitiesSnapshotCard />
          </Grid>
          <Grid item xs={12} md={8}>
            <EligibilityAlertsPanel />
          </Grid>
          <Grid item xs={12}>
            <EventQueueCard />
          </Grid>
        </Grid>
      </Stack>
    </CrownLayout>
  );
}
