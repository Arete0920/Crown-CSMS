import React from 'react';
import { Alert } from '@mui/material';

export default function DashboardErrorState({ error }) {
  return (
    <Alert severity="error">
      {error?.message || 'Dashboard data failed to load.'}
    </Alert>
  );
}
