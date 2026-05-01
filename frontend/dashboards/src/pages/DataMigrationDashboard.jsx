import { Grid, Stack, Typography } from '@mui/material';
import DataMigrationSnapshotCard from '../components/dashboard/datamigration/DataMigrationSnapshotCard';
import DataMigrationAlertsPanel from '../components/dashboard/datamigration/DataMigrationAlertsPanel';
import DataMigrationQueueCard from '../components/dashboard/datamigration/DataMigrationQueueCard';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

const DATA_MIGRATION_KPI = [
  { label: 'Records Migrated', value: '—', dataSource: 'SIS' },
  { label: 'Validation Errors', value: '—', dataSource: 'SIS' },
  { label: 'Pending', value: '—', dataSource: 'SIS' },
  { label: 'Validated', value: '—', dataSource: 'SIS' }
];

export default function DataMigrationDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Data Migration Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Import quality, mapping validation, cutover readiness, and migration execution risk.
        </Typography>
      </div>

      <KpiStrip cards={DATA_MIGRATION_KPI} />

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <DataMigrationSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <DataMigrationAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <DataMigrationQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
