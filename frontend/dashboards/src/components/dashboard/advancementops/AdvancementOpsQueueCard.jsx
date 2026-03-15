import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText } from '@mui/material';

const queue = [
  'Send major donor stewardship updates',
  'Finalize church partner scholarship packet',
  'Review proposal packet approvals',
  'Assign post-event thank-you calls',
  'Update advancement task board',
];

export default function AdvancementOpsQueueCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Advancement Operations Queue
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
