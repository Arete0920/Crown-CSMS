import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { title: 'Microsoft 365 roster sync failed for one tenant cluster', level: 'High' },
  { title: 'Payment processing callback retries exceeded threshold', level: 'High' },
  { title: 'Two Power Automate jobs are stuck in queued state', level: 'Medium' },
  { title: 'Outbound notification delivery dipped below SLA', level: 'Medium' },
];

export default function IntegrationsAutomationAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Integration Alerts
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
                secondary="Integration or automation follow-up required"
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
