import { Grid, Stack, Typography } from '@mui/material';
import ImplementationSuccessSnapshotCard from '../components/dashboard/implementationsuccess/ImplementationSuccessSnapshotCard';
import ImplementationSuccessAlertsPanel from '../components/dashboard/implementationsuccess/ImplementationSuccessAlertsPanel';
import ImplementationSuccessQueueCard from '../components/dashboard/implementationsuccess/ImplementationSuccessQueueCard';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

const IMPL_SUCCESS_KPI = [
  { label: 'Schools Onboarded', value: '—', dataSource: 'SIS' },
  { label: 'In Progress', value: '—', dataSource: 'SIS' },
  { label: 'Support Tickets', value: '—', dataSource: 'Support' },
  { label: 'At Risk', value: '—', dataSource: 'SIS' }
];

export default function ImplementationSuccessDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Implementation Success Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Launch readiness, school onboarding progress, training workload, and go-live risks.
        </Typography>
      </div>

      <KpiStrip cards={IMPL_SUCCESS_KPI} />

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <ImplementationSuccessSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <ImplementationSuccessAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <ImplementationSuccessQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
