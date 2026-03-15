import { useEffect, useMemo, useState } from 'react';
import { Alert, Grid, Stack, Typography } from '@mui/material';
import PageHeader from '../components/dashboard/PageHeader';
import DemoReadinessCard from '../components/system/DemoReadinessCard';
import { DEMO_READINESS_CHECKS } from '../config/demoReadinessChecks';
import { getAdmissionsApplications } from '../api/admissions';
import { getInvoices } from '../api/finance';
import { getThreads } from '../api/communications';
import api from '../services/api';

function getStatus(count, warnIfLessThan) {
  if (count == null) return 'fail';
  if (count < warnIfLessThan) return 'warn';
  return 'pass';
}

export default function DemoReadinessPage() {
  const [state, setState] = useState({
    loading: true,
    error: null,
    admissions: null,
    finance: null,
    communications: null,
    healthOk: false,
  });

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        const [admissionsResult, financeResult, communicationsResult, healthResult] =
          await Promise.allSettled([
            getAdmissionsApplications(),
            getInvoices(),
            getThreads(),
            api.get('/health/'),
          ]);

        if (!mounted) return;

        setState({
          loading: false,
          error: null,
          admissions:
            admissionsResult.status === 'fulfilled'
              ? admissionsResult.value.length
              : null,
          finance:
            financeResult.status === 'fulfilled'
              ? financeResult.value.length
              : null,
          communications:
            communicationsResult.status === 'fulfilled'
              ? communicationsResult.value.length
              : null,
          healthOk: healthResult.status === 'fulfilled',
        });
      } catch (error) {
        if (!mounted) return;
        setState({
          loading: false,
          error,
          admissions: null,
          finance: null,
          communications: null,
          healthOk: false,
        });
      }
    }

    load();

    return () => {
      mounted = false;
    };
  }, []);

  const summary = useMemo(() => {
    return DEMO_READINESS_CHECKS.map((check) => {
      const count = state[check.key];
      return {
        ...check,
        count,
        status: getStatus(count, check.warnIfLessThan),
      };
    });
  }, [state]);

  return (
    <Stack spacing={3} sx={{ p: 3 }}>
      <PageHeader
        title="Demo Readiness"
        subtitle="Truth panel for investor demo data coverage"
      />

      {state.error ? (
        <Alert severity="error">
          {state.error?.message || 'Failed to load demo readiness.'}
        </Alert>
      ) : null}

      {!state.healthOk ? (
        <Alert severity="warning">
          Backend health is not confirmed. Do not start the demo until this is green.
        </Alert>
      ) : null}

      <Grid container spacing={2}>
        {summary.map((item) => (
          <Grid item xs={12} md={4} key={item.key}>
            <DemoReadinessCard
              label={item.label}
              count={item.count ?? 0}
              status={item.status}
              helperText={
                item.status === 'warn'
                  ? `Low seeded data. Recommended minimum: ${item.warnIfLessThan}.`
                  : item.status === 'fail'
                    ? 'Dataset unavailable.'
                    : 'Dataset is adequate for demo use.'
              }
            />
          </Grid>
        ))}
      </Grid>

      <Typography variant="body2" color="text.secondary">
        This page reports actual current data counts. It does not fabricate demo content.
      </Typography>
    </Stack>
  );
}
