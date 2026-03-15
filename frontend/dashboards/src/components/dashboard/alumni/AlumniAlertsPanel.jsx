import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { title: 'Homecoming alumni outreach is behind schedule', level: 'High' },
  { title: 'Twelve profile changes are awaiting review', level: 'Medium' },
  { title: 'Reunion volunteer committee needs confirmation', level: 'Medium' },
  { title: 'Young alumni engagement rate dipped this quarter', level: 'High' },
];

export default function AlumniAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Alumni Relations Alerts
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
                  color={item.level === 'High' ? 'error' : 'warning'}
                />
              }
            >
              <ListItemText
                primary={item.title}
                secondary="Alumni relations follow-up required"
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
