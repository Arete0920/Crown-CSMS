import { Grid, Stack, Typography } from '@mui/material';
import ChaplainSnapshotCard from '../components/dashboard/chaplain/ChaplainSnapshotCard';
import ChaplainAlertsPanel from '../components/dashboard/chaplain/ChaplainAlertsPanel';
import ChaplainQueueCard from '../components/dashboard/chaplain/ChaplainQueueCard';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

const CHAPLAIN_KPI = [
  { label: 'Chapel Attendance', value: '—', dataSource: 'SIS' },
  { label: 'Prayer Requests', value: '—', dataSource: 'SIS' },
  { label: 'Special Days', value: '—', dataSource: 'SIS' },
  { label: 'Volunteer Servers', value: '—', dataSource: 'SIS' }
];

export default function ChaplainSpiritualLifeDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Chaplain / Spiritual Life Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Prayer care, chapel rhythm, student follow-up, spiritual formation touchpoints, and pastoral workload.
        </Typography>
      </div>

      <KpiStrip cards={CHAPLAIN_KPI} />

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <ChaplainSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <ChaplainAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <ChaplainQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
