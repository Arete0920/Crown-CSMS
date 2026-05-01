import { Grid, Stack, Typography } from '@mui/material';
import HRSnapshotCard from '../components/dashboard/hr/HRSnapshotCard';
import HRAlertsPanel from '../components/dashboard/hr/HRAlertsPanel';
import HRWorkQueueCard from '../components/dashboard/hr/HRWorkQueueCard';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

const HR_KPI = [
  { label: 'Active Staff', value: '—', dataSource: 'HRIS' },
  { label: 'On Leave', value: '—', dataSource: 'HRIS' },
  { label: 'Open Positions', value: '—', dataSource: 'HRIS' },
  { label: 'Background Checks', value: '—', dataSource: 'HRIS' }
];

export default function HRDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          HR Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Staffing readiness, onboarding, compliance, reviews, and absence coverage.
        </Typography>
      </div>

      <KpiStrip cards={HR_KPI} />

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <HRSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <HRAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <HRWorkQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
