import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { title: 'Student household import has unresolved parent-link mismatches', level: 'High' },
  { title: 'Legacy billing export missing required school-year field', level: 'High' },
  { title: 'One attendance file contains duplicate student identifiers', level: 'Medium' },
  { title: 'Final cutover validation report not signed off', level: 'Medium' },
];

export default function DataMigrationAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Data Migration Alerts
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
                secondary="Migration engineer action required"
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
