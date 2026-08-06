import { useEffect, useMemo, useState } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  TextField,
  Button,
  Chip,
  Stack,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from "@mui/material";

import {
  listSections,
  listAssignments,
  listSubmissions,
  gradeSubmission,
} from "../lib/academicsApi";

function statusChip(status) {
  const s = (status || "").toLowerCase();
  if (s === "graded") return <Chip label="Graded" size="small" color="success" />;
  if (s === "late") {
    return (
      <Chip
        label="Late"
        size="small"
        color="warning"
        sx={{
          "& .MuiChip-label": { color: "var(--crown-compat-color-7705d1144a)", fontWeight: 600 },
          bgcolor: "var(--crown-compat-color-a9c8c941d5)",
        }}
      />
    );
  }
  if (s === "missing") return <Chip label="Missing" size="small" color="error" />;
  if (s === "submitted") return <Chip label="Submitted" size="small" color="info" />;
  return <Chip label="Assigned" size="small" />;
}

export default function AcademicsTeacherGrading() {
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const [sections, setSections] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [submissions, setSubmissions] = useState([]);

  const [sectionId, setSectionId] = useState("");
  const [assignmentId, setAssignmentId] = useState("");

  // draft scores: { submissionId: "95" }
  const [draftScores, setDraftScores] = useState({});
  const [savingId, setSavingId] = useState("");

  // Status filter for demo convenience
  const [statusFilter, setStatusFilter] = useState("all");

  async function loadSections() {
    const data = await listSections();
    setSections(Array.isArray(data) ? data : data.results || []);
  }

  async function loadAssignments(secId) {
    const data = await listAssignments(secId);
    setAssignments(Array.isArray(data) ? data : data.results || []);
  }

  async function loadSubmissions(aId) {
    const data = await listSubmissions(aId);
    setSubmissions(Array.isArray(data) ? data : data.results || []);
  }

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setErr("");
        await loadSections();
      } catch (e) {
        setErr(e.message || String(e));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (!sectionId) return;
    (async () => {
      try {
        setErr("");
        setAssignments([]);
        setAssignmentId("");
        setSubmissions([]);
        await loadAssignments(sectionId);
      } catch (e) {
        setErr(e.message || String(e));
      }
    })();
  }, [sectionId]);

  useEffect(() => {
    if (!assignmentId) return;
    (async () => {
      try {
        setErr("");
        setSubmissions([]);
        await loadSubmissions(assignmentId);
      } catch (e) {
        setErr(e.message || String(e));
      }
    })();
  }, [assignmentId]);

  const assignmentMap = useMemo(() => {
    const m = new Map();
    assignments.forEach((a) => m.set(a.id, a));
    return m;
  }, [assignments]);

  const filteredSubmissions = useMemo(() => {
    if (statusFilter === "all") return submissions;
    return submissions.filter(
      (s) => (s.status || "").toLowerCase() === statusFilter
    );
  }, [submissions, statusFilter]);

  function autoFillSubmitted() {
    const updates = {};
    submissions.forEach((sub) => {
      if ((sub.status || "").toLowerCase() === "submitted") {
        updates[sub.id] = "100";
      }
    });
    setDraftScores((prev) => ({ ...prev, ...updates }));
  }

  async function onGradeRow(sub) {
    const scoreStr = draftScores[sub.id];
    const score = Number(scoreStr);
    if (!Number.isFinite(score)) {
      setErr("Enter a numeric score before grading.");
      return;
    }

    try {
      setSavingId(sub.id);
      setErr("");
      await gradeSubmission(sub.id, score, "");
      await loadSubmissions(assignmentId);
    } catch (e) {
      setErr(e.message || String(e));
    } finally {
      setSavingId("");
    }
  }

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h5" sx={{ mb: 2 }}>
        Teacher Grading
      </Typography>

      {loading && (
        <Stack direction="row" spacing={2} alignItems="center">
          <CircularProgress size={20} />
          <Typography>Loading…</Typography>
        </Stack>
      )}

      {err && <Alert severity="error" sx={{ mb: 2 }}>{err}</Alert>}

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
            <FormControl fullWidth>
              <InputLabel>Section</InputLabel>
              <Select
                label="Section"
                value={sectionId}
                onChange={(e) => setSectionId(e.target.value)}
              >
                {sections.map((s) => (
                  <MenuItem key={s.id} value={s.id}>
                    {s.course_name || s.course?.name || s.name || s.term || s.id}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl fullWidth disabled={!sectionId}>
              <InputLabel>Assignment</InputLabel>
              <Select
                label="Assignment"
                value={assignmentId}
                onChange={(e) => setAssignmentId(e.target.value)}
              >
                {assignments.map((a) => (
                  <MenuItem key={a.id} value={a.id}>
                    {a.name || a.title || a.id}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>

          {assignmentId && (
            <Typography variant="body2" sx={{ mt: 2, color: "text.secondary" }}>
              Selected: {assignmentMap.get(assignmentId)?.name || assignmentId}
            </Typography>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Stack direction={{ xs: "column", md: "row" }} spacing={2} alignItems="center" sx={{ mb: 2 }}>
            <Typography variant="h6" sx={{ flexGrow: 1 }}>
              Submissions
            </Typography>
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Filter</InputLabel>
              <Select
                label="Filter"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="submitted">Submitted</MenuItem>
                <MenuItem value="missing">Missing</MenuItem>
                <MenuItem value="late">Late</MenuItem>
                <MenuItem value="graded">Graded</MenuItem>
              </Select>
            </FormControl>
          </Stack>

          <Accordion disableGutters sx={{ mb: 2, boxShadow: "none", border: "1px solid", borderColor: "divider" }}>
            <AccordionSummary expandIcon={<span style={{ fontSize: "1.2rem" }}>{"\u25BC"}</span>}>
              <Typography variant="body2" color="text.secondary">Demo Tools</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Button
                variant="outlined"
                size="small"
                onClick={autoFillSubmitted}
                disabled={submissions.length === 0}
              >
                Auto-fill 100 for &ldquo;Submitted&rdquo;
              </Button>
            </AccordionDetails>
          </Accordion>

          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Student</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Score</TableCell>
                <TableCell align="right">Action</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredSubmissions.map((sub) => (
                <TableRow key={sub.id}>
                  <TableCell>
                    {sub.student_name || sub.student?.name || sub.student || "Student"}
                  </TableCell>
                  <TableCell>{statusChip(sub.status)}</TableCell>
                  <TableCell align="right" sx={{ width: 160 }}>
                    <TextField
                      size="small"
                      inputProps={{ inputMode: "numeric" }}
                      value={draftScores[sub.id] ?? ""}
                      onChange={(e) =>
                        setDraftScores((prev) => ({ ...prev, [sub.id]: e.target.value }))
                      }
                      placeholder="e.g., 95"
                    />
                  </TableCell>
                  <TableCell align="right" sx={{ width: 140 }}>
                    <Button
                      variant="contained"
                      size="small"
                      disabled={!assignmentId || savingId === sub.id}
                      onClick={() => onGradeRow(sub)}
                    >
                      {savingId === sub.id ? "Saving…" : "Grade"}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}

              {filteredSubmissions.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4}>
                    <Typography color="text.secondary">
                      Select a section and assignment to view submissions.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>

          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Demo behavior: grading a submission updates mastery automatically (latest evidence replaces).
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}

