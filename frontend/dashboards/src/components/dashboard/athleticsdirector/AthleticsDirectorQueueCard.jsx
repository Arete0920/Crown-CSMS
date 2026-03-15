import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText } from '@mui/material';

const queue = [
  'Finalize tournament staffing assignments',
  'Confirm team travel rosters',
  'Post weekly athletics schedule update',
  'Review athlete academic check-ins',
  'Approve game-day volunteer layout',
];

export default function AthleticsDirectorQueueCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Athletics Director Queue
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
