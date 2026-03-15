import React from 'react';
import { Card, CardContent, Typography, Stack, Divider } from '@mui/material';

const metrics = [
  { label: 'Active Volunteers', value: '142' },
  { label: 'Open Sign-Up Gaps', value: '16' },
  { label: 'Background Checks Pending', value: '7' },
  { label: 'Hours Logged This Month', value: '418' },
  { label: 'Upcoming Events Requiring Coverage', value: '5' },
];

export default function VolunteerSnapshotCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Volunteer Snapshot
        </Typography>

        <Stack spacing={1.5}>
          {metrics.map((item, index) => (
            <React.Fragment key={item.label}>
              <Stack direction="row" justifyContent="space-between">
                <Typography variant="body2" color="text.secondary">
                  {item.label}
                </Typography>
                <Typography variant="subtitle1" fontWeight={700}>
                  {item.value}
                </Typography>
              </Stack>
              {index < metrics.length - 1 && <Divider />}
            </React.Fragment>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
}
