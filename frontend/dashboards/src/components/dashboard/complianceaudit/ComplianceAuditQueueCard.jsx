import { Card, CardContent, Typography, List, ListItem, ListItemText } from '@mui/material';

const queue = [
  'Close unresolved access exception',
  'Refresh tenant enforcement evidence bundle',
  'Complete monthly audit packet assembly',
  'Review open policy review tasks',
  'Publish compliance status note to leadership',
];

export default function ComplianceAuditQueueCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Compliance Queue
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
