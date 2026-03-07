import React, { useEffect, useMemo, useState } from "react";
import { Box, Typography, Grid, Alert, CircularProgress } from "@mui/material";

import { getSelectedSchoolId } from "../utils/authClient";
import { listClassrooms, getClassroom } from "../api/classrooms";
import { KpiStrip } from "../components/dashboard/KpiFlipCard.jsx";

import ClassroomCard from "../components/classroom/ClassroomCard";
import ClassroomDetailDrawer from "../components/classroom/ClassroomDetailDrawer";

/* ── Classrooms KPI flip cards ───────────────────────────────────── */
const CLASSROOMS_KPI = [
  { label: "Classrooms",     value: "18",  trend: null, trendUp: null,
    definition: "Active homeroom classrooms registered for the current school year.",
    dataSource: "Classrooms Module", dataHref: "/classrooms" },
  { label: "Students Rostered", value: "247", trend: null, trendUp: null,
    definition: "Total students rostered across all active classroom sections.",
    dataSource: "Classrooms Module", dataHref: "/classrooms" },
  { label: "Teachers",       value: "14",  trend: null, trendUp: null,
    definition: "Homeroom teachers currently assigned to active classroom sections.",
    dataSource: "Classrooms Module", dataHref: "/classrooms" },
  { label: "Announcements",  value: "4",   trend: null, trendUp: null,
    definition: "Active classroom announcements published to students and parents this week.",
    dataSource: "Classrooms Module", dataHref: "/classrooms" },
];

export default function ClassroomsDashboard() {
  const schoolId = useMemo(() => getSelectedSchoolId(), []);
  const [loading, setLoading] = useState(true);
  const [classrooms, setClassrooms] = useState([]);
  const [error, setError] = useState("");
  const [openId, setOpenId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    let alive = true;
    async function load() {
      setLoading(true);
      setError("");
      try {
        if (!schoolId) {
          setError("School context missing. Select a school or re-login.");
          setClassrooms([]);
          return;
        }
        const data = await listClassrooms({ schoolId });
        const results = data?.results ?? data ?? [];
        if (alive) setClassrooms(results);
      } catch (e) {
        if (alive) setError(e?.message || "Failed to load classrooms.");
      } finally {
        if (alive) setLoading(false);
      }
    }
    load();
    return () => {
      alive = false;
    };
  }, [schoolId]);

  async function openDrawer(id) {
    setOpenId(id);
    setDetail(null);
    if (!schoolId) return;
    setDetailLoading(true);
    try {
      const d = await getClassroom({ id, schoolId });
      setDetail(d);
    } catch (e) {
      setDetail(null);
      setError(e?.message || "Failed to load classroom detail.");
    } finally {
      setDetailLoading(false);
    }
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          Classrooms
        </Typography>
        <Typography variant="body1" sx={{ opacity: 0.8 }}>
          Homerooms, rosters, seating charts, assignments, and announcements (read-only demo).
        </Typography>
      </Box>

      <KpiStrip cards={CLASSROOMS_KPI} />

      {!!error && <Alert severity="warning" sx={{ mb: 2 }}>{error}</Alert>}

      {loading ? (
        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
          <CircularProgress size={22} />
          <Typography>Loading classrooms…</Typography>
        </Box>
      ) : (
        <Grid container spacing={2}>
          {classrooms.map((c) => (
            <Grid item xs={12} md={6} lg={4} key={c.id}>
              <ClassroomCard classroom={c} onOpen={() => openDrawer(c.id)} />
            </Grid>
          ))}
          {classrooms.length === 0 && !error && (
            <Grid item xs={12}>
              <Alert severity="info">No classrooms found for this school.</Alert>
            </Grid>
          )}
        </Grid>
      )}

      <ClassroomDetailDrawer
        open={!!openId}
        onClose={() => setOpenId(null)}
        loading={detailLoading}
        classroom={detail}
      />
    </Box>
  );
}
