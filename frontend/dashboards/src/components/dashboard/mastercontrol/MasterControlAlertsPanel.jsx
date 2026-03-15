import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  Chip,
} from '@mui/material';

const alerts = [
  { title: 'One tenant reporting rising failed payment retries', level: 'Medium' },
  { title: 'Two schools lagging re-enrollment benchmarks', level: 'High' },
  { title: 'Aid review backlog above SLA in one region', level: 'Medium' },
  { title: 'Messaging delivery health dip in one school cluster', level: 'Low' },
];

export default function MasterControlAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Portfolio Alerts
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
                  color={
                    item.level === 'High'
                      ? 'error'
                      : item.level === 'Medium'
                        ? 'warning'
                        : 'default'
                  }
                />
              }
            >
              <ListItemText
                primary={item.title}
                secondary="Platform-level intervention or account management follow-up"
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
