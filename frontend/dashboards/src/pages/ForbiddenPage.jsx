import { Box, Button, Paper, Stack, Typography } from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';
import { PATHS } from '../routes/paths';

export default function ForbiddenPage() {
  const location = useLocation();
  const navigate = useNavigate();

  const state = location.state || {};
  const role = state.role || 'unknown';
  const from = state.from || 'unknown page';

  return (
    <Box sx={{ p: 4 }}>
      <Paper elevation={2} sx={{ maxWidth: 760, p: 4, mx: 'auto', borderRadius: 3 }}>
        <Stack spacing={2}>
          <Typography variant="h4" fontWeight={700}>
            Access denied
          </Typography>

          <Typography variant="body1">
            Your current role does not have access to this page.
          </Typography>

          <Typography variant="body2" color="text.secondary">
            Role: <strong>{role}</strong>
          </Typography>

          <Typography variant="body2" color="text.secondary">
            Requested page: <strong>{from}</strong>
          </Typography>

          <Stack direction="row" spacing={2} sx={{ pt: 1 }}>
            <Button variant="contained" onClick={() => navigate(PATHS.HOME)}>
              Back to home
            </Button>
            <Button variant="outlined" onClick={() => navigate(-1)}>
              Go back
            </Button>
          </Stack>
        </Stack>
      </Paper>
    </Box>
  );
}
