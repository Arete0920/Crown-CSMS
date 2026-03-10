import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { title: 'One access-role exception lacks final approval evidence', level: 'High' },
  { title: 'Audit packet for February deployment not complete', level: 'High' },
  { title: 'Tenant header enforcement evidence needs refresh', level: 'Medium' },
  { title: 'Quarterly policy acknowledgment campaign not launched', level: 'Medium' },
];

export default function ComplianceAuditAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Compliance Alerts
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
                secondary="Compliance owner follow-up required"
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
