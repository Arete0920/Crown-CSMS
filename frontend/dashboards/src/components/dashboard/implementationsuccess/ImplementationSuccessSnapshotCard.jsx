import React from 'react';
import { Card, CardContent, Typography, Stack, Divider } from '@mui/material';

const metrics = [
  { label: 'Active Implementations', value: '12' },
  { label: 'Schools Launching This Month', value: '4' },
  { label: 'Tasks Behind Schedule', value: '9' },
  { label: 'Training Sessions Scheduled', value: '18' },
  { label: 'Go-Live Risks Open', value: '5' },
];

export default function ImplementationSuccessSnapshotCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Implementation Snapshot
        </Typography>

        <Stack spacing={1.5}>
          {metrics.map((item, index) => (
            <React.Fragment key={item.label}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
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
