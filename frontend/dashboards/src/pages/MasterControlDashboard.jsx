import { Grid, Stack, Typography } from '@mui/material';
import MasterControlSnapshotCard from '../components/dashboard/mastercontrol/MasterControlSnapshotCard';
import PortfolioHealthPanel from '../components/dashboard/mastercontrol/PortfolioHealthPanel';
import MasterControlAlertsPanel from '../components/dashboard/mastercontrol/MasterControlAlertsPanel';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

const MASTER_CONTROL_KPI = [
  { label: 'Schools Active', value: '—', dataSource: 'SIS' },
  { label: 'Critical Alerts', value: '—', dataSource: 'SIS' },
  { label: 'Platform Uptime', value: '—', dataSource: 'Monitor' },
  { label: 'Revenue Today', value: '—', dataSource: 'Finance' }
];

export default function MasterControlDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Master Control Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Multi-school portfolio oversight, platform operations, payment flow, and tenant health.
        </Typography>
      </div>

      <KpiStrip cards={MASTER_CONTROL_KPI} />

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <MasterControlSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <MasterControlAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <PortfolioHealthPanel />
        </Grid>
      </Grid>
    </Stack>
  );
}
