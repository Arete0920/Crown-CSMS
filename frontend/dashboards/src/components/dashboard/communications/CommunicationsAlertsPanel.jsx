import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { title: 'Parent thread requires finance follow-up', type: 'Finance' },
  { title: 'Attendance outreach not delivered to 3 families', type: 'Attendance' },
  { title: 'Teacher escalation pending admin response', type: 'Admin' },
];

export default function CommunicationsAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Communication Alerts
        </Typography>

        <List disablePadding>
          {alerts.map((item) => (
            <ListItem key={item.title} disableGutters secondaryAction={<Chip size="small" label={item.type} />}>
              <ListItemText primary={item.title} secondary="Resolve to keep family communication tight" />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
