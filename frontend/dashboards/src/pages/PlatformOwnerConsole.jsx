import { useEffect, useState } from "react";
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
  const [page, setPage] = useState(1);
  const [refreshVersion, setRefreshVersion] = useState(0);

  // An owner may oversee hundreds of schools. Retrieve only the requested
  // server page and cancel stale requests on navigation/unmount.
  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      setLoading(true);
      setError("");
      try {
        const [summary, list] = await Promise.all([
          authenticatedJson("/api/platform/overview", {
            omitSchoolContext: true,
            signal: controller.signal,
          }),
          authenticatedJson("/api/platform/schools/list", {
            omitSchoolContext: true,
            query: { page, per_page: 50 },
            signal: controller.signal,
          }),
        ]);
        if (controller.signal.aborted) return;
        setOverview(summary);
        setSchools(list);
      } catch (caught) {
        if (controller.signal.aborted) return;
        setOverview(null);
        setSchools(null);
        setError(
          caught?.status === 401 || caught?.status === 403
            ? "Access denied: active platform-operator authority is required."
            : "Unable to load operator records. Verify backend availability and your session.",
        );
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    void load();
    return () => controller.abort();
  }, [page, refreshVersion]);

  const refresh = () => setRefreshVersion((version) => version + 1);
  const pageSize = schools?.per_page || 50;
  const totalSchools = schools?.total || 0;
  const displayedPage = schools?.page || page;
  const pageCount = Math.max(1, Math.ceil(totalSchools / pageSize));
  const firstSchool = totalSchools > 0 ? (displayedPage - 1) * pageSize + 1 : 0;
  const lastSchool = schools?.results?.length
    ? firstSchool + schools.results.length - 1
    : 0;

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
      {!loading && overview && (
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
            <Typography variant="h6" gutterBottom>Backend queues · database pulse</Typography>
            {overview.outbox?.data_state === "available" ? (
              <Stack spacing={1}>
                <Typography variant="body2">
                  Outbox pending: {overview.outbox.pending} · Due: {overview.outbox.due} ·
                  Deferred: {overview.outbox.deferred} · Failed: {overview.outbox.failed} ·
                  Dead: {overview.outbox.dead}
                </Typography>
                <Typography variant="body2">
                  Oldest due: {overview.outbox.oldest_due_age_seconds == null
                    ? "none" : `${overview.outbox.oldest_due_age_seconds} seconds`}
                  {" · "}Oldest queued provisioning: {overview.provisioning?.oldest_queued_age_seconds == null
                    ? "none" : `${overview.provisioning.oldest_queued_age_seconds} seconds`}
                </Typography>
                {overview.outbox.due > 0 && <Alert severity="warning">
                  Due messages await processing. Verify worker and broker before diagnosing lag.
                </Alert>}
                {(overview.outbox.failed > 0 || overview.outbox.dead > 0) && (
                  <Alert severity="warning">
                    Failed or dead outbox records require operator review.
                    Database state alone does not establish delivery or worker health.
                  </Alert>
                )}
                <Typography variant="caption" color="text.secondary">
                  Worker and beat: not verified. Database records do not prove delivery.
                </Typography>
              </Stack>
            ) : <Alert severity="warning">Outbox backlog unavailable; runtime health unknown.</Alert>}
          </CardContent></Card>
          <Card><CardContent>
            <Typography variant="h6" gutterBottom>Support Operations</Typography>
            {overview.support?.data_state === "available" ? (
              <Stack spacing={1}>
                <Typography variant="body2">
                  Unresolved tickets: {overview.support.unresolved} · Open: {overview.support.open} · Escalated: {overview.support.escalated}
                </Typography>
                <Typography variant="body2">
                  Critical unresolved: {overview.support.critical_unresolved} · Overdue open: {overview.support.overdue_open}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Aggregated current-database records only. Alert delivery is not certified.
                  No student details or ticket contents are displayed.
                </Typography>
              </Stack>
            ) : (
              <Alert severity="warning">Support operational metrics unavailable; not verified.</Alert>
            )}
          </CardContent></Card>
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
              Showing {firstSchool}–{lastSchool} of {totalSchools} records.
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
            <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mt: 2 }}>
              <Button
                variant="outlined"
                onClick={() => setPage((current) => Math.max(1, current - 1))}
                disabled={loading || displayedPage <= 1}
              >
                Previous page
              </Button>
              <Typography variant="body2" aria-live="polite">
                Page {displayedPage} of {pageCount}
              </Typography>
              <Button
                variant="outlined"
                onClick={() => setPage((current) => current + 1)}
                disabled={loading || displayedPage >= pageCount}
              >
                Next page
              </Button>
            </Stack>
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
