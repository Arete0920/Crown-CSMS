import React, { useState } from "react";
import {
  Drawer,
  Box,
  Typography,
  Divider,
  CircularProgress,
  Chip,
  Stack,
  Alert,
  Tabs,
  Tab,
} from "@mui/material";
import SeatingChart from "./SeatingChart";

function formatDate(dateStr) {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function getAssignmentStatusColor(dueDate) {
  if (!dueDate) return "default";
  const today = new Date().toISOString().split("T")[0];
  if (dueDate < today) return "error";
  if (dueDate === today) return "warning";
  return "success";
}

function getAssignmentStatusLabel(dueDate) {
  if (!dueDate) return "—";
  const today = new Date().toISOString().split("T")[0];
  if (dueDate < today) return "Overdue";
  if (dueDate === today) return "Due Today";
  return "Upcoming";
}

function TabContent({ tabIndex, classroom }) {
  if (tabIndex === 0) {
    // Overview
    return (
      <>
        <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: "wrap" }}>
          <Chip label={`${(classroom.students || []).length} students`} />
          <Chip label={`${(classroom.assignments || []).length} assignments`} />
          <Chip label={`${(classroom.announcements || []).length} announcements`} />
        </Stack>
      </>
    );
  }

  if (tabIndex === 1) {
    // Roster
    return (
      <>
        <Typography variant="body2" sx={{ opacity: 0.8, mb: 2 }}>
          {(classroom.students || []).length} students enrolled
        </Typography>
        {(classroom.students || []).length === 0 ? (
          <Typography variant="body2" sx={{ opacity: 0.7 }}>No students enrolled.</Typography>
        ) : (
          <Stack spacing={0.5}>
            {(classroom.students || []).map((s) => (
              <Typography key={s.id} variant="body2">
                • {s.name}
              </Typography>
            ))}
          </Stack>
        )}
      </>
    );
  }

  if (tabIndex === 2) {
    // Assignments
    return (
      <>
        {(classroom.assignments || []).length === 0 ? (
          <Typography variant="body2" sx={{ opacity: 0.7 }}>No assignments.</Typography>
        ) : (
          <Stack spacing={1.5}>
            {(classroom.assignments || []).map((a) => (
              <Box key={a.id} sx={{ p: 1.5, bgcolor: "#f5f5f5", borderRadius: 1 }}>
                <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "start", gap: 1, mb: 0.5 }}>
                  <Typography variant="body2" sx={{ fontWeight: 700, flex: 1 }}>
                    {a.title}
                  </Typography>
                  <Chip
                    label={getAssignmentStatusLabel(a.due_date)}
                    size="small"
                    color={getAssignmentStatusColor(a.due_date)}
                    variant="outlined"
                  />
                </Box>
                <Typography variant="caption" sx={{ opacity: 0.75 }}>
                  {a.description}
                </Typography>
                <Box sx={{ display: "flex", justifyContent: "space-between", mt: 0.75 }}>
                  <Typography variant="caption" sx={{ opacity: 0.7 }}>
                    Due: {formatDate(a.due_date)}
                  </Typography>
                  <Typography variant="caption" sx={{ opacity: 0.7 }}>
                    {a.points} pts
                  </Typography>
                </Box>
              </Box>
            ))}
          </Stack>
        )}
      </>
    );
  }

  if (tabIndex === 3) {
    // Announcements
    return (
      <>
        {(classroom.announcements || []).length === 0 ? (
          <Typography variant="body2" sx={{ opacity: 0.7 }}>No announcements.</Typography>
        ) : (
          <Stack spacing={1.5}>
            {(classroom.announcements || []).map((a) => (
              <Box key={a.id} sx={{ p: 1.5, bgcolor: a.pinned ? "#fffacd" : "#f5f5f5", borderRadius: 1 }}>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
                  <Typography variant="body2" sx={{ fontWeight: 700, flex: 1 }}>
                    {a.pinned ? "📌 " : ""}{a.title}
                  </Typography>
                </Box>
                <Typography variant="caption" sx={{ opacity: 0.75, display: "block" }}>
                  {a.body}
                </Typography>
                <Typography variant="caption" sx={{ opacity: 0.65, mt: 0.5, display: "block" }}>
                  {formatDate(a.created_at)}
                </Typography>
              </Box>
            ))}
          </Stack>
        )}
      </>
    );
  }

  return null;
}

export default function ClassroomDetailDrawer({ open, onClose, loading, classroom }) {
  const [tabIndex, setTabIndex] = useState(0);

  return (
    <Drawer anchor="right" open={open} onClose={onClose}>
      <Box sx={{ width: { xs: 360, sm: 520 }, p: 3 }}>
        {loading ? (
          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            <CircularProgress size={22} />
            <Typography>Loading…</Typography>
          </Box>
        ) : !classroom ? (
          <Alert severity="info">No classroom selected.</Alert>
        ) : (
          <>
            <Typography variant="h5" sx={{ fontWeight: 800 }}>
              {classroom.name}
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.8, mb: 2 }}>
              Room: {classroom.room || "—"} • Grade: {classroom.grade_level || "—"} • Teacher:{" "}
              {classroom.homeroom_teacher_name || "—"}
            </Typography>

            <Tabs value={tabIndex} onChange={(e, v) => setTabIndex(v)} sx={{ mb: 2 }}>
              <Tab label="Overview" />
              <Tab label="Roster" />
              <Tab label="Assignments" />
              <Tab label="Announcements" />
            </Tabs>

            <TabContent tabIndex={tabIndex} classroom={classroom} />

            {tabIndex === 0 && (
              <>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                  Seating Chart
                </Typography>
                <SeatingChart seatingChart={classroom.seating_chart} students={classroom.students} />
              </>
            )}
          </>
        )}
      </Box>
    </Drawer>
  );
}
