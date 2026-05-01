import { Grid, Stack, Typography } from '@mui/material';
import IntegrationsAutomationSnapshotCard from '../components/dashboard/integrationsautomation/IntegrationsAutomationSnapshotCard';
import IntegrationsAutomationAlertsPanel from '../components/dashboard/integrationsautomation/IntegrationsAutomationAlertsPanel';
import IntegrationsAutomationQueueCard from '../components/dashboard/integrationsautomation/IntegrationsAutomationQueueCard';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

const INTEGRATIONS_KPI = [
  { label: 'Active Integrations', value: '—', dataSource: 'SIS' },
  { label: 'Failed Syncs', value: '—', dataSource: 'SIS' },
  { label: 'Pending Queued', value: '—', dataSource: 'SIS' },
  { label: 'Last Run', value: '—', dataSource: 'SIS' }
];

export default function IntegrationsAutomationDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Integrations / Automation Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Connector health, automation backlog, retry pressure, and sync risk across the platform.
        </Typography>
      </div>

      <KpiStrip cards={INTEGRATIONS_KPI} />

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <IntegrationsAutomationSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <IntegrationsAutomationAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <IntegrationsAutomationQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
