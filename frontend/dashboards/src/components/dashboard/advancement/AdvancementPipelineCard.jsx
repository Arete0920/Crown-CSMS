import { Card, CardContent, Typography, Grid, Paper, Stack } from '@mui/material';

const items = [
  { label: 'New Donor Leads', value: '32' },
  { label: 'Qualified Conversations', value: '18' },
  { label: 'Major Gift Prospects', value: '9' },
  { label: 'Church Partnerships', value: '6' },
  { label: 'Volunteer Champions', value: '21' },
  { label: 'Event Sponsors', value: '11' },
];

export default function AdvancementPipelineCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Donor and Partner Pipeline
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
