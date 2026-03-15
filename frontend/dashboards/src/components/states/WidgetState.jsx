import { Alert, Box, CircularProgress, Paper, Stack, Typography } from '@mui/material';

export default function WidgetState({
  title,
  loading = false,
  error = null,
  empty = false,
  emptyMessage = 'No data available.',
  children,
}) {
  return (
    <Paper elevation={1} sx={{ p: 2.5, borderRadius: 3, minHeight: 180 }}>
      <Stack spacing={2}>
        {title ? (
          <Typography variant="h6" fontWeight={700}>
            {title}
          </Typography>
        ) : null}

        {loading ? (
          <Stack spacing={1} alignItems="center" justifyContent="center" sx={{ minHeight: 90 }}>
            <CircularProgress size={28} />
            <Typography variant="body2">Loading...</Typography>
          </Stack>
        ) : error ? (
          <Alert severity="error">
            {typeof error === 'string' ? error : error?.message || 'Widget failed to load.'}
          </Alert>
        ) : empty ? (
          <Box>
            <Typography variant="body2" color="text.secondary">
              {emptyMessage}
            </Typography>
          </Box>
        ) : (
          children
        )}
      </Stack>
    </Paper>
  );
}
