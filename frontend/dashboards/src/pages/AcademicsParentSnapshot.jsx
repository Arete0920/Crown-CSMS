import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Stack,
  Alert,
  CircularProgress,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
} from "@mui/material";

import { listStudentSubmissions, listTranscript, listStudents } from "../lib/academicsApi";

function statusChip(status) {
  const s = (status || "").toLowerCase();
  if (s === "missing") return <Chip label="Missing" size="small" color="error" />;
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
  return <Chip label="OK" size="small" color="success" />;
}

export default function AcademicsParentSnapshot() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const [students, setStudents] = useState([]);
  const [studentId, setStudentId] = useState(
    sessionStorage.getItem("crown.student.id") || ""
  );

  const [submissions, setSubmissions] = useState([]);
  const [transcript, setTranscript] = useState([]);

  // Load student list on mount
  useEffect(() => {
    (async () => {
      try {
        const data = await listStudents();
        const list = Array.isArray(data) ? data : data.results || [];
        setStudents(list);
        // Auto-select first student if none stored
        setStudentId((current) => {
          if (current || list.length === 0) return current;
          const firstId = list[0].student_id || list[0].id;
          sessionStorage.setItem("crown.student.id", firstId);
          return firstId;
        });
      } catch (e) {
        setErr(e.message || String(e));
      }
    })();
  }, []);

  // Load data when student changes
  useEffect(() => {
    if (!studentId) return;
    (async () => {
      try {
        setLoading(true);
        setErr("");

        const subs = await listStudentSubmissions(studentId);
        const tr = await listTranscript(studentId);

        setSubmissions(Array.isArray(subs) ? subs : subs.results || []);
        setTranscript(Array.isArray(tr) ? tr : tr.results || []);
      } catch (e) {
        setErr(e.message || String(e));
      } finally {
        setLoading(false);
      }
    })();
  }, [studentId]);

  function onStudentChange(e) {
    const id = e.target.value;
    setStudentId(id);
    sessionStorage.setItem("crown.student.id", id);
  }

  const missing = useMemo(
    () => submissions.filter((s) => (s.status || "").toLowerCase() === "missing"),
    [submissions]
  );

  const late = useMemo(
    () => submissions.filter((s) => (s.status || "").toLowerCase() === "late"),
    [submissions]
  );

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h5" sx={{ mb: 2 }}>
        Parent Snapshot
      </Typography>

      {loading && (
        <Stack direction="row" spacing={2} alignItems="center">
          <CircularProgress size={20} />
          <Typography>Loading…</Typography>
        </Stack>
      )}

      {err && <Alert severity="warning" sx={{ mb: 2 }}>{err}</Alert>}

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <FormControl fullWidth>
            <InputLabel>Select Child</InputLabel>
            <Select label="Select Child" value={studentId} onChange={onStudentChange}>
              {students.map((s) => (
                <MenuItem key={s.student_id || s.id} value={s.student_id || s.id}>
                  {s.last_name}, {s.first_name} — Grade {s.grade_level || "?"}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          {studentId && (
            <Button
              variant="contained"
              onClick={() => navigate(`/parent/students/${studentId}`)}
              sx={{ mt: 2 }}
              fullWidth
            >
              View Full Student360
            </Button>
          )}
        </CardContent>
      </Card>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6">Alerts</Typography>
          <Typography sx={{ mt: 1 }}>
            Missing: <strong>{missing.length}</strong> &nbsp; | &nbsp; Late:{" "}
            <strong>{late.length}</strong>
          </Typography>

          <Table size="small" sx={{ mt: 1 }}>
            <TableHead>
              <TableRow>
                <TableCell>Assignment</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {missing.slice(0, 8).map((s) => (
                <TableRow key={s.id}>
                  <TableCell>{s.assignment_name || s.assignment?.name || "Assignment"}</TableCell>
                  <TableCell>{statusChip(s.status)}</TableCell>
                </TableRow>
              ))}
              {missing.length === 0 && (
                <TableRow>
                  <TableCell colSpan={2}>
                    <Typography color="text.secondary">No missing work.</Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6">Transcript Preview</Typography>
          <Table size="small" sx={{ mt: 1 }}>
            <TableHead>
              <TableRow>
                <TableCell>Course</TableCell>
                <TableCell>Term</TableCell>
                <TableCell align="right">Credit</TableCell>
                <TableCell align="right">Grade</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {transcript.map((t) => (
                <TableRow key={t.id}>
                  <TableCell>{t.course_name || t.course?.name || "-"}</TableCell>
                  <TableCell>{t.term_name || t.term?.name || "-"}</TableCell>
                  <TableCell align="right">{t.credit_value ?? "-"}</TableCell>
                  <TableCell align="right">{t.final_letter_grade ?? "-"}</TableCell>
                </TableRow>
              ))}
              {transcript.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4}>
                    <Typography color="text.secondary">
                      No transcript entries yet (demo-safe).
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </Box>
  );
}

