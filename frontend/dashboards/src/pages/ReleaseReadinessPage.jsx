import { useEffect, useMemo, useState } from 'react';
import { Alert, Chip, Grid, Paper, Stack, Typography } from '@mui/material';
import { releaseChecklist } from '../config/releaseChecklist';
import { evaluateStaticReleaseChecks } from '../utils/releaseChecks';
import { getBuildInfo } from '../utils/buildInfo';
import api from '../services/api';
import PageHeader from '../components/dashboard/PageHeader';

export default function ReleaseReadinessPage() {
  const [healthOk, setHealthOk] = useState(false);
  const [healthError, setHealthError] = useState(null);

  useEffect(() => {
    let mounted = true;

    async function loadHealth() {
      try {
        await api.get('/api/health/');
        if (mounted) setHealthOk(true);
      } catch (err) {
        if (mounted) {
          setHealthOk(false);
          setHealthError(err);
        }
      }
    }

    loadHealth();

    return () => {
      mounted = false;
    };
  }, []);

  const build = getBuildInfo();
  const staticChecks = useMemo(() => evaluateStaticReleaseChecks(), []);

  const results = useMemo(
    () => ({
      ...staticChecks,
      'health-ok': healthOk,
    }),
    [staticChecks, healthOk],
  );

  const passedCount = Object.values(results).filter(Boolean).length;
  const totalCount = releaseChecklist.length;

  return (
    <Stack spacing={3} sx={{ p: 3 }}>
      <PageHeader
        title="Release Readiness"
        subtitle="Runtime proof panel for release gate visibility"
      />

      <Paper elevation={1} sx={{ p: 3, borderRadius: 3 }}>
        <Stack spacing={1.5}>
          <Typography variant="h6" fontWeight={700}>
            Overall Status
          </Typography>
          <Typography variant="body1">
            {passedCount} / {totalCount} checks passing
          </Typography>
          <Chip
            label={passedCount === totalCount ? 'PASS' : 'FAIL'}
            color={passedCount === totalCount ? 'success' : 'error'}
            sx={{ width: 100 }}
          />
        </Stack>
      </Paper>

      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Paper elevation={1} sx={{ p: 3, borderRadius: 3 }}>
            <Stack spacing={1.25}>
              <Typography variant="h6" fontWeight={700}>
                Build Info
              </Typography>
              <Typography variant="body2">
                <strong>Build SHA:</strong> {build.buildSha}
              </Typography>
              <Typography variant="body2">
                <strong>Build Tag:</strong> {build.buildTag}
              </Typography>
              <Typography variant="body2">
                <strong>Build Time:</strong> {build.buildTime}
              </Typography>
              <Typography variant="body2">
                <strong>API Base URL:</strong> {build.apiBaseUrl}
              </Typography>
            </Stack>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper elevation={1} sx={{ p: 3, borderRadius: 3 }}>
            <Stack spacing={1.25}>
              <Typography variant="h6" fontWeight={700}>
                Health Check
              </Typography>
              {healthError ? (
                <Alert severity="error">
                  {healthError.message || 'Health endpoint failed.'}
                </Alert>
              ) : (
                <Chip
                  label={healthOk ? 'Backend reachable' : 'Checking...'}
                  color={healthOk ? 'success' : 'default'}
                  sx={{ width: 180 }}
                />
              )}
            </Stack>
          </Paper>
        </Grid>
      </Grid>

      <Paper elevation={1} sx={{ p: 3, borderRadius: 3 }}>
        <Stack spacing={2}>
          <Typography variant="h6" fontWeight={700}>
            Gate Checklist
          </Typography>

          {releaseChecklist.map((item) => {
            const pass = Boolean(results[item.key]);

            return (
              <Paper
                key={item.key}
                variant="outlined"
                sx={{ p: 2, borderRadius: 2 }}
              >
                <Stack
                  direction="row"
                  justifyContent="space-between"
                  alignItems="center"
                  spacing={2}
                >
                  <Typography variant="body1">{item.label}</Typography>
                  <Chip
                    label={pass ? 'PASS' : 'FAIL'}
                    color={pass ? 'success' : 'error'}
                  />
                </Stack>
              </Paper>
            );
          })}
        </Stack>
      </Paper>
    </Stack>
  );
}
