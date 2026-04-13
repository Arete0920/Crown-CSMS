import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { title: 'Three major donor follow-ups are overdue', level: 'High' },
  { title: 'Scholarship appeal packet not sent to one church partner', level: 'High' },
  { title: 'Event sponsor confirmation lagging behind target', level: 'Medium' },
  { title: 'Thank-you workflow missed two recent gifts', level: 'Medium' },
];

export default function AdvancementOpsAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Advancement Operations Alerts
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
                secondary="Advancement office action required"
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
