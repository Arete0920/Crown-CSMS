import {
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  Chip,
} from '@mui/material';

function getChipColor(level) {
  const normalized = String(level || '').toLowerCase();
  if (normalized === 'high') return 'error';
  if (normalized === 'medium') return 'warning';
  return 'default';
}

export default function AlertListCard({ title, items = [] }) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>

        <List disablePadding>
          {items.map((item, index) => (
            <ListItem
              key={`${item.title}-${index}`}
              disableGutters
              secondaryAction={
                <Chip
                  size="small"
                  label={item.level || 'Low'}
                  color={getChipColor(item.level)}
                />
              }
            >
              <ListItemText
                primary={item.title}
                secondary={item.secondary || ''}
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
