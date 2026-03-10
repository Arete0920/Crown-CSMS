import React from 'react';
import { Grid, Stack, Typography } from '@mui/material';
import useDashboardData from '../hooks/useDashboardData';
import DataStatusBanner from '../components/dashboard/shared/DataStatusBanner';
import DashboardLoadingState from '../components/dashboard/shared/DashboardLoadingState';
import DashboardErrorState from '../components/dashboard/shared/DashboardErrorState';
import MetricSummaryGrid from '../components/dashboard/shared/MetricSummaryGrid';
import AlertListCard from '../components/dashboard/shared/AlertListCard';
import TextListCard from '../components/dashboard/shared/TextListCard';

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
        <Typography variant="h4" fontWeight={700}>
          Attendance Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Live attendance visibility with scaffold fallback until full endpoint certification is complete.
        </Typography>
      </div>

      <DataStatusBanner
        certification={certification}
        source={source}
        endpoint={config?.endpoint}
        lastLoadedAt={lastLoadedAt}
        error={error}
      />

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
    </Stack>
  );
}
