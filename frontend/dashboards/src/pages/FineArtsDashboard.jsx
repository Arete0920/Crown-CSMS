import { Grid, Stack, Typography } from '@mui/material';
import FineArtsSnapshotCard from '../components/dashboard/finearts/FineArtsSnapshotCard';
import FineArtsAlertsPanel from '../components/dashboard/finearts/FineArtsAlertsPanel';
import FineArtsQueueCard from '../components/dashboard/finearts/FineArtsQueueCard';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

const FINE_ARTS_KPI = [
  { label: 'Students Enrolled', value: '—', dataSource: 'SIS' },
  { label: 'Performances Scheduled', value: '—', dataSource: 'SIS' },
  { label: 'Practice Hours Logged', value: '—', dataSource: 'SIS' },
  { label: 'Productions This Year', value: '—', dataSource: 'SIS' }
];

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

      <KpiStrip cards={FINE_ARTS_KPI} />

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
