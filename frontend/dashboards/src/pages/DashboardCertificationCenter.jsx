import {
  Card,
  CardContent,
  Chip,
  Grid,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { DASHBOARD_REGISTRY } from '../config/dashboardRegistry';
import {
  DASHBOARD_CERTIFICATION_REGISTRY,
  getCertificationStatusColor,
} from '../config/dashboardCertificationRegistry';
import { DASHBOARD_DATA_REGISTRY } from '../config/dashboardDataRegistry';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

function countByStatus(status) {
  return Object.values(DASHBOARD_CERTIFICATION_REGISTRY).filter(
    (item) => item.status === status
  ).length;
}

const DASH_CERT_KPI = [
  { label: 'Certified', value: '—', dataSource: 'Registry' },
  { label: 'In Review', value: '—', dataSource: 'Registry' },
  { label: 'Pending', value: '—', dataSource: 'Registry' },
  { label: 'Blocked', value: '—', dataSource: 'Registry' }
];

export default function DashboardCertificationCenter() {
  const rows = DASHBOARD_REGISTRY.map((dashboard) => {
    const certification = DASHBOARD_CERTIFICATION_REGISTRY[dashboard.key] || {
      status: 'scaffold',
      owner: 'Unknown',
      notes: '',
    };

    const dataConfig = DASHBOARD_DATA_REGISTRY[dashboard.key];

    return {
      ...dashboard,
      certification,
      endpoint: dataConfig?.endpoint || '—',
    };
  });

  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Dashboard Certification Center
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Single view of dashboard readiness, endpoint binding, ownership, and rollout posture.
        </Typography>
      </div>

      <KpiStrip cards={DASH_CERT_KPI} />

      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                Scaffold
              </Typography>
              <Typography variant="h4" fontWeight={700}>
                {countByStatus('scaffold')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                Hybrid
              </Typography>
              <Typography variant="h4" fontWeight={700}>
                {countByStatus('hybrid')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                Live
              </Typography>
              <Typography variant="h4" fontWeight={700}>
                {countByStatus('live')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                Certified
              </Typography>
              <Typography variant="h4" fontWeight={700}>
                {countByStatus('certified')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Dashboard Readiness Matrix
          </Typography>

          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Tier</TableCell>
                <TableCell>Label</TableCell>
                <TableCell>Section</TableCell>
                <TableCell>Path</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Owner</TableCell>
                <TableCell>Endpoint</TableCell>
              </TableRow>
            </TableHead>

            <TableBody>
              {rows.map((row) => (
                <TableRow key={row.key}>
                  <TableCell>{row.tier}</TableCell>
                  <TableCell>{row.label}</TableCell>
                  <TableCell>{row.section}</TableCell>
                  <TableCell>{row.path}</TableCell>
                  <TableCell>
                    <Chip
                      size="small"
                      label={row.certification.status}
                      color={getCertificationStatusColor(row.certification.status)}
                    />
                  </TableCell>
                  <TableCell>{row.certification.owner}</TableCell>
                  <TableCell>{row.endpoint}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </Stack>
  );
}
