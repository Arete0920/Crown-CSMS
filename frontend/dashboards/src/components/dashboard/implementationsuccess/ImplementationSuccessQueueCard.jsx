import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText } from '@mui/material';

const queue = [
  'Finalize go-live checklist for Heritage Christian Academy',
  'Confirm training roster for next Tuesday session',
  'Review admissions wizard configuration gap',
  'Send school readiness summary to implementation lead',
  'Close completed launch tasks from last wave',
];

export default function ImplementationSuccessQueueCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Implementation Queue
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
