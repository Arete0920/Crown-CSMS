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
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useCallback, useEffect, useState } from "react";
import {
  createDisputeAction,
  fetchDisputeDetail,
} from "../api/compuwerxPackage3";

const ACTIONS = [
  "acknowledge",
  "submit_evidence",
  "mark_won",
  "mark_lost",
  "close",
];

export default function CompuwerxDisputeWorkbench() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [detail, setDetail] = useState(null);
  const [actionType, setActionType] = useState("acknowledge");
  const [note, setNote] = useState("");

  const disputeId = new URLSearchParams(window.location.search).get(
    "dispute_id",
  );

  const load = useCallback(async () => {
    if (!disputeId) {
      setError("Missing dispute_id in query string.");
      setLoading(false);
      return;
    }

    try {
      const res = await fetchDisputeDetail(disputeId);
      setDetail(res);
    } catch (err) {
      setError(err?.message || "Unable to load dispute detail.");
    } finally {
      setLoading(false);
    }
  }, [disputeId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleSubmit() {
    setSaving(true);
    setError("");

    try {
      await createDisputeAction(disputeId, {
        action_type: actionType,
        note,
        evidence: {},
      });
      setNote("");
      await load();
    } catch (err) {
      setError(err?.message || "Unable to create dispute action.");
    } finally {
      setSaving(false);
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
        <Typography variant="h4">Compuwerx Dispute Workbench</Typography>
        {error ? <Alert severity="error">{error}</Alert> : null}

        {detail?.dispute ? (
          <Card>
            <CardContent>
              <Stack spacing={1}>
                <Typography variant="h6">Dispute Detail</Typography>
                <Typography variant="body2">
                  Dispute ID: {detail.dispute.dispute_id}
                </Typography>
                <Typography variant="body2">
                  Status: {detail.dispute.status}
                </Typography>
                <Typography variant="body2">
                  Amount: {detail.dispute.amount} {detail.dispute.currency}
                </Typography>
                <Typography variant="body2">
                  Reason: {detail.dispute.reason || "-"}
                </Typography>
                <Typography variant="body2">
                  Invoice ID: {detail.dispute.invoice_id || "-"}
                </Typography>
              </Stack>
            </CardContent>
          </Card>
        ) : null}

        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="h6">Create Action</Typography>
              <TextField
                select
                label="Action Type"
                value={actionType}
                onChange={(e) => setActionType(e.target.value)}
              >
                {ACTIONS.map((row) => (
                  <MenuItem key={row} value={row}>
                    {row}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                label="Note"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                multiline
                minRows={3}
              />
              <Button
                disabled={saving}
                variant="contained"
                onClick={handleSubmit}
              >
                {saving ? "Submitting..." : "Submit Action"}
              </Button>
            </Stack>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="h6">Action History</Typography>
              <Divider />
              {!detail?.actions?.length ? (
                <Typography color="text.secondary">
                  No actions found.
                </Typography>
              ) : (
                <List dense>
                  {detail.actions.map((row) => (
                    <ListItem key={row.id} disableGutters>
                      <ListItemText
                        primary={row.action_type}
                        secondary={`${row.note || "-"} • ${row.created_at || ""}`}
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
