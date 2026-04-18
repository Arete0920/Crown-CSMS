import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { title: 'Bible curriculum review overdue for upper school', level: 'High' },
  { title: 'Twelve teachers missing required PD evidence upload', level: 'High' },
  { title: 'Two departments lack updated pacing guides', level: 'Medium' },
  { title: 'One new teacher induction track not completed', level: 'Medium' },
];

export default function CurriculumPDAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Curriculum / PD Alerts
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
                secondary="Curriculum leader or PD coordinator follow-up required"
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
