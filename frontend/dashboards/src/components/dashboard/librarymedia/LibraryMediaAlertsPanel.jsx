import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';

const alerts = [
  { title: 'Overdue STEM kit return affecting two classes', level: 'High' },
  { title: 'Book fair setup materials not yet delivered', level: 'Medium' },
  { title: 'Projector cart reservation conflict for Friday', level: 'Medium' },
  { title: 'Three teacher resource requests aging over 5 days', level: 'Low' },
];

export default function LibraryMediaAlertsPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Library / Media Alerts
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
                secondary="Library or media center action required"
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
