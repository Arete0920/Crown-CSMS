import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  Drawer,
  List,
  ListItem,
  ListItemText,
  Stack,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import {
  fetchCompuwerxPayoutBatchDetail,
  fetchCompuwerxPayoutBatches,
} from "../api/compuwerxOps";

export default function CompuwerxPayoutReconciliation() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [rows, setRows] = useState([]);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [detail, setDetail] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetchCompuwerxPayoutBatches();
        setRows(res?.results || []);
      } catch (err) {
        setError(err?.message || "Unable to load payout batches.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  async function openDetail(batchId) {
    try {
      const res = await fetchCompuwerxPayoutBatchDetail(batchId);
      setDetail(res);
      setDrawerOpen(true);
    } catch (err) {
      setError(err?.message || "Unable to load payout batch detail.");
    }
  }

  if (loading) {
    return (
      <Box sx={{ p: 3, display: "flex", justifyContent: "center" }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Stack spacing={2}>
        <Typography variant="h4">Compuwerx Payout Reconciliation</Typography>
        {error ? <Alert severity="error">{error}</Alert> : null}

        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="h6">Payout Batches</Typography>
              <Divider />
              {!rows.length ? (
                <Typography color="text.secondary">
                  No payout batches found.
                </Typography>
              ) : (
                <List dense>
                  {rows.map((row) => (
                    <ListItem
                      key={row.id}
                      disableGutters
                      secondaryAction={
                        <Button size="small" onClick={() => openDetail(row.id)}>
                          Open
                        </Button>
                      }
                    >
                      <ListItemText
                        primary={`${row.net_amount} net • ${row.status}`}
                        secondary={`Payout ${row.payout_id} • Entries ${row.entry_count}/${row.expected_payment_count} • Entry Net ${row.entry_net_total}`}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Stack>
          </CardContent>
        </Card>
      </Stack>

      <Drawer
        anchor="right"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      >
        <Box sx={{ width: 420, p: 3 }}>
          <Stack spacing={2}>
            <Typography variant="h6">Payout Detail</Typography>
            <Divider />
            {!detail?.batch ? (
              <Typography color="text.secondary">
                No payout detail loaded.
              </Typography>
            ) : (
              <>
                <Typography variant="body2">
                  Payout ID: {detail.batch.payout_id}
                </Typography>
                <Typography variant="body2">
                  Net Amount: {detail.batch.net_amount}
                </Typography>
                <Typography variant="body2">
                  Fee Amount: {detail.batch.fee_amount}
                </Typography>
                <Typography variant="body2">
                  Status: {detail.batch.status}
                </Typography>
                <Divider />
                {!detail.entries?.length ? (
                  <Typography color="text.secondary">
                    No entries found.
                  </Typography>
                ) : (
                  <List dense>
                    {detail.entries.map((entry) => (
                      <ListItem key={entry.id} disableGutters>
                        <ListItemText
                          primary={`${entry.net_amount} ${entry.currency}`}
                          secondary={`Invoice ${entry.invoice_id || "-"} • Household ${entry.household_id || "-"} • Payment ${entry.provider_payment_id || "-"}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                )}
              </>
            )}
          </Stack>
        </Box>
      </Drawer>
    </Box>
  );
}
