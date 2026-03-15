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
import {
  fetchHouseholdStatementCsvUrl,
  fetchPaymentReceiptUrl,
} from "../api/compuwerxPackage3";

export default function FamilyStatementExportPage() {
  const [householdId, setHouseholdId] = useState("");
  const [paymentId, setPaymentId] = useState("");
  const [error] = useState("");

  return (
    <Box sx={{ p: 3 }}>
      <Stack spacing={3}>
        <Typography variant="h4">Statement / Receipt Export</Typography>
        {error ? <Alert severity="error">{error}</Alert> : null}

        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="h6">Household Statement CSV</Typography>
              <TextField
                label="Household ID"
                value={householdId}
                onChange={(e) => setHouseholdId(e.target.value)}
              />
              <Button
                variant="contained"
                disabled={!householdId}
                onClick={() =>
                  window.open(
                    fetchHouseholdStatementCsvUrl(householdId),
                    "_blank",
                  )
                }
              >
                Download Statement CSV
              </Button>
            </Stack>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="h6">Payment Receipt</Typography>
              <TextField
                label="Payment ID"
                value={paymentId}
                onChange={(e) => setPaymentId(e.target.value)}
              />
              <Button
                variant="contained"
                disabled={!paymentId}
                onClick={() =>
                  window.open(fetchPaymentReceiptUrl(paymentId), "_blank")
                }
              >
                Open Receipt
              </Button>
            </Stack>
          </CardContent>
        </Card>
      </Stack>
    </Box>
  );
}
