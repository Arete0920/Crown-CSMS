import { Grid, Stack, Typography } from '@mui/material';
import RevenueOpsSnapshotCard from '../components/dashboard/revenueops/RevenueOpsSnapshotCard';
import RevenueOpsAlertsPanel from '../components/dashboard/revenueops/RevenueOpsAlertsPanel';
import RevenueOpsQueueCard from '../components/dashboard/revenueops/RevenueOpsQueueCard';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

const REVENUE_OPS_KPI = [
  { label: 'Revenue MTD', value: '—', dataSource: 'Finance' },
  { label: 'Invoices Sent', value: '—', dataSource: 'Finance' },
  { label: 'Collections Rate', value: '—', dataSource: 'Finance' },
  { label: 'Pending', value: '—', dataSource: 'Finance' }
];

export default function RevenueOperationsDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Revenue Operations Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Crown-side invoicing, renewals, collections exceptions, implementation fees, and account risk.
        </Typography>
      </div>

      <KpiStrip cards={REVENUE_OPS_KPI} />

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <RevenueOpsSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <RevenueOpsAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <RevenueOpsQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
