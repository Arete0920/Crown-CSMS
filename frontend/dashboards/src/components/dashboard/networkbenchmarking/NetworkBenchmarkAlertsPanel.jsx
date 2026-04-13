import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { title: 'Two schools are materially below retention benchmark', level: 'High' },
  { title: 'One region shows higher-than-normal payment retry failures', level: 'High' },
  { title: 'Three schools remain below volunteer engagement benchmark', level: 'Medium' },
  { title: 'PD completion variance widened this quarter', level: 'Medium' },
];

export default function NetworkBenchmarkAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Network Benchmark Alerts
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
                secondary="Portfolio-level action; no student-level detail exposed"
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
