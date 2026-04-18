import { Card, CardContent, Typography, List, ListItem, ListItemText } from '@mui/material';

const queue = [
  'Review open prayer and care requests',
  'Finalize next chapel speaker schedule',
  'Assign small group follow-up conversations',
  'Close resolved care notes',
  'Prepare weekly spiritual life update',
];

export default function ChaplainQueueCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Chaplain Work Queue
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
