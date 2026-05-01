import {
  Alert,
  Box,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  Stack,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import { fetchCompuwerxDisputes } from "../api/compuwerxOps";
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

const COMPUWERX_KPI = [
  { label: 'Open Disputes', value: '—', dataSource: 'CompuWerx' },
  { label: 'Resolved MTD', value: '—', dataSource: 'CompuWerx' },
  { label: 'Pending Review', value: '—', dataSource: 'CompuWerx' },
  { label: 'Escalated', value: '—', dataSource: 'CompuWerx' }
];

export default function CompuwerxDisputesDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [rows, setRows] = useState([]);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetchCompuwerxDisputes();
        setRows(res?.results || []);
      } catch (err) {
        setError(err?.message || "Unable to load disputes.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  if (loading) {
    return (
      <Box sx={{ p: 3, display: "flex", justifyContent: "center" }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <KpiStrip cards={COMPUWERX_KPI} />
      <Stack spacing={2}>
        <Typography variant="h4">Compuwerx Disputes</Typography>
        {error ? <Alert severity="error">{error}</Alert> : null}

        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="h6">Dispute Queue</Typography>
              <Divider />
              {!rows.length ? (
                <Typography color="text.secondary">
                  No disputes found.
                </Typography>
              ) : (
                <List dense>
                  {rows.map((row) => (
                    <ListItem key={row.id} disableGutters>
                      <ListItemText
                        primary={`${row.amount} ${row.currency} • ${row.status}`}
                        secondary={`Dispute ${row.dispute_id} • Invoice ${row.invoice_id || "-"} • Reason ${row.reason || "-"}`}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Stack>
          </CardContent>
        </Card>
      </Stack>
    </Box>
  );
}
