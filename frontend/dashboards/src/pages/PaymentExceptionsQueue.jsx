/* eslint-disable react-hooks/set-state-in-effect */
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
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import {
  fetchPaymentExceptions,
  ignorePaymentException,
  retryPaymentException,
} from "../api/paymentSupport";

export default function PaymentExceptionsQueue() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [rows, setRows] = useState([]);

  async function load() {
    try {
      const res = await fetchPaymentExceptions();
      setRows(res?.results || []);
    } catch (err) {
      setError(err?.message || "Unable to load payment exceptions.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function handleRetry(id) {
    try {
      await retryPaymentException(id);
      await load();
    } catch (err) {
      setError(err?.message || "Retry failed.");
    }
  }

  async function handleIgnore(id) {
    try {
      await ignorePaymentException(id);
      await load();
    } catch (err) {
      setError(err?.message || "Ignore failed.");
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
        <Typography variant="h4">Payment Exceptions Queue</Typography>
        {error ? <Alert severity="error">{error}</Alert> : null}

        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="h6">Open Exceptions</Typography>
              <Divider />
              {!rows.length ? (
                <Typography color="text.secondary">
                  No payment exceptions found.
                </Typography>
              ) : (
                <List dense>
                  {rows.map((row) => (
                    <ListItem
                      key={row.id}
                      disableGutters
                      secondaryAction={
                        <Stack direction="row" spacing={1}>
                          <Button
                            size="small"
                            onClick={() => handleRetry(row.id)}
                          >
                            Retry
                          </Button>
                          <Button
                            size="small"
                            color="warning"
                            onClick={() => handleIgnore(row.id)}
                          >
                            Ignore
                          </Button>
                        </Stack>
                      }
                    >
                      <ListItemText
                        primary={`${row.category} • ${row.severity} • ${row.status}`}
                        secondary={`${row.message} • retries ${row.retry_count}`}
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

