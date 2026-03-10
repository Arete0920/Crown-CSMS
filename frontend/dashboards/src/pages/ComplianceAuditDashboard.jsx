import React from 'react';
import { Grid, Stack, Typography } from '@mui/material';
import ComplianceAuditSnapshotCard from '../components/dashboard/complianceaudit/ComplianceAuditSnapshotCard';
import ComplianceAuditAlertsPanel from '../components/dashboard/complianceaudit/ComplianceAuditAlertsPanel';
import ComplianceAuditQueueCard from '../components/dashboard/complianceaudit/ComplianceAuditQueueCard';

export default function ComplianceAuditDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Compliance / Audit Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Tenant safety, audit evidence, policy readiness, and control exceptions across Crown.
        </Typography>
      </div>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <ComplianceAuditSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <ComplianceAuditAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <ComplianceAuditQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
