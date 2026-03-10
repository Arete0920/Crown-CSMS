import React from 'react';
import { Alert, Chip, Stack, Typography } from '@mui/material';
import { getCertificationStatusColor } from '../../../config/dashboardCertificationRegistry';

function getSourceColor(source) {
  switch (source) {
    case 'live':
      return 'success';
    case 'fallback':
      return 'warning';
    default:
      return 'default';
  }
}

export default function DataStatusBanner({
  certification,
  source,
  endpoint,
  lastLoadedAt,
  error,
}) {
  const certificationStatus = certification?.status || 'scaffold';
  const owner = certification?.owner || 'Unknown';

  return (
    <Alert severity={source === 'live' ? 'success' : source === 'fallback' ? 'warning' : 'info'}>
      <Stack spacing={1}>
        <Stack direction="row" spacing={1} flexWrap="wrap">
          <Chip
            size="small"
            label={`Status: ${certificationStatus}`}
            color={getCertificationStatusColor(certificationStatus)}
          />
          <Chip
            size="small"
            label={`Source: ${source || 'none'}`}
            color={getSourceColor(source)}
          />
          <Chip size="small" label={`Owner: ${owner}`} />
        </Stack>

        {endpoint ? (
          <Typography variant="caption" color="text.secondary">
            Endpoint: {endpoint}
          </Typography>
        ) : null}

        {lastLoadedAt ? (
          <Typography variant="caption" color="text.secondary">
            Last loaded: {new Date(lastLoadedAt).toLocaleString()}
          </Typography>
        ) : null}

        {error ? (
          <Typography variant="caption" color="text.secondary">
            Last fetch error: {error.message}
          </Typography>
        ) : null}
      </Stack>
    </Alert>
  );
}
