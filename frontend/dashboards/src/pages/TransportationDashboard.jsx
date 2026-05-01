import { Grid, Stack, Typography } from '@mui/material';
import TransportationSnapshotCard from '../components/dashboard/transportation/TransportationSnapshotCard';
import TransportationAlertsPanel from '../components/dashboard/transportation/TransportationAlertsPanel';
import TransportationQueueCard from '../components/dashboard/transportation/TransportationQueueCard';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

const TRANSPORTATION_KPI = [
  { label: 'Routes Active', value: '—', dataSource: 'Transport' },
  { label: 'Riders Today', value: '—', dataSource: 'Transport' },
  { label: 'Incidents', value: '—', dataSource: 'Transport' },
  { label: 'Vehicles', value: '—', dataSource: 'Transport' }
];

export default function TransportationDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Transportation Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Routes, vehicle readiness, family stop changes, and transport coverage status.
        </Typography>
      </div>

      <KpiStrip cards={TRANSPORTATION_KPI} />

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <TransportationSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <TransportationAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <TransportationQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
