import { Button, Paper, Stack, Typography } from '@mui/material';

export default function ActionCard({
  title,
  description,
  primaryActionLabel,
  onPrimaryAction,
  secondaryAction = null,
}) {
  return (
    <Paper elevation={1} sx={{ p: 2.5, borderRadius: 3, minHeight: 180 }}>
      <Stack spacing={2}>
        <Typography variant="h6" fontWeight={700}>
          {title}
        </Typography>

        <Typography variant="body2" color="text.secondary">
          {description}
        </Typography>

        <Stack direction="row" spacing={1.5}>
          <Button variant="contained" onClick={onPrimaryAction}>
            {primaryActionLabel}
          </Button>
          {secondaryAction}
        </Stack>
      </Stack>
    </Paper>
  );
}
