import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip, Stack } from '@mui/material';

const conflicts = [
  { title: 'Grade 9 Bible / English overlap', severity: 'High' },
  { title: 'Science lab double-booked', severity: 'Medium' },
  { title: 'Mrs. Carter exceeds prep threshold', severity: 'Medium' },
  { title: 'Gym conflict with volleyball block', severity: 'Low' },
];

export default function SchedulingConflictsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Scheduling Conflicts
        </Typography>

        <List disablePadding>
          {conflicts.map((item) => (
            <ListItem
              key={item.title}
              disableGutters
              secondaryAction={
                <Chip
                  size="small"
                  label={item.severity}
                  color={
                    item.severity === 'High'
                      ? 'error'
                      : item.severity === 'Medium'
                      ? 'warning'
                      : 'default'
                  }
                />
              }
            >
              <ListItemText primary={item.title} secondary="Needs registrar review" />
            </ListItem>
          ))}
        </List>

        <Stack mt={2}>
          <Typography variant="caption" color="text.secondary">
            Use this card later for live timetable collision results from the scheduling engine.
          </Typography>
        </Stack>
      </CardContent>
    </Card>
  );
}
