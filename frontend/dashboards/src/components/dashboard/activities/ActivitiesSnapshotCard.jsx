import React from 'react';
import { Card, CardContent, Typography, Stack, Divider } from '@mui/material';

const metrics = [
  { label: 'Active Teams / Clubs', value: '18' },
  { label: 'Eligibility Flags', value: '6' },
  { label: 'Events This Week', value: '11' },
  { label: 'Volunteer Gaps', value: '3' },
];

export default function ActivitiesSnapshotCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Activities Snapshot
        </Typography>

        <Stack spacing={1.5}>
          {metrics.map((item, idx) => (
            <React.Fragment key={item.label}>
              <Stack direction="row" justifyContent="space-between">
                <Typography variant="body2" color="text.secondary">
                  {item.label}
                </Typography>
                <Typography variant="subtitle1" fontWeight={700}>
                  {item.value}
                </Typography>
              </Stack>
              {idx < metrics.length - 1 && <Divider />}
            </React.Fragment>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
}
