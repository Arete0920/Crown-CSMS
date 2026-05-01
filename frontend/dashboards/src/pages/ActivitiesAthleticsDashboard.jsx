import { Grid, Stack } from '@mui/material';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import ActivitiesSnapshotCard from '../components/dashboard/activities/ActivitiesSnapshotCard.jsx';
import EligibilityAlertsPanel from '../components/dashboard/activities/EligibilityAlertsPanel.jsx';
import EventQueueCard from '../components/dashboard/activities/EventQueueCard.jsx';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

const ACTIVITIES_KPI = [
  { label: 'Active Clubs', value: '—', dataSource: 'SIS' },
  { label: 'Teams Enrolled', value: '—', dataSource: 'SIS' },
  { label: 'Events This Week', value: '—', dataSource: 'SIS' },
  { label: 'Eligibility Holds', value: '—', dataSource: 'SIS' }
];

export default function ActivitiesAthleticsDashboard() {
  return (
    <CrownLayout
      title="Activities and Athletics Dashboard"
      subtitle="Clubs, teams, eligibility, events, volunteers, and operational readiness"
    >
      <KpiStrip cards={ACTIVITIES_KPI} />
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
      <KpiStrip cards={ACTIVITIES_KPI} />
      </Stack>
    </CrownLayout>
  );
}
