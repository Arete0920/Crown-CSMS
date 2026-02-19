import React, { useEffect, useMemo, useState } from "react";
import {
  Drawer,
  Box,
  Typography,
  Divider,
  IconButton,
  CircularProgress,
  Alert,
  Stack,
  Chip,
  Button,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow
} from "@mui/material";

function normalizeBaseUrl(url) {
  if (!url) return "";
  return url.endsWith("/") ? url.slice(0, -1) : url;
}

function getAuthHeaders() {
  const token = sessionStorage.getItem("crown.jwt.access") || "";
  const schoolId = sessionStorage.getItem("crown.school.id") || "";

  const h = {
    "Content-Type": "application/json",
  };

  if (token) h["Authorization"] = `Bearer ${token}`;
  if (schoolId) h["X-School-Id"] = schoolId;

  return h;
}

export default function GraduationBreakdownDrawer({ open, onClose, studentUuid }) {
  const API_BASE = useMemo(
    () => normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL || ""),
    []
  );

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [data, setData] = useState(null);

  useEffect(() => {
    if (!open || !studentUuid) return;

    const controller = new AbortController();

    async function load() {
      setLoading(true);
      setErr("");
      setData(null);

      try {
        const url = `${API_BASE}/api/v1/graduation/audit/${studentUuid}/breakdown/`;
        const res = await fetch(url, {
          method: "GET",
          headers: getAuthHeaders(),
          signal: controller.signal,
        });

        if (!res.ok) {
          const text = await res.text().catch(() => "");
          throw new Error(`Breakdown failed: ${res.status} ${res.statusText}${text ? ` — ${text}` : ""}`);
        }

        const json = await res.json();
        setData(json);
      } catch (e) {
        if (e.name !== "AbortError") setErr(e.message || String(e));
      } finally {
        setLoading(false);
      }
    }

    load();
    return () => controller.abort();
  }, [open, studentUuid, API_BASE]);

  const creditsLine = data?.credits
    ? `${data.credits.earned} / ${data.credits.required}`
    : "";

  const statusChip = (status) => {
    if (!status) return null;
    const label =
      status === "ON_TRACK" ? "On Track" :
      status === "AT_RISK" ? "At Risk" :
      status === "NOT_ELIGIBLE" ? "Not Eligible" : status;

    return <Chip label={label} size="small" />;
  };

  const exportCsv = () => {
    if (!data) return;

    const rows = [
      ["student_id", data.student_id],
      ["as_of", data.as_of],
      ["status", data.status],
      ["credits_earned", data.credits?.earned],
      ["credits_required", data.credits?.required],
      [],
      ["Requirement", "Required", "Earned", "Met"],
      ...(data.requirements || []).map(r => [r.name, r.required, r.earned, r.met]),
      [],
      ["Notes"],
      ...(data.notes || []).map(n => [n]),
    ];

    const csv = rows.map(r => r.map(v => {
      const s = String(v ?? "");
      return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
    }).join(",")).join("\n");

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `graduation-breakdown-${data.student_id}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  return (
    <Drawer anchor="right" open={open} onClose={onClose}>
      <Box sx={{ width: 520, p: 2 }}>
        <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <Typography variant="h6">Graduation Requirement Breakdown</Typography>
          <IconButton onClick={onClose} aria-label="Close">
            ✕
          </IconButton>
        </Box>

        <Divider sx={{ my: 2 }} />

        {loading && (
          <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {err && <Alert severity="error">{err}</Alert>}

        {data && (
          <Stack spacing={2}>
            <Box sx={{ display: "flex", gap: 1, alignItems: "center", flexWrap: "wrap" }}>
              <Typography variant="subtitle2">Status:</Typography>
              {statusChip(data.status)}
              <Typography variant="subtitle2" sx={{ ml: 2 }}>Credits:</Typography>
              <Chip label={creditsLine} size="small" />
              <Typography variant="caption" sx={{ ml: 2, opacity: 0.8 }}>
                As of: {data.as_of}
              </Typography>
            </Box>

            <Button variant="outlined" onClick={exportCsv}>
              Export Breakdown (CSV)
            </Button>

            <Box>
              <Typography variant="subtitle1" sx={{ mb: 1 }}>Requirements</Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Requirement</TableCell>
                    <TableCell align="right">Required</TableCell>
                    <TableCell align="right">Earned</TableCell>
                    <TableCell align="center">Met</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(data.requirements || []).map((r, idx) => (
                    <TableRow key={idx}>
                      <TableCell>{r.name}</TableCell>
                      <TableCell align="right">{r.required}</TableCell>
                      <TableCell align="right">{r.earned}</TableCell>
                      <TableCell align="center">{r.met ? "✅" : "—"}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>

            {(data.notes || []).length > 0 && (
              <Box>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>Notes</Typography>
                <Stack spacing={1}>
                  {data.notes.map((n, i) => (
                    <Alert key={i} severity="info">{n}</Alert>
                  ))}
                </Stack>
              </Box>
            )}
          </Stack>
        )}
      </Box>
    </Drawer>
  );
}
