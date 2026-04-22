import {
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  Chip,
} from '@mui/material';

function getChipProps(level) {
  const normalized = String(level || '').toLowerCase();
  if (normalized === 'high') return { color: 'error' };
  if (normalized === 'medium') {
    return {
      color: 'warning',
      sx: {
        '& .MuiChip-label': { color: '#4d3200', fontWeight: 600 },
        bgcolor: '#f8d58a',
      },
    };
  }
  return { color: 'default' };
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
            // Keep chip props computed once for each item so warning color gets readable foreground.
            (() => {
              const chipProps = getChipProps(item.level);
              return (
            <ListItem
              key={`${item.title}-${index}`}
              disableGutters
              secondaryAction={
                <Chip
                  size="small"
                  label={item.level || 'Low'}
                  color={chipProps.color}
                  sx={chipProps.sx}
                />
              }
            >
              <ListItemText
                primary={item.title}
                secondary={item.secondary || ''}
              />
            </ListItem>
              );
            })()
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
