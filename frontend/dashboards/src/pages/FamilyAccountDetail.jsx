import {
  Alert,
  Box,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  Grid,
  List,
  ListItem,
  ListItemText,
  Stack,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import { fetchHouseholdFinanceSummary } from "../api/compuwerxOps";

export default function FamilyAccountDetail() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [data, setData] = useState(null);

  const householdId = new URLSearchParams(window.location.search).get(
    "household_id",
  );

  useEffect(() => {
    async function load() {
      if (!householdId) {
        setError("Missing household_id in query string.");
        setLoading(false);
        return;
      }

      try {
        const res = await fetchHouseholdFinanceSummary(householdId);
        setData(res);
      } catch (err) {
        setError(err?.message || "Unable to load household finance summary.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [householdId]);

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
        <Typography variant="h4">Family Account Detail</Typography>
        {error ? <Alert severity="error">{error}</Alert> : null}

        {data?.summary ? (
          <Grid container spacing={2}>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography variant="overline">Total Invoiced</Typography>
                  <Typography variant="h5">
                    {data.summary.total_invoiced}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography variant="overline">Outstanding</Typography>
                  <Typography variant="h5">
                    {data.summary.total_outstanding}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography variant="overline">Open Invoices</Typography>
                  <Typography variant="h5">
                    {data.summary.open_invoice_count}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography variant="overline">
                    Recent Payments Total
                  </Typography>
                  <Typography variant="h5">
                    {data.summary.recent_payments_total}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        ) : null}

        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Stack spacing={2}>
                  <Typography variant="h6">Invoices</Typography>
                  <Divider />
                  {!data?.invoices?.length ? (
                    <Typography color="text.secondary">
                      No invoices found.
                    </Typography>
                  ) : (
                    <List dense>
                      {data.invoices.map((row) => (
                        <ListItem key={row.id} disableGutters>
                          <ListItemText
                            primary={row.invoice_number || `Invoice ${row.id}`}
                            secondary={`${row.status || "-"} • Due ${row.balance_due}`}
                          />
                        </ListItem>
                      ))}
                    </List>
                  )}
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Stack spacing={2}>
                  <Typography variant="h6">Payments</Typography>
                  <Divider />
                  {!data?.payments?.length ? (
                    <Typography color="text.secondary">
                      No payments found.
                    </Typography>
                  ) : (
                    <List dense>
                      {data.payments.map((row) => (
                        <ListItem key={row.id} disableGutters>
                          <ListItemText
                            primary={`${row.amount} • ${row.status || "-"}`}
                            secondary={
                              row.external_payment_id || row.source || "Payment"
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                  )}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Stack>
    </Box>
  );
}
