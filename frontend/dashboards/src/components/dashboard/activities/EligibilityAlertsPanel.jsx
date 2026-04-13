import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { title: '3 athletes below grade threshold', label: 'Academic' },
  { title: '2 missing physical forms', label: 'Compliance' },
  { title: '1 travel roster awaiting approval', label: 'Operations' },
];

export default function EligibilityAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Eligibility and Event Alerts
        </Typography>

        <List disablePadding>
          {alerts.map((item) => (
            <ListItem key={item.title} disableGutters secondaryAction={<Chip size="small" label={item.label} />}>
              <ListItemText primary={item.title} secondary="Resolve before event participation" />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
