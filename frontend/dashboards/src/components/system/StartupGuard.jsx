import { Alert, Box, Paper, Stack, Typography } from '@mui/material';
import { getBuildInfo } from '../../utils/buildInfo';

export default function StartupGuard({ children }) {
  const enforceStartupGuard = import.meta.env.VITE_ENFORCE_STARTUP_GUARD === '1';
  if (!enforceStartupGuard) {
    return children;
  }

  const build = getBuildInfo();

  const missing = [];

  if (!build.apiBaseUrl || build.apiBaseUrl === 'missing') {
    missing.push('VITE_API_BASE_URL');
  }

  if (!build.buildSha || build.buildSha === 'missing') {
    missing.push('VITE_BUILD_SHA');
  }

  if (missing.length > 0) {
    return (
      <Box sx={{ p: 4 }}>
        <Paper elevation={2} sx={{ p: 4, borderRadius: 3, maxWidth: 760, mx: 'auto' }}>
          <Stack spacing={2}>
            <Typography variant="h4" fontWeight={700}>
              Startup configuration error
            </Typography>
            <Alert severity="error">
              Required runtime variables are missing: {missing.join(', ')}
            </Alert>
            <Typography variant="body2" color="text.secondary">
              Fix the frontend environment injection before using this build.
            </Typography>
          </Stack>
        </Paper>
      </Box>
    );
  }

  return children;
}
