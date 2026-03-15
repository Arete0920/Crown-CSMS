import { Alert, Box, Button, CircularProgress, Paper, Stack, Typography } from '@mui/material';

export default function PageState({
  loading = false,
  error = null,
  empty = false,
  emptyTitle = 'No data found',
  emptyMessage = 'There is nothing to show here yet.',
  onRetry,
  children,
}) {
  if (loading) {
    return (
      <Paper elevation={1} sx={{ p: 4, borderRadius: 3 }}>
        <Stack spacing={2} alignItems="center">
          <CircularProgress />
          <Typography variant="body1">Loading data...</Typography>
        </Stack>
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper elevation={1} sx={{ p: 4, borderRadius: 3 }}>
        <Stack spacing={2}>
          <Alert severity="error">
            {typeof error === 'string' ? error : error?.message || 'Something went wrong.'}
          </Alert>
          {typeof onRetry === 'function' && (
            <Box>
              <Button variant="contained" onClick={onRetry}>
                Retry
              </Button>
            </Box>
          )}
        </Stack>
      </Paper>
    );
  }

  if (empty) {
    return (
      <Paper elevation={1} sx={{ p: 4, borderRadius: 3 }}>
        <Stack spacing={1}>
          <Typography variant="h6" fontWeight={700}>
            {emptyTitle}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {emptyMessage}
          </Typography>
        </Stack>
      </Paper>
    );
  }

  return <>{children}</>;
}
