import {
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  Chip,
} from '@mui/material';

const risks = [
  { title: 'Re-enrollment softness in Grade 6 and Grade 10', level: 'Medium' },
  { title: 'Teacher replacement pipeline thin in STEM roles', level: 'High' },
  { title: 'Financial aid demand rising faster than available budget', level: 'High' },
  { title: 'Deferred facilities maintenance planning needed', level: 'Medium' },
];

export default function BoardRiskPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Strategic Risks
        </Typography>

        <List disablePadding>
          {risks.map((item) => (
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
                secondary="Board-level concern; no student-level detail shown"
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
