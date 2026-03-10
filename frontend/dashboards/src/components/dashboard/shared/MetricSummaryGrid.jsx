import { Card, CardContent, Grid, Typography, Stack } from '@mui/material';

export default function MetricSummaryGrid({ metrics = [] }) {
  return (
    <Grid container spacing={3}>
      {metrics.map((metric) => (
        <Grid item xs={12} sm={6} md={3} key={metric.label}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Stack spacing={1}>
                <Typography variant="body2" color="text.secondary">
                  {metric.label}
                </Typography>
                <Typography variant="h5" fontWeight={700}>
                  {metric.value}
                </Typography>
                {metric.secondary ? (
                  <Typography variant="caption" color="text.secondary">
                    {metric.secondary}
                  </Typography>
                ) : null}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
}
