import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText } from '@mui/material';

const queue = [
  'Provision accounts for new teacher hires',
  'Complete Chromebook imaging batch',
  'Resolve classroom projector outages',
  'Review help desk ticket aging',
  'Verify MFA enrollment completion',
];

export default function ITSupportQueueCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          IT Support Queue
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
