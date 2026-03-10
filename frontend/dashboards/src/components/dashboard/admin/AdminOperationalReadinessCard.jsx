import React from 'react';
import { Card, CardContent, Typography, Grid, Paper, Stack } from '@mui/material';

const blocks = [
  { label: 'Admissions', value: 'Stable' },
  { label: 'Billing', value: 'Watch' },
  { label: 'Attendance', value: 'Good' },
  { label: 'Gradebook', value: 'Watch' },
  { label: 'Communications', value: 'Good' },
  { label: 'Student Care', value: 'Action' },
];

export default function AdminOperationalReadinessCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Operational Readiness
        </Typography>

        <Grid container spacing={2}>
          {blocks.map((item) => (
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
