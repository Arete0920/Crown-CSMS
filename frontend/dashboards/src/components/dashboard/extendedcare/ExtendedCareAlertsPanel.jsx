import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { title: 'One late pickup requires parent follow-up', level: 'High' },
  { title: 'Aftercare snack inventory running low', level: 'Medium' },
  { title: 'Tomorrow staffing coverage not fully confirmed', level: 'High' },
  { title: 'Nine accounts flagged for outstanding balance review', level: 'Medium' },
];

export default function ExtendedCareAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Extended Care Alerts
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
                secondary="Extended care coordinator follow-up needed"
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
