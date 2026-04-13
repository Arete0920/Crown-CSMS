import { Card, CardContent, Typography, List, ListItem, ListItemText } from '@mui/material';

const queue = [
  'Review failed release gate evidence',
  'Verify environment build SHA alignment',
  'Close open production incident postmortem tasks',
  'Complete release proof packet for latest deploy',
  'Publish release readiness summary',
];

export default function ReleaseReliabilityQueueCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Release Reliability Queue
        </Typography>

        <List dense disablePadding>
          {queue.map((item) => (
            <ListItem key={item} disableGutters>
              <ListItemText primary={item} />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
