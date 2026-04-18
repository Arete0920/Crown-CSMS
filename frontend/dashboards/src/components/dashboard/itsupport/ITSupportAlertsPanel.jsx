import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { title: 'SSO sync failure affecting 3 new staff accounts', level: 'High' },
  { title: 'Two classroom projectors offline', level: 'Medium' },
  { title: 'Wi-Fi complaint spike in west wing', level: 'Medium' },
  { title: 'Pending student Chromebook swap approvals', level: 'Low' },
];

export default function ITSupportAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          IT Support Alerts
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
              <ListItemText primary={item.title} secondary="IT action required" />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
