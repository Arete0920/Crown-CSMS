import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { title: 'Thirty-six students are below service-hour target pace', level: 'High' },
  { title: 'Mentor approval queue has aged beyond 5 days', level: 'Medium' },
  { title: 'One service partner site needs renewal approval', level: 'Medium' },
  { title: 'Senior capstone reflection uploads incomplete', level: 'High' },
];

export default function PortraitServiceAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Portrait / Service Alerts
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
                secondary="Coordinator or advisor follow-up required"
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
