import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { title: 'Milk inventory below threshold', level: 'Medium' },
  { title: '27 families need low-balance reminders', level: 'High' },
  { title: 'Allergen meal prep checklist not signed', level: 'High' },
  { title: 'Friday field trip boxed lunch count pending', level: 'Low' },
];

export default function FoodServiceAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Food Service Alerts
        </Typography>

        <List disablePadding>
          {alerts.map((item) => (
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
              <ListItemText primary={item.title} secondary="Kitchen or finance follow-up needed" />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
