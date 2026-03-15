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

const campaigns = [
  { title: 'Annual Fund pacing behind goal by 8%', level: 'Medium' },
  { title: 'Scholarship campaign response above target', level: 'Low' },
  { title: 'Capital reserve ask pending for 3 major donors', level: 'High' },
  { title: 'Church partner outreach packet not yet sent', level: 'Medium' },
];

export default function AdvancementCampaignPanel() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Campaign and Outreach Priorities
        </Typography>

        <List disablePadding>
          {campaigns.map((item) => (
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
                secondary="Advancement or head-of-school follow-up needed"
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
