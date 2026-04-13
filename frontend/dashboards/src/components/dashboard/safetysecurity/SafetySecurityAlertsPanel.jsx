import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { title: 'Visitor badge exception not yet closed', level: 'High' },
  { title: 'One exterior door check failed morning audit', level: 'High' },
  { title: 'Next lockdown drill communication plan not published', level: 'Medium' },
  { title: 'Cafeteria camera ticket remains open', level: 'Medium' },
];

export default function SafetySecurityAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Safety / Security Alerts
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
                secondary="Safety team or admin follow-up required"
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
