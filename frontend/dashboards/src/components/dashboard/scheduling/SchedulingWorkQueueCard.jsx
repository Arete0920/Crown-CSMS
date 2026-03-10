import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText } from '@mui/material';

const items = [
  'Finalize middle school electives',
  'Confirm room assignments for labs',
  'Resolve teacher overload exceptions',
  'Publish draft student schedules',
  'Lock spring athletics travel blocks',
];

export default function SchedulingWorkQueueCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Registrar Work Queue
        </Typography>

        <List dense disablePadding>
          {items.map((item) => (
            <ListItem key={item} disableGutters>
              <ListItemText primary={item} />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
