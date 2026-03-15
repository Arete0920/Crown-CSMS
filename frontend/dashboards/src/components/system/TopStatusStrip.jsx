import React from 'react';
import { Box, Chip, Stack } from '@mui/material';
import { getBuildInfo } from '../../utils/buildInfo';

function getRole() {
  try {
    const raw =
      window.localStorage.getItem('crown_user') ||
      window.sessionStorage.getItem('crown_user');

    if (!raw) return 'guest';

    const parsed = JSON.parse(raw);
    return parsed?.role || parsed?.roles?.[0] || 'guest';
  } catch {
    return 'guest';
  }
}

export default function TopStatusStrip() {
  const build = getBuildInfo();
  const role = getRole();

  return (
    <Box sx={{ px: 3, pt: 2 }}>
      <Stack direction="row" spacing={1} flexWrap="wrap">
        <Chip size="small" label={`Role: ${role}`} />
        <Chip size="small" label={`Mode: ${build.mode}`} />
        <Chip size="small" label={`Build: ${build.buildTag}`} />
      </Stack>
    </Box>
  );
}
