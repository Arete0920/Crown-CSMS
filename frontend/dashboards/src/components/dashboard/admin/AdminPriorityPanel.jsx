import {
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  Chip,
} from '@mui/material';

const priorities = [
  { title: 'Grade 10 attendance dip for second straight week', level: 'High' },
  { title: 'Three families entering withdrawal-risk discussion', level: 'High' },
  { title: 'Financial aid decisions pending for late applicants', level: 'Medium' },
  { title: 'Teacher coverage strain in upper school science', level: 'Medium' },
  { title: 'Board packet due by Friday', level: 'Low' },
];

export default function AdminPriorityPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Administrator Priorities
        </Typography>

        <List disablePadding>
          {priorities.map((item) => (
            <ListItem
              key={item.title}
              disableGutters
              secondaryAction={
                <Chip
                  size="small"
                  label={item.level}
                  color={
                    item.level === 'High'
                      ? 'error'
                      : item.level === 'Medium'
                        ? 'warning'
                        : 'default'
                  }
                />
              }
            >
              <ListItemText
                primary={item.title}
                secondary="Requires admin review or leadership action"
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
