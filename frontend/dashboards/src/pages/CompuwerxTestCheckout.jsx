import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";
import useCompuwerxCheckout from "../hooks/useCompuwerxCheckout";

export default function CompuwerxTestCheckout() {
  const [invoiceId, setInvoiceId] = useState("");
  const [householdId, setHouseholdId] = useState("");
  const [amount, setAmount] = useState("");
  const { loading, error, beginCheckout } = useCompuwerxCheckout();

  const handleSubmit = async () => {
    await beginCheckout({
      invoice_id: invoiceId || null,
      household_id: householdId || null,
      amount,
      currency: "USD",
      description: "Crown invoice payment",
    });
  };

  return (
    <Box sx={{ p: 3 }}>
      <Card>
        <CardContent>
          <Stack spacing={2}>
            <Typography variant="h5">Compuwerx Test Checkout</Typography>
            {error ? <Alert severity="error">{error}</Alert> : null}

            <TextField
              label="Invoice ID"
              value={invoiceId}
              onChange={(e) => setInvoiceId(e.target.value)}
            />
            <TextField
              label="Household ID"
              value={householdId}
              onChange={(e) => setHouseholdId(e.target.value)}
            />
            <TextField
              label="Amount"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />

            <Button
              disabled={loading || !amount}
              variant="contained"
              onClick={handleSubmit}
            >
              {loading ? "Starting..." : "Start Compuwerx Checkout"}
            </Button>
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
}
