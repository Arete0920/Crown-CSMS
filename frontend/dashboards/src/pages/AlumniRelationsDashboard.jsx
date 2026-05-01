import { Grid, Stack, Typography } from '@mui/material';
import AlumniSnapshotCard from '../components/dashboard/alumni/AlumniSnapshotCard';
import AlumniAlertsPanel from '../components/dashboard/alumni/AlumniAlertsPanel';
import AlumniQueueCard from '../components/dashboard/alumni/AlumniQueueCard';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

const ALUMNI_RELATIONS_KPI = [
  { label: 'Alumni Records', value: '—', dataSource: 'CRM' },
  { label: 'Events Planned', value: '—', dataSource: 'SIS' },
  { label: 'Giving Participation', value: '—', dataSource: 'Finance' },
  { label: 'Engaged This Year', value: '—', dataSource: 'CRM' }
];

export default function AlumniRelationsDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Alumni Relations Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Alumni records, engagement, event outreach, giving participation, and follow-up workload.
        </Typography>
      </div>

      <KpiStrip cards={ALUMNI_RELATIONS_KPI} />

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <AlumniSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <AlumniAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <AlumniQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
