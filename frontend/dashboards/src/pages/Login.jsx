import { Box, Paper, Typography, TextField, Button, Stack } from "@mui/material";

/**
 * Login — split-panel login template with Crown branding.
 *
 * This is a UI design template using the crownTheme color system.
 * Production auth routes to LoginPage.jsx (M365 SSO via /auth/microsoft/login/).
 */
export default function Login() {
  return (
    <Box sx={{ display: "flex", height: "100vh" }}>
      {/* Left brand panel */}
      <Box
        sx={{
          flex: 1,
          background: "linear-gradient(135deg, #1B3A6F 0%, #274C91 100%)",
          color: "var(--crown-surface)",
          p: 6,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
        }}
      >
        <Typography variant="h1" sx={{ color: "var(--crown-surface)", mb: 1 }}>
          Crown2026
        </Typography>
        <Typography variant="body1" sx={{ color: "rgba(255,255,255,0.72)" }}>
          School information system
        </Typography>
      </Box>

      {/* Right form panel */}
      <Box
        sx={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          bgcolor: "background.default",
        }}
      >
        <Paper sx={{ p: 5, width: 360, boxShadow: "0 4px 24px rgba(0,0,0,0.08)" }}>
          <Stack spacing={2.5}>
            <Typography variant="h2" sx={{ mb: 0.5 }}>
              Sign In
            </Typography>

            <TextField fullWidth label="Email" type="email" size="small" />
            <TextField fullWidth label="Password" type="password" size="small" />

            <Button fullWidth variant="contained" size="large">
              Login
            </Button>
          </Stack>
        </Paper>
      </Box>
    </Box>
  );
}
