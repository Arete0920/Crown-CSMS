import { Card, CardContent, Typography, List, ListItem, ListItemText } from '@mui/material';

const queue = [
  'Issue pending implementation invoice',
  'Review overdue account outreach plan',
  'Finalize renewal proposal packet',
  'Assign collections exception owner',
  'Publish month-to-date revenue ops summary',
];

export default function RevenueOpsQueueCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Revenue Operations Queue
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
