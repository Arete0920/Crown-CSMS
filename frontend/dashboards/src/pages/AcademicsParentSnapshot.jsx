import React, { useEffect, useMemo, useState } from "react";
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
} from "@mui/material";

import { listStudentSubmissions, listTranscript } from "../lib/academicsApi";

function statusChip(status) {
  const s = (status || "").toLowerCase();
  if (s === "missing") return <Chip label="Missing" size="small" color="error" />;
  if (s === "late") return <Chip label="Late" size="small" color="warning" />;
  return <Chip label="OK" size="small" color="success" />;
}

export default function AcademicsParentSnapshot() {
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const [submissions, setSubmissions] = useState([]);
  const [transcript, setTranscript] = useState([]);

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
