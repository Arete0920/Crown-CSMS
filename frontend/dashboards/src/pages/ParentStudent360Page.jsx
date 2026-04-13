import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Stack,
  Chip,
  LinearProgress,
  Alert
} from "@mui/material";
import GraduationBreakdownDrawer from "../components/student360/GraduationBreakdownDrawer.jsx";

function normalizeBaseUrl(url) {
  if (!url) return "";
  return url.endsWith("/") ? url.slice(0, -1) : url;
}

function getAuthHeaders() {
  const token = sessionStorage.getItem("crown.jwt.access") || "";
  const schoolId = sessionStorage.getItem("crown.school.id") || "";

  const h = { "Content-Type": "application/json" };
  if (token) h["Authorization"] = `Bearer ${token}`;
  if (schoolId) h["X-School-Id"] = schoolId;
  return h;
}

export default function ParentStudent360Page() {
  const { id } = useParams(); // uuid
  const studentUuid = id;

  const API_BASE = useMemo(
    () => normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL || ""),
    []
  );

  const [gradOpen, setGradOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [breakdown, setBreakdown] = useState(null);

  useEffect(() => {
    if (!studentUuid) return;
    const controller = new AbortController();

    async function loadTile() {
      setLoading(true);
      setErr("");
      try {
        const url = `${API_BASE}/api/v1/graduation/audit/${studentUuid}/breakdown/`;
        const res = await globalThis.fetch(url, {
          method: "GET",
          headers: getAuthHeaders(),
          signal: controller.signal,
        });

        if (!res.ok) {
          const text = await res.text().catch(() => "");
          throw new Error(`Graduation breakdown failed: ${res.status} ${res.statusText}${text ? `  ${text}` : ""}`);
        }

        const json = await res.json();
        setBreakdown(json);
      } catch (e) {
        if (e.name !== "AbortError") setErr(e.message || String(e));
      } finally {
        setLoading(false);
      }
    }

    loadTile();
    return () => controller.abort();
  }, [studentUuid, API_BASE]);

  const credits = breakdown?.credits
    ? `${breakdown.credits.earned} / ${breakdown.credits.required}`
    : "";

  const statusLabel =
    breakdown?.status === "ON_TRACK" ? "On Track" :
    breakdown?.status === "AT_RISK" ? "At Risk" :
    breakdown?.status === "NOT_ELIGIBLE" ? "Not Eligible" :
    (breakdown?.status || "");

  // For a simple progress bar, clamp 0..100
  const pct = (() => {
    const e = Number(breakdown?.credits?.earned ?? 0);
    const r = Number(breakdown?.credits?.required ?? 0);
    if (!r || r <= 0) return 0;
    const p = Math.round((e / r) * 100);
    return Math.max(0, Math.min(100, p));
  })();

  return (
    <Box sx={{ p: 3 }}>
      <Stack spacing={2}>
        <Box>
          <Typography variant="h5">Parent View</Typography>
          <Typography variant="body2" sx={{ opacity: 0.8 }}>
            Student360 (read-only)
          </Typography>
        </Box>

        {err && <Alert severity="error">{err}</Alert>}

        <Card
          onClick={() => setGradOpen(true)}
          sx={{
            cursor: "pointer",
            maxWidth: 720,
          }}
        >
          <CardContent>
            <Stack spacing={1}>
              <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                <Typography variant="h6">Graduation</Typography>
                <Chip size="small" label={statusLabel} />
                <Chip size="small" label={`Credits: ${credits}`} />
              </Stack>

              {loading ? (
                <LinearProgress />
              ) : (
                <LinearProgress variant="determinate" value={pct} />
              )}

              <Typography variant="caption" sx={{ opacity: 0.8 }}>
                Click to view breakdown, export CSV, or print a board-ready audit.
              </Typography>
            </Stack>
          </CardContent>
        </Card>

        <GraduationBreakdownDrawer
          open={gradOpen}
          onClose={() => setGradOpen(false)}
          studentUuid={studentUuid}
        />
      </Stack>
    </Box>
  );
}

