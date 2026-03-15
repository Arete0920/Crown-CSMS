import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { title: 'Background clearance renewal due for 2 staff members', level: 'High' },
  { title: 'Science substitute coverage not confirmed for Friday', level: 'High' },
  { title: 'Employee handbook acknowledgment missing for 3 hires', level: 'Medium' },
  { title: 'Performance review packets not finalized', level: 'Low' },
];

export default function HRAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          HR Alerts
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
              <ListItemText
                primary={item.title}
                secondary="Requires HR or school leadership follow-up"
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
