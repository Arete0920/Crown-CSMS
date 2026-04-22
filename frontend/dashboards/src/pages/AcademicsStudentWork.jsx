import { useEffect, useState } from "react";
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
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from "@mui/material";

import { listStudentSubmissions, listMastery, listStudents } from "../lib/academicsApi";

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
          "& .MuiChip-label": { color: "#4d3200", fontWeight: 600 },
          bgcolor: "#f8d58a",
        }}
      />
    );
  }
  if (s === "missing") return <Chip label="Missing" size="small" color="error" />;
  if (s === "submitted") return <Chip label="Submitted" size="small" color="info" />;
  return <Chip label="Assigned" size="small" />;
}

export default function AcademicsStudentWork() {
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const [students, setStudents] = useState([]);
  const [studentId, setStudentId] = useState(
    sessionStorage.getItem("crown.student.id") || ""
  );

  const [submissions, setSubmissions] = useState([]);
  const [mastery, setMastery] = useState([]);

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
        const mas = await listMastery(studentId);

        setSubmissions(Array.isArray(subs) ? subs : subs.results || []);
        setMastery(Array.isArray(mas) ? mas : mas.results || []);
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

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h5" sx={{ mb: 2 }}>
        Student Work
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
            <InputLabel>Student</InputLabel>
            <Select label="Student" value={studentId} onChange={onStudentChange}>
              {students.map((s) => (
                <MenuItem key={s.student_id || s.id} value={s.student_id || s.id}>
                  {s.last_name}, {s.first_name} — Grade {s.grade_level || "?"}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </CardContent>
      </Card>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6">Assignments</Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Assignment</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Score</TableCell>
                <TableCell align="right">Letter</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {submissions.map((s) => (
                <TableRow key={s.id}>
                  <TableCell>{s.assignment_name || s.assignment?.name || "Assignment"}</TableCell>
                  <TableCell>{statusChip(s.status)}</TableCell>
                  <TableCell align="right">{s.grade?.percentage ?? "-"}</TableCell>
                  <TableCell align="right">{s.grade?.letter_grade ?? "-"}</TableCell>
                </TableRow>
              ))}
              {submissions.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4}>
                    <Typography color="text.secondary">No submissions found.</Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6">Mastery</Typography>
          <Divider sx={{ my: 1 }} />
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Objective</TableCell>
                <TableCell>Description</TableCell>
                <TableCell align="right">Level</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {mastery.map((m) => (
                <TableRow key={m.id}>
                  <TableCell>{m.objective_code || m.objective?.objective_code || "-"}</TableCell>
                  <TableCell>{m.objective_description || m.objective?.description || "-"}</TableCell>
                  <TableCell align="right">{m.mastery_level}</TableCell>
                </TableRow>
              ))}
              {mastery.length === 0 && (
                <TableRow>
                  <TableCell colSpan={3}>
                    <Typography color="text.secondary">No mastery records yet.</Typography>
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

