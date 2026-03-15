import React from 'react';
import { Card, CardContent, Typography, Stack, Divider } from '@mui/material';

const metrics = [
  { label: 'Meals Served Today', value: '342' },
  { label: 'Low-Balance Accounts', value: '27' },
  { label: 'Special Meal Flags', value: '9' },
  { label: 'Inventory Warnings', value: '4' },
  { label: 'Catering/Event Requests', value: '3' },
];

export default function FoodServiceSnapshotCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Food Service Snapshot
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
