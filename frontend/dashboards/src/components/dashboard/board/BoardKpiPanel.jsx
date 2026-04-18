import {
  Card,
  CardContent,
  Typography,
  Grid,
  Paper,
  LinearProgress,
  Stack,
} from '@mui/material';

const items = [
  { label: 'Mission Fit', value: 88 },
  { label: 'Family Satisfaction', value: 84 },
  { label: 'Faculty Stability', value: 79 },
  { label: 'Enrollment Health', value: 86 },
  { label: 'Financial Sustainability', value: 81 },
  { label: 'Spiritual Formation Indicators', value: 83 },
];

export default function BoardKpiPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Strategic KPIs
        </Typography>

        <Grid container spacing={2}>
          {items.map((item) => (
            <Grid item xs={12} sm={6} key={item.label}>
              <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
                <Stack spacing={1}>
                  <Typography variant="body2" color="text.secondary">
                    {item.label}
                  </Typography>
                  <Typography variant="subtitle1" fontWeight={700}>
                    {item.value} / 100
                  </Typography>
                  <LinearProgress variant="determinate" value={item.value} />
                </Stack>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
}
