import { Card, CardContent, Typography, List, ListItem, ListItemText } from '@mui/material';

const queue = [
  'Review upper school Bible curriculum notes',
  'Send PD evidence upload reminder batch',
  'Approve new teacher induction completion',
  'Update pacing guide tracker',
  'Respond to department resource requests',
];

export default function CurriculumPDQueueCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Curriculum / PD Queue
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
