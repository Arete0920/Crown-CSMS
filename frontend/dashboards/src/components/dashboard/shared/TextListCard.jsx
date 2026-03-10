import { Card, CardContent, Typography, List, ListItem, ListItemText } from '@mui/material';

export default function TextListCard({ title, items = [] }) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>

        <List dense disablePadding>
          {items.map((item, index) => (
            <ListItem key={`${item}-${index}`} disableGutters>
              <ListItemText primary={item} />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
