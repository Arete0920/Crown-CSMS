import React from 'react';
import { Card, CardContent, Typography, Stack, Divider } from '@mui/material';

const metrics = [
  { label: 'Students Registered', value: '74' },
  { label: 'Checked In Today', value: '51' },
  { label: 'Late Pickups This Month', value: '6' },
  { label: 'Staff Coverage Gaps', value: '1' },
  { label: 'Balance Flags', value: '9' },
];

export default function ExtendedCareSnapshotCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Extended Care Snapshot
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
