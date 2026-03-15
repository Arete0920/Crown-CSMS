import { useEffect, useState } from 'react';
import { Alert, Box, Grid, Paper, Stack, Typography } from '@mui/material';
import BuildInfoPanel from '../components/system/BuildInfoPanel';
import { authenticatedFetch } from '../utils/authClient';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export default function SystemStatusPage() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        const response = await authenticatedFetch(`${API_BASE}/api/health/`);

        if (!response.ok) {
          throw new Error(`Health probe failed (${response.status})`);
        }

        const payload = await response.json();

        if (mounted) {
          setHealth(payload);
        }
      } catch (err) {
        if (mounted) {
          setError(err);
        }
      }
    }

    load();

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <Box sx={{ p: 3 }}>
      <Stack spacing={3}>
        <Typography variant="h4" fontWeight={700}>
          System Status
        </Typography>

        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <BuildInfoPanel />
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper elevation={1} sx={{ p: 3, borderRadius: 3 }}>
              <Stack spacing={1.25}>
                <Typography variant="h6" fontWeight={700}>
                  API Health
                </Typography>

                {error ? (
                  <Alert severity="error">
                    {error?.message || 'Failed to load backend health.'}
                  </Alert>
                ) : health ? (
                  <>
                    <Typography variant="body2">
                      <strong>Status:</strong> {health.status || 'unknown'}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Build SHA:</strong> {health.build_sha || 'missing'}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Deploy Tag:</strong> {health.deploy_tag || health.prod_deploy_tag || 'missing'}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Environment:</strong> {health.environment || 'unknown'}
                    </Typography>
                  </>
                ) : (
                  <Typography variant="body2">Loading backend health...</Typography>
                )}
              </Stack>
            </Paper>
          </Grid>
        </Grid>
      </Stack>
    </Box>
  );
}
