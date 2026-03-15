import React from 'react';
import { Card, CardContent, Typography, Stack, Divider } from '@mui/material';

const metrics = [
  { label: 'Service Hours Logged YTD', value: '5,284' },
  { label: 'Students Below Target', value: '36' },
  { label: 'Portrait Reflections Submitted', value: '412' },
  { label: 'Mentor Reviews Pending', value: '18' },
  { label: 'Approved Service Partners', value: '22' },
];

export default function PortraitServiceSnapshotCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Portrait / Service Snapshot
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
