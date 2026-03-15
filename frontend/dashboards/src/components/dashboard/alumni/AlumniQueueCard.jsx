import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText } from '@mui/material';

const queue = [
  'Send reunion outreach batch',
  'Approve pending alumni profile updates',
  'Review homecoming event RSVP progress',
  'Assign young alumni engagement calls',
  'Publish alumni spotlight content calendar',
];

export default function AlumniQueueCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Alumni Relations Queue
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
