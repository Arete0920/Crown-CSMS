import React from "react";
import {
  Drawer,
  Box,
  Typography,
  Divider,
  CircularProgress,
  Chip,
  Stack,
  Alert,
} from "@mui/material";
import SeatingChart from "./SeatingChart";

export default function ClassroomDetailDrawer({ open, onClose, loading, classroom }) {
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
            <Typography variant="body2" sx={{ opacity: 0.8, mb: 1 }}>
              Room: {classroom.room || "—"} • Grade: {classroom.grade_level || "—"} • Teacher:{" "}
              {classroom.homeroom_teacher_name || "—"}
            </Typography>

            <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: "wrap" }}>
              <Chip label={`${(classroom.students || []).length} students`} />
              <Chip label={`${(classroom.assignments || []).length} assignments`} />
              <Chip label={`${(classroom.announcements || []).length} announcements`} />
            </Stack>

            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>
              Announcements
            </Typography>
            {(classroom.announcements || []).slice(0, 4).map((a) => (
              <Box key={a.id} sx={{ mb: 1.5 }}>
                <Typography variant="body2" sx={{ fontWeight: 700 }}>
                  {a.pinned ? "📌 " : ""}{a.title}
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.85 }}>
                  {a.body}
                </Typography>
              </Box>
            ))}
            {(classroom.announcements || []).length === 0 && (
              <Typography variant="body2" sx={{ opacity: 0.7 }}>No announcements.</Typography>
            )}

            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>
              Assignments
            </Typography>
            {(classroom.assignments || []).slice(0, 6).map((a) => (
              <Box key={a.id} sx={{ mb: 1.25 }}>
                <Typography variant="body2" sx={{ fontWeight: 700 }}>
                  {a.title}
                </Typography>
                <Typography variant="caption" sx={{ opacity: 0.8 }}>
                  Due: {a.due_date || "—"} • Points: {a.points} • Status: {a.status}
                </Typography>
              </Box>
            ))}
            {(classroom.assignments || []).length === 0 && (
              <Typography variant="body2" sx={{ opacity: 0.7 }}>No assignments.</Typography>
            )}

            <Divider sx={{ my: 2 }} />

            <SeatingChart seatingChart={classroom.seating_chart} students={classroom.students} />
          </>
        )}
      </Box>
    </Drawer>
  );
}
