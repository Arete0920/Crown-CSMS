import { useCallback, useEffect, useState } from "react";
import {
  Alert, Box, Button, Card, CardContent, Chip, CircularProgress,
  Container, Stack, Table, TableBody, TableCell, TableHead,
  TableRow, Typography,
} from "@mui/material";
import { authenticatedJson } from "../utils/authClient.js";

/**
 * CROWN operator console. Authorization and corporate data ownership remain
 * entirely server-side. No school-selector header belongs on global requests.
 * This surface intentionally provides no write access or simulated revenue.
 */
export default function PlatformOwnerConsole() {
  const [overview, setOverview] = useState(null);
  const [schools, setSchools] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const summary = await authenticatedJson("/api/platform/overview", {
        omitSchoolContext: true,
      });
      const list = await authenticatedJson("/api/platform/schools/list", {
        omitSchoolContext: true,
        query: { page: 1, per_page: 50 },
      });
      setOverview(summary);
      setSchools(list);
    } catch (caught) {
      setOverview(null);
      setSchools(null);
      setError(
        caught?.status === 403
          ? "Access denied: active platform-operator authority is required."
          : "Unable to load operator records. Verify backend availability and your session.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const statusEntries = Object.entries(overview?.schools?.by_status || {});
  const jobEntries = Object.entries(overview?.provisioning?.by_state || {});

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Stack direction="row" alignItems="center" justifyContent="space-between" mb={3}>
        <Box>
          <Typography variant="h4" component="h1">CROWN Owner Control Center</Typography>
          <Typography variant="body2" color="text.secondary">
            Platform operations · authenticated, read-only current-database view
          </Typography>
        </Box>
        <Button variant="outlined" onClick={refresh} disabled={loading}>Refresh</Button>
      </Stack>
      {loading && <CircularProgress aria-label="Loading operator data" />}
      {error && <Alert severity="error">{error}</Alert>}
      {overview && (
        <Stack spacing={3}>
          <Alert severity="info">
            Counts describe records in this database, including any sandbox records.
            They are not verified paying-customer counts. Source: {overview.meta?.data_source};
            as of {overview.meta?.as_of}.
          </Alert>
          <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
            <Card sx={{ flex: 1 }}><CardContent>
              <Typography variant="overline">School tenant records</Typography>
              <Typography variant="h3">{overview.schools.total}</Typography>
              <Stack direction="row" gap={1} flexWrap="wrap">
                {statusEntries.map(([state, count]) => <Chip key={state} label={`${state}: ${count}`} size="small" />)}
              </Stack>
            </CardContent></Card>
            <Card sx={{ flex: 1 }}><CardContent>
              <Typography variant="overline">Provisioning jobs</Typography>
              <Typography variant="h3">
                {jobEntries.reduce((sum, [, count]) => sum + count, 0)}
              </Typography>
              <Stack direction="row" gap={1} flexWrap="wrap">
                {jobEntries.map(([state, count]) => <Chip key={state} label={`${state}: ${count}`} size="small" />)}
              </Stack>
            </CardContent></Card>
            <Card sx={{ flex: 1 }}><CardContent>
              <Typography variant="overline">Audit events · past 7 days</Typography>
              <Typography variant="h3">{overview.audit.events_last_7_days}</Typography>
              <Typography variant="body2">Count only; sensitive payloads withheld.</Typography>
            </CardContent></Card>
          </Stack>
          <Card><CardContent>
            <Typography variant="h6" gutterBottom>Company Finance</Typography>
            <Alert severity="warning">
              {overview.company_finance.reason} No estimated, tuition, or synthetic
              revenue is represented as actual CROWN receipts.
            </Alert>
            <Typography variant="body2" sx={{ mt: 2 }}>
              External payment provisioning: {overview.external_payments.provisioning_policy}.
              Only none/manual modes are permitted.
            </Typography>
          </CardContent></Card>
          <Card><CardContent>
            <Typography variant="h6">School Directory</Typography>
            <Typography variant="body2" color="text.secondary">
              First {schools?.results?.length || 0} of {schools?.total || 0} records.
              School-specific financial and student information is not exposed.
            </Typography>
            <Box sx={{ overflowX: "auto" }}>
              <Table size="small" aria-label="Platform school directory">
                <TableHead><TableRow>
                  <TableCell>School</TableCell><TableCell>Status</TableCell>
                  <TableCell>Plan metadata</TableCell><TableCell>Payment mode</TableCell>
                </TableRow></TableHead>
                <TableBody>{(schools?.results || []).map((school) => (
                  <TableRow key={school.school_id}>
                    <TableCell>{school.school_name}</TableCell>
                    <TableCell>{school.status}</TableCell>
                    <TableCell>{school.plan_code}</TableCell>
                    <TableCell>{school.payment_provider}</TableCell>
                  </TableRow>
                ))}</TableBody>
              </Table>
            </Box>
          </CardContent></Card>
          <Card><CardContent>
            <Typography variant="h6">Recent Provisioning</Typography>
            <Box sx={{ overflowX: "auto" }}>
              <Table size="small" aria-label="Recent provisioning jobs">
                <TableHead><TableRow>
                  <TableCell>School</TableCell><TableCell>State</TableCell>
                  <TableCell>Progress</TableCell><TableCell>Created</TableCell>
                </TableRow></TableHead>
                <TableBody>{overview.provisioning.recent_jobs.map((job) => (
                  <TableRow key={job.job_id}>
                    <TableCell>{job.school_name}</TableCell>
                    <TableCell>{job.state}</TableCell>
                    <TableCell>{job.progress}%</TableCell>
                    <TableCell>{job.created_at}</TableCell>
                  </TableRow>
                ))}</TableBody>
              </Table>
            </Box>
          </CardContent></Card>
        </Stack>
      )}
    </Container>
  );
}
