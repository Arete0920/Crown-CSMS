import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { title: 'Contract gate failed on last main candidate build', level: 'High' },
  { title: 'Two environments are not on expected build SHA', level: 'High' },
  { title: 'One release proof packet is incomplete', level: 'Medium' },
  { title: 'Post-deploy smoke evidence missing for latest rollout', level: 'Medium' },
];

export default function ReleaseReliabilityAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Release Reliability Alerts
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
                secondary="Platform engineering follow-up required"
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
