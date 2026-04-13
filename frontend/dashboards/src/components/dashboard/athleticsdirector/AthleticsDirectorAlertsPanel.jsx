import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { title: 'Three athletes below eligibility threshold', level: 'High' },
  { title: 'Away-game bus request not finalized', level: 'High' },
  { title: 'One coach background renewal due this week', level: 'Medium' },
  { title: 'Game workers incomplete for Saturday tournament', level: 'Medium' },
];

export default function AthleticsDirectorAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Athletics Alerts
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
                secondary="Athletics office action required"
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
