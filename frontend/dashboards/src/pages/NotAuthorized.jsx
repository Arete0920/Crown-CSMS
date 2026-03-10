import React from 'react';
import { Card, CardContent, Stack, Typography, Button } from '@mui/material';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { getCurrentUserRoles } from '../auth/roleAdapter';
import { getDefaultDashboardPath } from '../config/dashboardRegistry';

export default function NotAuthorized() {
  const location = useLocation();
  const userRoles = getCurrentUserRoles();
  const fallbackPath = getDefaultDashboardPath(userRoles);
  const attemptedPath = location.state?.from || 'that page';

  return (
    <Stack spacing={3}>
      <Typography variant="h4" fontWeight={700}>
        Access Restricted
      </Typography>

      <Card>
        <CardContent>
          <Stack spacing={2}>
            <Typography variant="body1">
              You do not have permission to access <strong>{attemptedPath}</strong>.
            </Typography>

            <Typography variant="body2" color="text.secondary">
              If this is wrong, fix the assigned role set. Do not bypass the route guard.
            </Typography>

            <Stack direction="row" spacing={2}>
              <Button
                component={RouterLink}
                to={fallbackPath}
                variant="contained"
              >
                Go to Allowed Dashboard
              </Button>

              <Button
                component={RouterLink}
                to="/"
                variant="outlined"
              >
                Go Home
              </Button>
            </Stack>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
}
