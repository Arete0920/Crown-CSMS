import React from 'react';
import { Card, CardContent, Typography, Stack, Divider } from '@mui/material';

const metrics = [
  { label: 'Open Audit Exceptions', value: '6' },
  { label: 'Tenant Safety Checks Passing', value: '99.2%' },
  { label: 'Policy Reviews Due', value: '4' },
  { label: 'Access Exceptions Pending', value: '3' },
  { label: 'Evidence Packets Ready', value: '11' },
];

export default function ComplianceAuditSnapshotCard() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Compliance Snapshot
        </Typography>

        <Stack spacing={1.5}>
          {metrics.map((item, index) => (
            <React.Fragment key={item.label}>
              <Stack direction="row" justifyContent="space-between">
                <Typography variant="body2" color="text.secondary">
                  {item.label}
                </Typography>
                <Typography variant="subtitle1" fontWeight={700}>
                  {item.value}
                </Typography>
              </Stack>
              {index < metrics.length - 1 && <Divider />}
            </React.Fragment>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
}
