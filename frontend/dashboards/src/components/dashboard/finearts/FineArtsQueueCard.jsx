import { Card, CardContent, Typography, List, ListItem, ListItemText } from '@mui/material';

const queue = [
  'Approve final rehearsal calendar',
  'Confirm auditorium setup for performance weekend',
  'Publish student call-time schedule',
  'Review instrument repair requests',
  'Send parent volunteer reminder',
];

export default function FineArtsQueueCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Fine Arts Work Queue
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
