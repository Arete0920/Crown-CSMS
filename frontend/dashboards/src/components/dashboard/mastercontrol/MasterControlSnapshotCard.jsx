import React from 'react';
import { Card, CardContent, Typography, Stack, Divider } from '@mui/material';

const metrics = [
  { label: 'Active Schools', value: '24' },
  { label: 'Students Managed', value: '8,940' },
  { label: 'Payments Processed MTD', value: '$4.28M' },
  { label: 'Aid Applications This Cycle', value: '1,162' },
  { label: 'Open Tenant Alerts', value: '5' },
];

export default function MasterControlSnapshotCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Portfolio Snapshot
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
