import React, { useEffect, useState } from "react";
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
} from "@mui/material";

import { listStudentSubmissions, listMastery } from "../lib/academicsApi";

function statusChip(status) {
  const s = (status || "").toLowerCase();
  if (s === "graded") return <Chip label="Graded" size="small" color="success" />;
  if (s === "late") return <Chip label="Late" size="small" color="warning" />;
  if (s === "missing") return <Chip label="Missing" size="small" color="error" />;
  if (s === "submitted") return <Chip label="Submitted" size="small" color="info" />;
  return <Chip label="Assigned" size="small" />;
}

export default function AcademicsStudentWork() {
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const [submissions, setSubmissions] = useState([]);
  const [mastery, setMastery] = useState([]);

  // Demo: pick a student id from sessionStorage if you store it; otherwise hardcode later.
  const studentId =
    sessionStorage.getItem("crown.student.id") ||
    sessionStorage.getItem("studentId") ||
    "";

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setErr("");

        if (!studentId) {
          setErr("No student id in sessionStorage (crown.student.id). For demo, set it or add a picker.");
          return;
        }

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
