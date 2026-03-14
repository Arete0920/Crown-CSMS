import { useState, useEffect } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import CrownCard from "../components/crown/CrownCard.jsx";
import {
  Alert,
  Box,
  Button,
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
import useFinanceDashboardData from "../hooks/useFinanceDashboardData";

function metricValue(source, key, fallback = "—") {
  const value = source?.[key];
  return value === undefined || value === null || value === ""
    ? fallback
    : value;
}

function InvoiceList({ invoices }) {
  const openOnly = invoices.filter((row) => Number(row.balance_due || 0) > 0);

  if (!openOnly.length) {
    return (
      <Typography variant="body2" color="text.secondary">
        No open invoices found.
      </Typography>
    );
  }

  return (
    <List dense>
      {openOnly.slice(0, 10).map((row) => (
        <ListItem key={row.id} disableGutters>
          <ListItemText
            primary={row.invoice_number || `Invoice ${row.id}`}
            secondary={`${row.household_name || "Household"} • Due ${row.balance_due}`}
          />
        </ListItem>
      ))}
    </List>
  );
}

function KpiCard({ title, value, subtitle }) {
  return (
    <Card sx={{ height: "100%" }}>
      <CardContent>
        <Stack spacing={1}>
          <Typography variant="overline" color="text.secondary">
            {title}
          </Typography>
          <Typography variant="h4">{value}</Typography>
          {subtitle ? (
            <Typography variant="body2" color="text.secondary">
              {subtitle}
            </Typography>
          ) : null}
        </Stack>
      </CardContent>
    </Card>
  );
}

export default function FinanceDashboard() {
  const { loading, error, metrics, summary, invoices, reload } =
    useFinanceDashboardData();

  return (
    <Box sx={{ p: 3 }}>
      <Stack spacing={3}>
        <Stack
          direction={{ xs: "column", md: "row" }}
          spacing={2}
          justifyContent="space-between"
          alignItems={{ xs: "stretch", md: "center" }}
        >
          <Box>
            <Typography variant="h4">Finance Dashboard</Typography>
            <Typography variant="body2" color="text.secondary">
              Live finance metrics and invoice visibility.
            </Typography>
          </Box>

          <Button variant="outlined" onClick={reload}>
            Refresh
          </Button>
        </Stack>

        {error ? <Alert severity="error">{error}</Alert> : null}

        {loading ? (
          <Box sx={{ py: 8, display: "flex", justifyContent: "center" }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <KpiCard
                  title="AR Outstanding"
                  value={metricValue(metrics, "ar_outstanding")}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <KpiCard
                  title="Open Invoices"
                  value={metricValue(metrics, "open_invoices")}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <KpiCard
                  title="Collected This Month"
                  value={metricValue(metrics, "collected_month")}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <KpiCard
                  title="Payment Failures"
                  value={metricValue(metrics, "payment_failures")}
                />
              </Grid>
            </Grid>

            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Card sx={{ height: "100%" }}>
                  <CardContent>
                    <Stack spacing={2}>
                      <Typography variant="h6">Finance Summary</Typography>
                      <Divider />
                      {!summary ? (
                        <Typography variant="body2" color="text.secondary">
                          No summary data available.
                        </Typography>
                      ) : (
                        <Stack spacing={1}>
                          {Object.entries(summary).map(([key, value]) => (
                            <Stack
                              key={key}
                              direction="row"
                              justifyContent="space-between"
                              spacing={2}
                            >
                              <Typography
                                variant="body2"
                                color="text.secondary"
                              >
                                {key}
                              </Typography>
                              <Typography variant="body2">
                                {String(value)}
                              </Typography>
                            </Stack>
                          ))}
                        </Stack>
                      )}
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card sx={{ height: "100%" }}>
                  <CardContent>
                    <Stack spacing={2}>
                      <Typography variant="h6">Open Invoices</Typography>
                      <Divider />
                      <InvoiceList invoices={invoices} />
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </>
        )}
      </Stack>
    </Box>
  );
}
