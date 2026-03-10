import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { title: 'Two schools are missing finalized admissions config', level: 'High' },
  { title: 'One school training plan is behind by 6 days', level: 'High' },
  { title: 'Billing setup checklist incomplete for upcoming launch', level: 'Medium' },
  { title: 'Parent portal communications draft not approved', level: 'Medium' },
];

export default function ImplementationSuccessAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Implementation Alerts
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
                secondary="Implementation manager follow-up required"
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
