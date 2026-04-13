import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { title: 'Route 4 driver substitute not confirmed', level: 'High' },
  { title: 'Vehicle 12 inspection expires this week', level: 'Medium' },
  { title: 'Afternoon dismissal route running 14 minutes late', level: 'High' },
  { title: 'Two family stop changes pending approval', level: 'Low' },
];

export default function TransportationAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Transportation Alerts
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
                  color={item.level === 'High' ? 'error' : item.level === 'Medium' ? 'warning' : 'default'}
                />
              }
            >
              <ListItemText primary={item.title} secondary="Transportation team action required" />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
