import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const items = [
  { title: 'Repeat attendance + discipline pattern in Grade 8', level: 'High' },
  { title: 'Parent conference overdue for two students', level: 'Medium' },
  { title: 'Counselor follow-up needed after re-entry', level: 'Medium' },
  { title: 'Uniform/policy reminder trend', level: 'Low' },
];

export default function StudentCareAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Care and Discipline Alerts
        </Typography>

        <List disablePadding>
          {items.map((item) => (
            <ListItem
              key={item.title}
              disableGutters
              secondaryAction={
                <Chip
                  size="small"
                  label={item.level}
                  color={item.level === 'High' ? 'error' : item.level === 'Medium' ? 'warning' : 'default'}
                />
              }
            >
              <ListItemText primary={item.title} secondary="Review with dean, counselor, or admin" />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
