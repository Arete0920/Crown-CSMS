import { useEffect, useState } from "react";
import { crownApiClient } from "../../api/client";
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
  TableRow,
} from "@mui/material";

export default function GraduationBreakdownDrawer({ open, onClose, studentUuid }) {
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [data, setData] = useState(null);

  useEffect(() => {
    if (!open || !studentUuid) return undefined;

    const controller = new AbortController();

    async function load() {
      setLoading(true);
      setErr("");
      setData(null);

      try {
        const response = await crownApiClient.request({
          url: `/api/v1/graduation/audit/${studentUuid}/breakdown/`,
          method: "GET",
          signal: controller.signal,
        });

        setData(response.data);
      } catch (error) {
        if (error.name !== "AbortError") {
          setErr(error.message || String(error));
        }
      } finally {
        setLoading(false);
      }
    }

    load();
    return () => controller.abort();
  }, [open, studentUuid]);

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
      ...(data.requirements || []).map((requirement) => [requirement.name, requirement.required, requirement.earned, requirement.met]),
      [],
      ["Notes"],
      ...(data.notes || []).map((note) => [note]),
    ];

    const csv = rows.map((row) => row.map((value) => {
      const stringValue = String(value ?? "");
      return /[",\n]/.test(stringValue) ? `"${stringValue.replace(/"/g, '""')}"` : stringValue;
    }).join(",")).join("\n");

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const anchor = document.createElement("a");
    anchor.href = URL.createObjectURL(blob);
    anchor.download = `graduation-breakdown-${data.student_id}.csv`;
    anchor.click();
    URL.revokeObjectURL(anchor.href);
  };

  return (
    <Drawer anchor="right" open={open} onClose={onClose}>
      <Box sx={{ width: 520, p: 2 }}>
        <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <Typography variant="h6">Graduation Requirement Breakdown</Typography>
          <IconButton onClick={onClose} aria-label="Close">
            X
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
                  {(data.requirements || []).map((requirement, index) => (
                    <TableRow key={index}>
                      <TableCell>{requirement.name}</TableCell>
                      <TableCell align="right">{requirement.required}</TableCell>
                      <TableCell align="right">{requirement.earned}</TableCell>
                      <TableCell align="center">{requirement.met ? "Yes" : "-"}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>

            {(data.notes || []).length > 0 && (
              <Box>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>Notes</Typography>
                <Stack spacing={1}>
                  {data.notes.map((note, index) => (
                    <Alert key={index} severity="info">{note}</Alert>
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