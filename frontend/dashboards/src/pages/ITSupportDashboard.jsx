import { Grid, Stack, Typography } from '@mui/material';
import ITSupportSnapshotCard from '../components/dashboard/itsupport/ITSupportSnapshotCard';
import ITSupportAlertsPanel from '../components/dashboard/itsupport/ITSupportAlertsPanel';
import ITSupportQueueCard from '../components/dashboard/itsupport/ITSupportQueueCard';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

const IT_SUPPORT_KPI = [
  { label: 'Open Tickets', value: '—', dataSource: 'Support' },
  { label: 'Resolved Today', value: '—', dataSource: 'Support' },
  { label: 'SLA Breaches', value: '—', dataSource: 'Support' },
  { label: 'Pending Review', value: '—', dataSource: 'Support' }
];

export default function ITSupportDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          IT Support Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Ticket flow, account provisioning, device readiness, outages, and support backlog.
        </Typography>
      </div>

      <KpiStrip cards={IT_SUPPORT_KPI} />

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <ITSupportSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <ITSupportAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <ITSupportQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
