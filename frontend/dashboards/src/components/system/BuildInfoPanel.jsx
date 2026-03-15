import { Divider, Paper, Stack, Typography } from '@mui/material';
import { getBuildInfo } from '../../utils/buildInfo';

export default function BuildInfoPanel() {
  const info = getBuildInfo();

  return (
    <Paper elevation={1} sx={{ p: 3, borderRadius: 3 }}>
      <Stack spacing={1.25}>
        <Typography variant="h6" fontWeight={700}>
          Build and Runtime Truth
        </Typography>

        <Divider />

        <Typography variant="body2">
          <strong>Mode:</strong> {info.mode}
        </Typography>

        <Typography variant="body2">
          <strong>API Base URL:</strong> {info.apiBaseUrl}
        </Typography>

        <Typography variant="body2">
          <strong>Build SHA:</strong> {info.buildSha}
        </Typography>

        <Typography variant="body2">
          <strong>Build Tag:</strong> {info.buildTag}
        </Typography>

        <Typography variant="body2">
          <strong>Build Time:</strong> {info.buildTime}
        </Typography>
      </Stack>
    </Paper>
  );
}
