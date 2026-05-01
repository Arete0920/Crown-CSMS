import { Grid, Stack, Typography } from '@mui/material';
import CurriculumPDSnapshotCard from '../components/dashboard/curriculumpd/CurriculumPDSnapshotCard';
import CurriculumPDAlertsPanel from '../components/dashboard/curriculumpd/CurriculumPDAlertsPanel';
import CurriculumPDQueueCard from '../components/dashboard/curriculumpd/CurriculumPDQueueCard';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

const CURRICULUM_PD_KPI = [
  { label: 'PD Sessions', value: '—', dataSource: 'SIS' },
  { label: 'Teachers Enrolled', value: '—', dataSource: 'HRIS' },
  { label: 'Completion Rate', value: '—', dataSource: 'SIS' },
  { label: 'Upcoming Sessions', value: '—', dataSource: 'SIS' }
];

export default function CurriculumPDDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Curriculum / PD Hub Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Curriculum reviews, teacher professional development, resource support, and follow-up workload.
        </Typography>
      </div>

      <KpiStrip cards={CURRICULUM_PD_KPI} />

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <CurriculumPDSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <CurriculumPDAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <CurriculumPDQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
