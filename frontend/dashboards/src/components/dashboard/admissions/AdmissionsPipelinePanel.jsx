import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  Chip,
} from '@mui/material';

const queue = [
  { title: '12 applications awaiting transcript review', tag: 'Review' },
  { title: '8 pastoral references still missing', tag: 'Documents' },
  { title: '5 family interviews need scheduling', tag: 'Schedule' },
  { title: '4 accepted families are cold after offer', tag: 'Yield Risk' },
];

export default function AdmissionsPipelinePanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Admissions Work Queue
        </Typography>

        <List disablePadding>
          {queue.map((item) => (
            <ListItem
              key={item.title}
              disableGutters
              secondaryAction={<Chip size="small" label={item.tag} />}
            >
              <ListItemText
                primary={item.title}
                secondary="Admissions team action required"
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
