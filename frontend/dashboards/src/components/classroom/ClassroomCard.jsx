import React from "react";
import { Card, CardContent, Typography, Box, Button, Chip } from "@mui/material";

export default function ClassroomCard({ classroom, onOpen }) {
  const teacher = classroom?.homeroom_teacher_name || "—";
  const count = classroom?.student_count ?? 0;

  return (
    <Card variant="outlined" sx={{ borderRadius: 3 }}>
      <CardContent>
        <Box sx={{ display: "flex", justifyContent: "space-between", gap: 2 }}>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              {classroom?.name}
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.8 }}>
              Room: {classroom?.room || "—"} • Grade: {classroom?.grade_level || "—"}
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              Teacher: {teacher}
            </Typography>
          </Box>

          <Box sx={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 1 }}>
            <Chip label={`${count} students`} />
            <Button size="small" variant="contained" onClick={onOpen}>
              Open
            </Button>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}
