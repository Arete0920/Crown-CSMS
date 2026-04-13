import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { title: 'Three care follow-ups have aged beyond 7 days', level: 'High' },
  { title: 'Senior chapel testimony schedule still incomplete', level: 'Medium' },
  { title: 'Two student prayer requests need parent-sensitive review', level: 'High' },
  { title: 'Small group attendance dipped in one cohort', level: 'Medium' },
];

export default function ChaplainAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Spiritual Care Alerts
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
                secondary="Chaplain or spiritual life team follow-up required"
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
