import { Grid, Stack, Typography } from '@mui/material';
import AdvancementOpsSnapshotCard from '../components/dashboard/advancementops/AdvancementOpsSnapshotCard';
import AdvancementOpsAlertsPanel from '../components/dashboard/advancementops/AdvancementOpsAlertsPanel';
import AdvancementOpsQueueCard from '../components/dashboard/advancementops/AdvancementOpsQueueCard';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

const ADVANCEMENT_OPS_KPI = [
  { label: 'Donors Active', value: '—', dataSource: 'CRM' },
  { label: 'Proposals Open', value: '—', dataSource: 'CRM' },
  { label: 'Pledges YTD', value: '—', dataSource: 'Finance' },
  { label: 'Events Scheduled', value: '—', dataSource: 'SIS' }
];

export default function AdvancementOperationsDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Advancement Operations Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Donor workflow, stewardship execution, proposal pacing, church partner follow-up, and office readiness.
        </Typography>
      </div>

      <KpiStrip cards={ADVANCEMENT_OPS_KPI} />

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <AdvancementOpsSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <AdvancementOpsAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <AdvancementOpsQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
