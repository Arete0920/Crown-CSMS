import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useCallback, useEffect, useState } from "react";
import {
  createManualPayoutBankMatch,
  fetchBankStatementImports,
  fetchPayoutBankMatches,
  fetchUnmatchedBankEntries,
  runAutoPayoutBankMatch,
  uploadBankStatementCsv,
} from "../api/compuwerxPackage4";

export default function CompuwerxBankReconciliation() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [imports, setImports] = useState([]);
  const [unmatchedEntries, setUnmatchedEntries] = useState([]);
  const [matches, setMatches] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [matching, setMatching] = useState(false);

  const [manualPayoutBatchId, setManualPayoutBatchId] = useState("");
  const [manualBankEntryId, setManualBankEntryId] = useState("");
  const [manualNote, setManualNote] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [importsRes, unmatchedRes, matchesRes] = await Promise.all([
        fetchBankStatementImports(),
        fetchUnmatchedBankEntries(),
        fetchPayoutBankMatches(),
      ]);
      setImports(importsRes?.results || []);
      setUnmatchedEntries(unmatchedRes?.results || []);
      setMatches(matchesRes?.results || []);
    } catch (err) {
      setError(err?.message || "Unable to load bank reconciliation data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError("");
    try {
      await uploadBankStatementCsv(file);
      await load();
    } catch (err) {
      setError(err?.message || "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  async function handleAutoMatch() {
    setMatching(true);
    setError("");
    try {
      await runAutoPayoutBankMatch();
      await load();
    } catch (err) {
      setError(err?.message || "Auto-match failed.");
    } finally {
      setMatching(false);
    }
  }

  async function handleManualMatch() {
    setError("");
    try {
      await createManualPayoutBankMatch({
        payout_batch_id: manualPayoutBatchId,
        bank_entry_id: manualBankEntryId,
        note: manualNote,
      });
      setManualPayoutBatchId("");
      setManualBankEntryId("");
      setManualNote("");
      await load();
    } catch (err) {
      setError(err?.message || "Manual match failed.");
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
      <Stack spacing={3}>
        <Typography variant="h4">Compuwerx Bank Reconciliation</Typography>
        {error ? <Alert severity="error">{error}</Alert> : null}

        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="h6">Upload Bank Statement CSV</Typography>
              <Button
                variant="contained"
                component="label"
                disabled={uploading}
              >
                {uploading ? "Uploading..." : "Choose CSV"}
                <input
                  hidden
                  type="file"
                  accept=".csv"
                  onChange={handleUpload}
                />
              </Button>
            </Stack>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="h6">Imported Statements</Typography>
              <Divider />
              {!imports.length ? (
                <Typography color="text.secondary">
                  No bank statement imports found.
                </Typography>
              ) : (
                <List dense>
                  {imports.map((row) => (
                    <ListItem key={row.id} disableGutters>
                      <ListItemText
                        primary={`${row.source_name} • ${row.status}`}
                        secondary={`Rows ${row.row_count} • ${row.created_at || ""}`}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Stack>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="h6">Auto-Match Payouts</Typography>
              <Button
                variant="contained"
                disabled={matching}
                onClick={handleAutoMatch}
              >
                {matching ? "Matching..." : "Run Auto-Match"}
              </Button>
            </Stack>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="h6">Manual Match</Typography>
              <TextField
                label="Payout Batch ID"
                value={manualPayoutBatchId}
                onChange={(e) => setManualPayoutBatchId(e.target.value)}
              />
              <TextField
                label="Bank Entry ID"
                value={manualBankEntryId}
                onChange={(e) => setManualBankEntryId(e.target.value)}
              />
              <TextField
                label="Note"
                value={manualNote}
                onChange={(e) => setManualNote(e.target.value)}
              />
              <Button variant="outlined" onClick={handleManualMatch}>
                Create Manual Match
              </Button>
            </Stack>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="h6">Unmatched Bank Entries</Typography>
              <Divider />
              {!unmatchedEntries.length ? (
                <Typography color="text.secondary">
                  No unmatched bank entries found.
                </Typography>
              ) : (
                <List dense>
                  {unmatchedEntries.map((row) => (
                    <ListItem key={row.id} disableGutters>
                      <ListItemText
                        primary={`${row.amount} ${row.currency} • ${row.posted_date}`}
                        secondary={`${row.description || "-"} • Ref ${row.reference || "-"}`}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Stack>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="h6">Payout Matches</Typography>
              <Divider />
              {!matches.length ? (
                <Typography color="text.secondary">
                  No payout-bank matches found.
                </Typography>
              ) : (
                <List dense>
                  {matches.map((row) => (
                    <ListItem key={row.id} disableGutters>
                      <ListItemText
                        primary={`Payout ${row.payout_batch_id} ↔ Bank Entry ${row.bank_entry_id}`}
                        secondary={`${row.status} • Δ ${row.amount_delta} • ${row.date_delta_days} day(s)`}
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
