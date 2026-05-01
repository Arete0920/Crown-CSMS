import { Grid, Stack, Typography } from '@mui/material';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';
import useDashboardData from '../hooks/useDashboardData';
import DataStatusBanner from '../components/dashboard/shared/DataStatusBanner';
import DashboardLoadingState from '../components/dashboard/shared/DashboardLoadingState';
import DashboardErrorState from '../components/dashboard/shared/DashboardErrorState';
import MetricSummaryGrid from '../components/dashboard/shared/MetricSummaryGrid';
import AlertListCard from '../components/dashboard/shared/AlertListCard';
import TextListCard from '../components/dashboard/shared/TextListCard';
import PageState from '../components/states/PageState.jsx';

const ATTENDANCE_KPI = [
  { label: 'Daily Rate',     value: '—', trend: null, trendUp: null,
    definition: 'School-wide attendance rate for the current school day.',
    dataSource: 'Attendance API', dataHref: '/attendance' },
  { label: 'Absent Today',   value: '—', trend: null, trendUp: null,
    definition: 'Total students marked absent for the current school day.',
    dataSource: 'Attendance API', dataHref: '/attendance' },
  { label: 'Tardy Today',    value: '—', trend: null, trendUp: null,
    definition: 'Total students marked tardy for the current school day.',
    dataSource: 'Attendance API', dataHref: '/attendance' },
  { label: 'Chronic Absent', value: '—', trend: null, trendUp: null,
    definition: 'Students with 10% or more absences in the current term.',
    dataSource: 'Attendance API', dataHref: '/attendance' },
];

export default function AttendanceDashboard() {
  const {
    data,
    error,
    loading,
    source,
    lastLoadedAt,
    certification,
    config,
  } = useDashboardData('attendance');

  return (
    <Stack spacing={3}>
      <div>
        <Typography component="h1" variant="h4" fontWeight={700}>
          Attendance Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Live attendance visibility with scaffold fallback until full endpoint certification is complete.
        </Typography>
      </div>

      <KpiStrip cards={ATTENDANCE_KPI} />

      <DataStatusBanner
        certification={certification}
        source={source}
        endpoint={config?.endpoint}
        lastLoadedAt={lastLoadedAt}
        error={error}
      />

      <PageState
        loading={loading}
        error={source === 'none' ? error : null}
        empty={!loading && !error && (!data || (data.metrics || []).length === 0)}
        emptyTitle="No attendance metrics yet"
        emptyMessage="Attendance metrics appear after your first attendance sync."
      >
        {loading ? <DashboardLoadingState title="Loading attendance metrics..." /> : null}
        {!loading && error && source === 'none' ? <DashboardErrorState error={error} /> : null}

        {!loading && data ? (
          <>
            <MetricSummaryGrid metrics={data.metrics || []} />

            <Grid container spacing={3}>
              <Grid item xs={12} md={7}>
                <AlertListCard title="Attendance Alerts" items={data.alerts || []} />
              </Grid>
              <Grid item xs={12} md={5}>
                <TextListCard title="Attendance Queue" items={data.queue || []} />
              </Grid>
            </Grid>
          </>
        ) : null}
      </PageState>
    </Stack>
  );
}
