import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { title: 'Spring concert stage setup still incomplete', level: 'High' },
  { title: 'Two costume orders not yet confirmed', level: 'Medium' },
  { title: 'Choir rehearsal room double-booked on Thursday', level: 'Medium' },
  { title: 'Lighting check not assigned for Friday performance', level: 'High' },
];

export default function FineArtsAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Fine Arts Alerts
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
                secondary="Director or production follow-up required"
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
