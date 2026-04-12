import { Paper, Stack, Typography } from '@mui/material';

export default function MetricCard({ label, value, helperText, footer }) {
  return (
    <Paper elevation={1} sx={{ p: 2.5, borderRadius: 3, minHeight: 150 }}>
      <Stack spacing={1.5}>
        <Typography variant="body2" color="text.secondary">
          {label}
        </Typography>

        <Typography variant="h3" fontWeight={700}>
          {value}
        </Typography>

        {helperText ? (
          <Typography variant="body2" color="text.secondary">
            {helperText}
          </Typography>
        ) : null}

        {footer ? <div>{footer}</div> : null}
      </Stack>
    </Paper>
  );
}
