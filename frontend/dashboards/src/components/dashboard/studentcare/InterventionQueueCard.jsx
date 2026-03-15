import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText } from '@mui/material';

const tasks = [
  'Call parents for attendance intervention case',
  'Log follow-up for chapel behavior incident',
  'Review academic support note with teacher team',
  'Close resolved care note after conference',
];

export default function InterventionQueueCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Intervention Queue
        </Typography>

        <List dense disablePadding>
          {tasks.map((task) => (
            <ListItem key={task} disableGutters>
              <ListItemText primary={task} />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
