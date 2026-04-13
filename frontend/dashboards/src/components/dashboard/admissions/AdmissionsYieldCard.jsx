import { Card, CardContent, Typography, Grid, Paper, Stack } from '@mui/material';

const items = [
  { label: 'Inquiry -> Start', value: '65%' },
  { label: 'Start -> Complete', value: '74%' },
  { label: 'Complete -> Accept', value: '61%' },
  { label: 'Accept -> Deposit', value: '57%' },
  { label: 'Aid Applicants', value: '43%' },
  { label: 'Mission-Fit Strong', value: '81%' },
];

export default function AdmissionsYieldCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Yield and Mission Fit
        </Typography>

        <Grid container spacing={2}>
          {items.map((item) => (
            <Grid item xs={12} sm={6} md={4} key={item.label}>
              <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
                <Stack spacing={0.5}>
                  <Typography variant="body2" color="text.secondary">
                    {item.label}
                  </Typography>
                  <Typography variant="subtitle1" fontWeight={700}>
                    {item.value}
                  </Typography>
                </Stack>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
}
