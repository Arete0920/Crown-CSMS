import { Grid, Stack } from '@mui/material';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import SchedulingSnapshotCard from '../components/dashboard/scheduling/SchedulingSnapshotCard.jsx';
import SchedulingConflictsPanel from '../components/dashboard/scheduling/SchedulingConflictsPanel.jsx';
import SchedulingWorkQueueCard from '../components/dashboard/scheduling/SchedulingWorkQueueCard.jsx';
import PageState from '../components/states/PageState.jsx';
import WidgetState from '../components/states/WidgetState.jsx';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

const SCHEDULING_KPI = [
  { label: 'Sections Scheduled', value: '—', dataSource: 'SIS' },
  { label: 'Conflicts', value: '—', dataSource: 'SIS' },
  { label: 'Substitutes Needed', value: '—', dataSource: 'HRIS' },
  { label: 'Open Periods', value: '—', dataSource: 'SIS' }
];

export default function SchedulingDashboard() {
  return (
    <CrownLayout title="Scheduling Dashboard" subtitle="Master schedule health, conflicts, room usage, and registrar workload">
      <KpiStrip cards={SCHEDULING_KPI} />
      <PageState>
        <Stack spacing={3}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <WidgetState>
                <SchedulingSnapshotCard />
              </WidgetState>
            </Grid>
            <Grid item xs={12} md={8}>
              <WidgetState>
                <SchedulingConflictsPanel />
              </WidgetState>
            </Grid>
            <Grid item xs={12}>
              <WidgetState>
                <SchedulingWorkQueueCard />
              </WidgetState>
            </Grid>
          </Grid>
        </Stack>
      <KpiStrip cards={SCHEDULING_KPI} />
      </PageState>
    </CrownLayout>
  );
}
