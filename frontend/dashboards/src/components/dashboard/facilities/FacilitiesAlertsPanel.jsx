import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { title: 'Gym HVAC ticket still unresolved', level: 'High' },
  { title: 'Playground inspection due this week', level: 'Medium' },
  { title: 'Leak reported in lower school hallway', level: 'High' },
  { title: 'Chapel seating setup incomplete for Thursday', level: 'Low' },
];

export default function FacilitiesAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Facilities Alerts
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
              <ListItemText primary={item.title} secondary="Needs facilities team action" />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
