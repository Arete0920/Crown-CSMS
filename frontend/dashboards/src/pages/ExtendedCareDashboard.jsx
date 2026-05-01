import { Grid, Stack, Typography } from '@mui/material';
import ExtendedCareSnapshotCard from '../components/dashboard/extendedcare/ExtendedCareSnapshotCard';
import ExtendedCareAlertsPanel from '../components/dashboard/extendedcare/ExtendedCareAlertsPanel';
import ExtendedCareQueueCard from '../components/dashboard/extendedcare/ExtendedCareQueueCard';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

const EXTENDED_CARE_KPI = [
  { label: 'Children Enrolled', value: '—', dataSource: 'SIS' },
  { label: 'Attendance Today', value: '—', dataSource: 'SIS' },
  { label: 'Staff on Duty', value: '—', dataSource: 'HRIS' },
  { label: 'Open Slots', value: '—', dataSource: 'SIS' }
];

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

      <KpiStrip cards={EXTENDED_CARE_KPI} />

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
