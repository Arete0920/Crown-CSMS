import React from 'react';
import { Box, Button, Paper, Stack, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { PATHS } from '../routes/paths';

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <Box sx={{ p: 4 }}>
      <Paper elevation={2} sx={{ p: 4, borderRadius: 3, maxWidth: 760, mx: 'auto' }}>
        <Stack spacing={2}>
          <Typography variant="h4" fontWeight={700}>
            Page not found
          </Typography>
          <Typography variant="body1">
            The requested Crown route does not exist.
          </Typography>
          <Box>
            <Button variant="contained" onClick={() => navigate(PATHS.HOME)}>
              Back to Dashboard
            </Button>
          </Box>
        </Stack>
      </Paper>
    </Box>
  );
}
