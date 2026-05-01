import { Grid, Stack, Typography } from '@mui/material';
import SafetySecuritySnapshotCard from '../components/dashboard/safetysecurity/SafetySecuritySnapshotCard';
import SafetySecurityAlertsPanel from '../components/dashboard/safetysecurity/SafetySecurityAlertsPanel';
import SafetySecurityQueueCard from '../components/dashboard/safetysecurity/SafetySecurityQueueCard';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

const SAFETY_SECURITY_KPI = [
  { label: 'Incidents Today', value: '—', dataSource: 'Safety' },
  { label: 'Open Drills', value: '—', dataSource: 'Safety' },
  { label: 'Badges Active', value: '—', dataSource: 'Safety' },
  { label: 'Alerts', value: '—', dataSource: 'Safety' }
];

export default function SafetySecurityDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Safety / Security Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Incidents, visitors, drills, follow-up tasks, and campus readiness.
        </Typography>
      </div>

      <KpiStrip cards={SAFETY_SECURITY_KPI} />

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <SafetySecuritySnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <SafetySecurityAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <SafetySecurityQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
