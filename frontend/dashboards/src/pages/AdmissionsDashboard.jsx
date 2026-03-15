import { useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardActionArea,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  Drawer,
  Grid,
  List,
  ListItem,
  ListItemText,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import useAdmissionsDashboardData from "../hooks/useAdmissionsDashboardData";
import PageState from "../components/states/PageState.jsx";
import WidgetState from "../components/states/WidgetState.jsx";

function formatMaybeDate(value) {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString();
}

function displayName(row) {
  return (
    row?.student_name ||
    row?.applicant_name ||
    row?.name ||
    row?.full_name ||
    row?.display_name ||
    "Unnamed applicant"
  );
}

function displayMeta(row) {
  const bits = [
    row?.status,
    row?.grade || row?.grade_applied || row?.applied_grade,
    row?.campus,
    row?.program,
  ].filter(Boolean);
  return bits.length ? bits.join(" | ") : "No additional details";
}

function SummaryCard({ title, value, onClick, clickable = true }) {
  const body = (
    <CardContent>
      <Stack spacing={1}>
        <Typography variant="overline" color="text.secondary">
          {title}
        </Typography>
        <Typography variant="h4">{value}</Typography>
      </Stack>
    </CardContent>
  );

  return (
    <Card sx={{ height: "100%" }}>
      {clickable ? (
        <CardActionArea onClick={onClick}>{body}</CardActionArea>
      ) : (
        body
      )}
    </Card>
  );
}

export default function AdmissionsDashboard() {
  const currentYear = new Date().getFullYear();
  const [year, setYear] = useState(String(currentYear));

  const {
    loading,
    drilldownLoading,
    error,
    summary,
    metrics,
    priorityQueue,
    timeline,
    drawerOpen,
    drawerTitle,
    drilldownRows,
    openDrilldown,
    closeDrilldown,
    reload,
  } = useAdmissionsDashboardData(year);

  const years = useMemo(
    () => [
      String(currentYear - 1),
      String(currentYear),
      String(currentYear + 1),
    ],
    [currentYear],
  );

  return (
    <Box sx={{ p: 3 }}>
      <Stack spacing={3}>
        <Stack
          direction={{ xs: "column", md: "row" }}
          spacing={2}
          justifyContent="space-between"
          alignItems={{ xs: "stretch", md: "center" }}
        >
          <Box>
            <Typography variant="h4">Admissions Dashboard</Typography>
            <Typography variant="body2" color="text.secondary">
              Live admissions metrics, queue, and activity.
            </Typography>
          </Box>

          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <TextField
              select
              size="small"
              label="Academic Year"
              value={year}
              onChange={(e) => setYear(e.target.value)}
              sx={{ minWidth: 180 }}
            >
              {years.map((item) => (
                <MenuItem key={item} value={item}>
                  {item}
                </MenuItem>
              ))}
            </TextField>

            <Button variant="outlined" onClick={reload}>
              Refresh
            </Button>
          </Stack>
        </Stack>

        <PageState
          loading={loading}
          error={error}
          empty={!loading && !error && Number(summary?.total || 0) === 0}
          emptyTitle="No admissions data yet"
          emptyMessage="Admissions metrics will appear when applications are created."
          onRetry={reload}
        >
          <>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <WidgetState title="Total Applications">
                  <SummaryCard
                    title="Total Applications"
                    value={summary.total}
                    clickable={false}
                  />
                </WidgetState>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <SummaryCard
                  title="Submitted"
                  value={summary.submitted}
                  onClick={() =>
                    openDrilldown("submitted", "Submitted Applications")
                  }
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <SummaryCard
                  title="Under Review"
                  value={summary.underReview}
                  onClick={() =>
                    openDrilldown("under_review", "Applications Under Review")
                  }
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <SummaryCard
                  title="Admitted"
                  value={summary.admitted}
                  onClick={() =>
                    openDrilldown("admitted", "Admitted Applicants")
                  }
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <SummaryCard
                  title="Waitlisted"
                  value={summary.waitlisted}
                  onClick={() =>
                    openDrilldown("waitlisted", "Waitlisted Applicants")
                  }
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <SummaryCard
                  title="Denied"
                  value={summary.denied}
                  onClick={() => openDrilldown("denied", "Denied Applicants")}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <SummaryCard
                  title="Enrolled"
                  value={summary.enrolled}
                  onClick={() =>
                    openDrilldown("enrolled", "Enrolled Applicants")
                  }
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card sx={{ height: "100%" }}>
                  <CardContent>
                    <Stack spacing={1}>
                      <Typography variant="overline" color="text.secondary">
                        Yield Snapshot
                      </Typography>
                      <Typography variant="h4">
                        {metrics?.yield_rate ||
                          metrics?.yieldRate ||
                          metrics?.yield ||
                          "-"}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Derived from live admissions metrics.
                      </Typography>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Card sx={{ height: "100%" }}>
                  <CardContent>
                    <Stack spacing={2}>
                      <Typography variant="h6">Priority Queue</Typography>
                      <Divider />
                      {priorityQueue.length === 0 ? (
                        <Typography variant="body2" color="text.secondary">
                          No applicants are currently in the priority queue.
                        </Typography>
                      ) : (
                        <List dense>
                          {priorityQueue.map((row, index) => (
                            <ListItem
                              key={row?.id || row?.application_id || index}
                              disableGutters
                            >
                              <ListItemText
                                primary={displayName(row)}
                                secondary={displayMeta(row)}
                              />
                              {row?.status ? (
                                <Chip size="small" label={row.status} />
                              ) : null}
                            </ListItem>
                          ))}
                        </List>
                      )}
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card sx={{ height: "100%" }}>
                  <CardContent>
                    <Stack spacing={2}>
                      <Typography variant="h6">Admissions Timeline</Typography>
                      <Divider />
                      {timeline.length === 0 ? (
                        <Typography variant="body2" color="text.secondary">
                          No recent admissions activity found.
                        </Typography>
                      ) : (
                        <List dense>
                          {timeline.map((row, index) => (
                            <ListItem
                              key={row?.id || row?.event_id || index}
                              disableGutters
                            >
                              <ListItemText
                                primary={
                                  row?.title ||
                                  row?.event ||
                                  row?.label ||
                                  displayName(row)
                                }
                                secondary={formatMaybeDate(
                                  row?.created_at ||
                                    row?.timestamp ||
                                    row?.date ||
                                    row?.event_date,
                                )}
                              />
                            </ListItem>
                          ))}
                        </List>
                      )}
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </>
        </PageState>
      </Stack>

      <Drawer anchor="right" open={drawerOpen} onClose={closeDrilldown}>
        <Box sx={{ width: { xs: 320, sm: 420 }, p: 3 }}>
          <Stack spacing={2}>
            <Typography variant="h6">
              {drawerTitle || "Admissions Drilldown"}
            </Typography>
            <Divider />

            {drilldownLoading ? (
              <Box sx={{ py: 4, display: "flex", justifyContent: "center" }}>
                <CircularProgress />
              </Box>
            ) : drilldownRows.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No matching records found.
              </Typography>
            ) : (
              <List dense>
                {drilldownRows.map((row, index) => (
                  <ListItem
                    key={row?.id || row?.application_id || index}
                    disableGutters
                  >
                    <ListItemText
                      primary={displayName(row)}
                      secondary={displayMeta(row)}
                    />
                  </ListItem>
                ))}
              </List>
            )}

            <Button variant="outlined" onClick={closeDrilldown}>
              Close
            </Button>
          </Stack>
        </Box>
      </Drawer>
    </Box>
  );
}
