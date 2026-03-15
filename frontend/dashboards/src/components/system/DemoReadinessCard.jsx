import { Chip, Paper, Stack, Typography } from '@mui/material';

export default function DemoReadinessCard({
  label,
  count = 0,
  status = 'default',
  helperText = '',
}) {
  return (
    <Paper elevation={1} sx={{ p: 2.5, borderRadius: 3 }}>
      <Stack spacing={1.25}>
        <Typography variant="h6" fontWeight={700}>
          {label}
        </Typography>

        <Typography variant="h3" fontWeight={700}>
          {count}
        </Typography>

        <Chip
          label={status.toUpperCase()}
          color={
            status === 'pass'
              ? 'success'
              : status === 'warn'
                ? 'warning'
                : status === 'fail'
                  ? 'error'
                  : 'default'
          }
          sx={{ width: 90 }}
        />

        {helperText ? (
          <Typography variant="body2" color="text.secondary">
            {helperText}
          </Typography>
        ) : null}
      </Stack>
    </Paper>
  );
}
