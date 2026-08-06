import { Box, Typography, Divider } from "@mui/material";

/**
 * DashboardSection — consistent titled section wrapper.
 *
 * Usage:
 *   <DashboardSection title="Executive Summary">
 *     <Grid container spacing={2}>…</Grid>
 *   </DashboardSection>
 */
export default function DashboardSection({ title, subtitle, children }) {
  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h2" sx={{ mb: subtitle ? 0.25 : 1 }}>
        {title}
      </Typography>
      {subtitle && (
        <Typography variant="body2" sx={{ mb: 1 }}>
          {subtitle}
        </Typography>
      )}
      <Divider sx={{ mb: 2 }} />
      {children}
    </Box>
  );
}
