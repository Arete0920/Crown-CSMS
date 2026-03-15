import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText } from '@mui/material';

const queue = [
  'Review outlier schools against retention benchmark',
  'Update cross-school KPI comparison packet',
  'Assign support outreach to flagged schools',
  'Audit quarter-to-date benchmark freshness',
  'Prepare network benchmarking summary for leadership',
];

export default function NetworkBenchmarkQueueCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Network Benchmark Queue
        </Typography>

        <List dense disablePadding>
          {queue.map((item) => (
            <ListItem key={item} disableGutters>
              <ListItemText primary={item} />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
