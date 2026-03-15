import { Box, Stack, TextField, Typography } from '@mui/material';

export default function CrownTableToolbar({
  title,
  subtitle,
  searchValue = '',
  onSearchChange,
  filters = null,
  actions = null,
  searchPlaceholder = 'Search',
}) {
  return (
    <Stack spacing={2} sx={{ mb: 2 }}>
      <Stack
        direction={{ xs: 'column', md: 'row' }}
        justifyContent="space-between"
        alignItems={{ xs: 'flex-start', md: 'center' }}
        spacing={2}
      >
        <Box>
          {title ? (
            <Typography variant="h6" fontWeight={700}>
              {title}
            </Typography>
          ) : null}
          {subtitle ? (
            <Typography variant="body2" color="text.secondary">
              {subtitle}
            </Typography>
          ) : null}
        </Box>

        {actions}
      </Stack>

      <Stack
        direction={{ xs: 'column', md: 'row' }}
        spacing={2}
        alignItems={{ xs: 'stretch', md: 'center' }}
      >
        <TextField
          label={searchPlaceholder}
          value={searchValue}
          onChange={(event) => onSearchChange?.(event.target.value)}
          size="small"
          sx={{ minWidth: 280 }}
        />

        {filters}
      </Stack>
    </Stack>
  );
}
