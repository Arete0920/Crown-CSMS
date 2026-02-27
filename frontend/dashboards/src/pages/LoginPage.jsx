/**
 * LoginPage — Microsoft 365 SSO only.
 *
 * Clicking "Sign in with Microsoft" redirects the browser to the Django
 * /auth/microsoft/login/ endpoint which initiates the OAuth2 flow.
 * On success Django sets a session cookie and redirects to /dash/<role>.
 *
 * No local password form. No JWT. No localStorage tokens.
 */
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

/** Inline Microsoft logo SVG — no icon package required. */
function MicrosoftLogo() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 21 21"
      width="20"
      height="20"
      aria-hidden="true"
    >
      <rect x="0"  y="0"  width="10" height="10" fill="#f25022" />
      <rect x="11" y="0"  width="10" height="10" fill="#7fba00" />
      <rect x="0"  y="11" width="10" height="10" fill="#00a4ef" />
      <rect x="11" y="11" width="10" height="10" fill="#ffb900" />
    </svg>
  );
}

export default function LoginPage() {
  const handleMicrosoftLogin = () => {
    window.location.href = `${API_BASE}/auth/microsoft/login/`;
  };

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "100vh",
        bgcolor: "grey.100",
      }}
    >
      <Paper
        elevation={3}
        sx={{
          p: 6,
          maxWidth: 400,
          width: "100%",
          textAlign: "center",
          borderRadius: 2,
        }}
      >
        <Stack spacing={4} alignItems="center">
          {/* Wordmark */}
          <Typography variant="h4" component="h1" fontWeight={700} letterSpacing={-0.5}>
            Crown2026
          </Typography>

          <Typography variant="body2" color="text.secondary">
            Sign in with your school Microsoft 365 account to continue.
          </Typography>

          {/* M365 SSO button */}
          <Button
            variant="outlined"
            size="large"
            onClick={handleMicrosoftLogin}
            startIcon={<MicrosoftLogo />}
            sx={{
              width: "100%",
              textTransform: "none",
              fontWeight: 500,
              borderColor: "grey.400",
              color: "text.primary",
              "&:hover": {
                borderColor: "grey.600",
                bgcolor: "grey.50",
              },
            }}
          >
            Sign in with Microsoft
          </Button>

          <Typography variant="caption" color="text.disabled">
            Access is restricted to provisioned accounts.
          </Typography>
        </Stack>
      </Paper>
    </Box>
  );
}
