import { Card, CardContent, Typography, Divider, Box } from "@mui/material";

export default function BoardCard({ title, subtitle, right, children }) {
  return (
    <Card>
      <CardContent>
        <Box
          sx={{
            display: "flex",
            alignItems: "baseline",
            justifyContent: "space-between",
            gap: 2,
          }}
        >
          <Box>
            <Typography variant="h3">{title}</Typography>
            {subtitle ? (
              <Typography variant="body2" sx={{ mt: 0.25 }}>
                {subtitle}
              </Typography>
            ) : null}
          </Box>
          {right ? <Box>{right}</Box> : null}
        </Box>
        <Divider sx={{ my: 2 }} />
        {children}
      </CardContent>
    </Card>
  );
}
