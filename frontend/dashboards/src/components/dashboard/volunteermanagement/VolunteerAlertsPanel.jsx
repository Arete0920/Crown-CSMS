import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { title: 'Three event stations still have no volunteer coverage', level: 'High' },
  { title: 'Seven volunteers require clearance completion', level: 'High' },
  { title: 'Service-day parent sign-ups below target', level: 'Medium' },
  { title: 'Two volunteer hour approvals still pending', level: 'Low' },
];

export default function VolunteerAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Volunteer Alerts
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
              <ListItemText primary={item.title} secondary="Volunteer coordinator action required" />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
