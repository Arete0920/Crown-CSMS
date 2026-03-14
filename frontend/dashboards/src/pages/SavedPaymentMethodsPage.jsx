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
import { useCallback, useEffect, useState } from "react";
import {
  createSavedPaymentMethodSetup,
  detachSavedPaymentMethod,
  fetchSavedPaymentMethods,
  setDefaultPaymentMethod,
} from "../api/compuwerxPackage3";

export default function SavedPaymentMethodsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [rows, setRows] = useState([]);
  const householdId = new URLSearchParams(window.location.search).get(
    "household_id",
  );

  const load = useCallback(async () => {
    if (!householdId) {
      setError("Missing household_id in query string.");
      setLoading(false);
      return;
    }

    try {
      const res = await fetchSavedPaymentMethods(householdId);
      setRows(res?.results || []);
    } catch (err) {
      setError(err?.message || "Unable to load saved payment methods.");
    } finally {
      setLoading(false);
    }
  }, [householdId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleAddMethod() {
    try {
      const res = await createSavedPaymentMethodSetup(householdId, {
        provider: "compuwerx",
        return_url: window.location.href,
      });
      if (res?.setup_url) {
        window.location.assign(res.setup_url);
      }
    } catch (err) {
      setError(err?.message || "Unable to start payment method setup.");
    }
  }

  async function handleSetDefault(methodId) {
    try {
      await setDefaultPaymentMethod(householdId, methodId);
      await load();
    } catch (err) {
      setError(err?.message || "Unable to set default payment method.");
    }
  }

  async function handleDetach(methodId) {
    try {
      await detachSavedPaymentMethod(householdId, methodId);
      await load();
    } catch (err) {
      setError(err?.message || "Unable to remove payment method.");
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
        <Typography variant="h4">Saved Payment Methods</Typography>
        {error ? <Alert severity="error">{error}</Alert> : null}

        <Button variant="contained" onClick={handleAddMethod}>
          Add / Manage in Compuwerx
        </Button>

        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="h6">Methods</Typography>
              <Divider />
              {!rows.length ? (
                <Typography color="text.secondary">
                  No saved payment methods found.
                </Typography>
              ) : (
                <List dense>
                  {rows.map((row) => (
                    <ListItem
                      key={row.id}
                      disableGutters
                      secondaryAction={
                        <Stack direction="row" spacing={1}>
                          {!row.is_default ? (
                            <Button
                              size="small"
                              onClick={() => handleSetDefault(row.id)}
                            >
                              Default
                            </Button>
                          ) : null}
                          <Button
                            size="small"
                            color="error"
                            onClick={() => handleDetach(row.id)}
                          >
                            Remove
                          </Button>
                        </Stack>
                      }
                    >
                      <ListItemText
                        primary={`${row.brand || row.method_type || "Method"} •••• ${row.last4 || "----"}`}
                        secondary={`${row.exp_month || "--"}/${row.exp_year || "----"}${row.is_default ? " • Default" : ""}`}
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
