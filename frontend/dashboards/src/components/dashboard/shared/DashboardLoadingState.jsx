import { Card, CardContent, CircularProgress, Stack, Typography } from '@mui/material';

export default function DashboardLoadingState({ title = 'Loading dashboard data...' }) {
  return (
    <Card>
      <CardContent>
        <Stack spacing={2} alignItems="center" justifyContent="center" sx={{ py: 4 }}>
          <CircularProgress size={28} />
          <Typography variant="body2" color="text.secondary">
            {title}
          </Typography>
        </Stack>
      </CardContent>
    </Card>
  );
}
