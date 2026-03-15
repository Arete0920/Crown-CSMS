import React from 'react';
import { Card, CardContent, Typography, Stack, Divider } from '@mui/material';

const metrics = [
  { label: 'Alumni Records Verified', value: '1,284' },
  { label: 'Recent Touchpoints This Month', value: '73' },
  { label: 'Event RSVPs Open', value: '41' },
  { label: 'Giving Alumni This Year', value: '126' },
  { label: 'Profile Updates Pending Review', value: '12' },
];

export default function AlumniSnapshotCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Alumni Snapshot
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
