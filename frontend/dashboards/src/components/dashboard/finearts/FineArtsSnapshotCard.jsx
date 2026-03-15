import React from 'react';
import { Card, CardContent, Typography, Stack, Divider } from '@mui/material';

const metrics = [
  { label: 'Active Programs', value: '7' },
  { label: 'Upcoming Performances', value: '4' },
  { label: 'Student Participants', value: '163' },
  { label: 'Rehearsal Conflicts', value: '3' },
  { label: 'Equipment Needs Open', value: '5' },
];

export default function FineArtsSnapshotCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Fine Arts Snapshot
        </Typography>

        <Stack spacing={1.5}>
          {metrics.map((item, idx) => (
            <React.Fragment key={item.label}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
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
