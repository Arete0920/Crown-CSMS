import { Grid, Stack, Typography } from '@mui/material';
import BoardSnapshotCard from '../components/dashboard/board/BoardSnapshotCard';
import BoardKpiPanel from '../components/dashboard/board/BoardKpiPanel';
import BoardRiskPanel from '../components/dashboard/board/BoardRiskPanel';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

const SCHOOL_BOARD_KPI = [
  { label: 'Enrollment', value: '—', dataSource: 'SIS' },
  { label: 'Revenue YTD', value: '—', dataSource: 'Finance' },
  { label: 'Retention Rate', value: '—', dataSource: 'SIS' },
  { label: 'Strategic Items', value: '—', dataSource: 'Board' }
];

export default function SchoolBoardDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          School Board Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Governance-safe view of mission health, sustainability, retention, and strategic risk.
        </Typography>
      </div>

      <KpiStrip cards={SCHOOL_BOARD_KPI} />

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <BoardSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <BoardRiskPanel />
        </Grid>
        <Grid item xs={12}>
          <BoardKpiPanel />
        </Grid>
      </Grid>
    </Stack>
  );
}
