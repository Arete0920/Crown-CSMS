import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { label: '11 students below 70% in Algebra I', type: 'Academic Risk' },
  { label: '3 teachers have grading backlog > 5 days', type: 'Teacher Action' },
  { label: '7 missing assignment patterns need outreach', type: 'Parent Contact' },
];

export default function GradebookAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Gradebook Alerts
        </Typography>

        <List disablePadding>
          {alerts.map((alert) => (
            <ListItem
              key={alert.label}
              disableGutters
              secondaryAction={<Chip size="small" label={alert.type} />}
            >
              <ListItemText primary={alert.label} secondary="Review with teachers or academic support" />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
