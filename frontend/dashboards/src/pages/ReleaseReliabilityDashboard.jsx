import { Grid, Stack, Typography } from '@mui/material';
import useDashboardData from '../hooks/useDashboardData';
import DataStatusBanner from '../components/dashboard/shared/DataStatusBanner';
import DashboardLoadingState from '../components/dashboard/shared/DashboardLoadingState';
import DashboardErrorState from '../components/dashboard/shared/DashboardErrorState';
import MetricSummaryGrid from '../components/dashboard/shared/MetricSummaryGrid';
import AlertListCard from '../components/dashboard/shared/AlertListCard';
import TextListCard from '../components/dashboard/shared/TextListCard';

export default function ReleaseReliabilityDashboard() {
  const {
    data,
    error,
    loading,
    source,
    lastLoadedAt,
    certification,
    config,
  } = useDashboardData('release-reliability');

  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Release Reliability Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Live release reliability view with scaffold fallback until full deployment telemetry is wired.
        </Typography>
      </div>

      <DataStatusBanner
        certification={certification}
        source={source}
        endpoint={config?.endpoint}
        lastLoadedAt={lastLoadedAt}
        error={error}
      />

      {loading ? <DashboardLoadingState title="Loading release reliability metrics..." /> : null}
      {!loading && error && source === 'none' ? <DashboardErrorState error={error} /> : null}

      {!loading && data ? (
        <>
          <MetricSummaryGrid metrics={data.metrics || []} />

          <Grid container spacing={3}>
            <Grid item xs={12} md={7}>
              <AlertListCard title="Release Reliability Alerts" items={data.alerts || []} />
            </Grid>
            <Grid item xs={12} md={5}>
              <TextListCard title="Release Queue" items={data.queue || []} />
            </Grid>
          </Grid>
        </>
      ) : null}
    </Stack>
  );
}
