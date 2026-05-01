import { Grid, Stack, Typography } from '@mui/material';
import HealthOfficeSnapshotCard from '../components/dashboard/healthoffice/HealthOfficeSnapshotCard';
import HealthOfficeAlertsPanel from '../components/dashboard/healthoffice/HealthOfficeAlertsPanel';
import HealthOfficeQueueCard from '../components/dashboard/healthoffice/HealthOfficeQueueCard';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

const HEALTH_OFFICE_KPI = [
  { label: 'Visits Today', value: '—', dataSource: 'Health' },
  { label: 'Medications Due', value: '—', dataSource: 'Health' },
  { label: 'Immunization Alerts', value: '—', dataSource: 'Health' },
  { label: 'Referrals Pending', value: '—', dataSource: 'Health' }
];

export default function HealthOfficeDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Health Office Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Nurse visits, medications, medical document follow-up, and care plan readiness.
        </Typography>
      </div>

      <KpiStrip cards={HEALTH_OFFICE_KPI} />

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <HealthOfficeSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <HealthOfficeAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <HealthOfficeQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
