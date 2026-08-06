import { Card, CardContent, Typography, Box } from "@mui/material";

export default function BoardKpiTile({ label, value, meta }) {
  return (
    <Card>
      <CardContent>
        <Typography variant="body2" sx={{ mb: 0.5 }}>
          {label}
        </Typography>
        <Typography variant="h2" sx={{ lineHeight: 1.1 }}>
          {value}
        </Typography>
        {meta ? (
          <Box sx={{ mt: 1 }}>
            <Typography variant="body2">{meta}</Typography>
          </Box>
        ) : null}
      </CardContent>
    </Card>
  );
}
