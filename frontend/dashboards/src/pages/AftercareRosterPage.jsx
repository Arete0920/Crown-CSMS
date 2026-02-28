import { useEffect, useState } from "react";
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Alert,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Paper,
} from "@mui/material";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import DashboardSection from "../components/layout/DashboardSection.jsx";
import { fetchRosterToday, checkinStudent, checkoutStudent } from "../api/aftercareApi.js";

function getSession() {
  try {
    return {
      token: sessionStorage.getItem("crown.jwt.access") || "",
      schoolId: sessionStorage.getItem("crown.school.id") || "",
    };
  } catch {
    return { token: "", schoolId: "" };
  }
}

function AttendanceChip({ row }) {
  const att = row.attendance;
  if (!att) return <Chip label="Not checked in" color="default" size="small" />;
  if (att.checkout_time) return <Chip label="Checked out" color="success" size="small" />;
  return <Chip label="Checked in" color="primary" size="small" />;
}

export default function AftercareRosterPage() {
  const { token, schoolId } = getSession();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [roster, setRoster] = useState(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRosterToday();
      setRoster(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleCheckin(studentId) {
    try {
      await checkinStudent({ student_id: studentId });
      await load();
    } catch (e) {
      alert(`Check-in failed: ${e.message}`);
    }
  }

  async function handleCheckout(studentId) {
    try {
      await checkoutStudent({ student_id: studentId, pickup_verified: false });
      await load();
    } catch (e) {
      alert(`Check-out failed: ${e.message}`);
    }
  }

  return (
    <CrownLayout title="Aftercare Roster">
      <DashboardSection title={`Today's Aftercare Roster${roster ? ` — ${roster.date} (${roster.dow})` : ""}`}>
        {loading && <CircularProgress size={28} />}
        {error && <Alert severity="error">{error}</Alert>}
        {!loading && !error && roster && (
          <Paper variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Student ID</TableCell>
                  <TableCell>Billing</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Late Min</TableCell>
                  <TableCell>Late Fee</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {roster.rows.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6}>
                      <Typography variant="body2" color="text.secondary">
                        No students scheduled today.
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
                {roster.rows.map((row) => {
                  const hasCheckin = !!row.attendance;
                  const hasCheckout = row.attendance?.checkout_time;
                  return (
                    <TableRow key={row.student_id}>
                      <TableCell>{row.student_id}</TableCell>
                      <TableCell>{row.enrollment?.billing_model}</TableCell>
                      <TableCell><AttendanceChip row={row} /></TableCell>
                      <TableCell>{row.attendance?.late_minutes ?? "—"}</TableCell>
                      <TableCell>
                        {row.attendance?.late_fee_cents
                          ? `$${(row.attendance.late_fee_cents / 100).toFixed(2)}`
                          : "—"}
                      </TableCell>
                      <TableCell>
                        {!hasCheckin && (
                          <Button size="small" variant="outlined" onClick={() => handleCheckin(row.student_id)}>
                            Check In
                          </Button>
                        )}
                        {hasCheckin && !hasCheckout && (
                          <Button size="small" variant="contained" color="success" onClick={() => handleCheckout(row.student_id)}>
                            Check Out
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </Paper>
        )}
      </DashboardSection>
    </CrownLayout>
  );
}
