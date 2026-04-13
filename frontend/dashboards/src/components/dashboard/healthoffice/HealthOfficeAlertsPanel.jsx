import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { title: 'Medication consent missing for 1 student', level: 'High' },
  { title: '2 students require parent follow-up today', level: 'Medium' },
  { title: 'Allergy action plan review due this week', level: 'High' },
  { title: 'Immunization document upload incomplete', level: 'Medium' },
];

export default function HealthOfficeAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Health Office Alerts
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
              <ListItemText primary={item.title} secondary="Requires nurse or office follow-up" />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
