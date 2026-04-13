import { Card, CardContent, Typography, Grid, Paper, Stack } from '@mui/material';

const schools = [
  { name: 'Heritage Christian Academy', status: 'Healthy' },
  { name: 'Cornerstone Christian School', status: 'Watch' },
  { name: 'Covenant Prep', status: 'Healthy' },
  { name: 'Faith Academy', status: 'Action' },
  { name: 'Liberty Christian School', status: 'Healthy' },
  { name: 'New Hope Christian Academy', status: 'Watch' },
];

export default function PortfolioHealthPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Portfolio Health
        </Typography>

        <Grid container spacing={2}>
          {schools.map((school) => (
            <Grid item xs={12} sm={6} md={4} key={school.name}>
              <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
                <Stack spacing={0.5}>
                  <Typography variant="body2" color="text.secondary">
                    {school.name}
                  </Typography>
                  <Typography variant="subtitle1" fontWeight={700}>
                    {school.status}
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
