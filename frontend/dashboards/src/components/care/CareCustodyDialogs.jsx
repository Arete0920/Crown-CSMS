import {
  Alert, Button, Checkbox, Dialog, DialogActions, DialogContent, DialogTitle,
  FormControlLabel, MenuItem, TextField, Typography,
} from "@mui/material";

/**
 * Shared, keyboard-accessible custody dialogs. The backend is authoritative
 * for both the authenticated school handoff and the active pickup grant.
 */
export function CareHandoffDialog({
  open, studentName, acknowledged, busy, onAcknowledge, onConfirm, onCancel,
}) {
  return (
    <Dialog
      open={open}
      onClose={busy ? undefined : onCancel}
      aria-labelledby="care-handoff-title"
      fullWidth
      maxWidth="sm"
    >
      <DialogTitle id="care-handoff-title">Confirm School Handoff — {studentName}</DialogTitle>
      <DialogContent dividers>
        <Typography variant="body1" sx={{ mb: 2 }}>
          The authenticated receiving staff member must personally confirm that the child
          is physically in their care. This is a recorded staff attestation, not automated identity proof.
        </Typography>
        <FormControlLabel
          control={<Checkbox checked={acknowledged} disabled={busy} onChange={(event) => onAcknowledge(event.target.checked)} />}
          label="I am the receiving staff member and acknowledge custody of this child."
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel} disabled={busy}>Cancel</Button>
        <Button variant="contained" onClick={onConfirm} disabled={busy || !acknowledged}>
          {busy ? "Recording..." : "Record School Handoff"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export function CarePickupDialog({
  open, studentName, contacts, selectedContactId, verified, busy,
  onSelectContact, onVerify, onConfirm, onCancel,
}) {
  const activeContacts = (Array.isArray(contacts) ? contacts : []).filter((contact) => contact.is_active);
  const selectedValid = activeContacts.some((contact) => String(contact.id) === String(selectedContactId));
  return (
    <Dialog
      open={open}
      onClose={busy ? undefined : onCancel}
      aria-labelledby="care-pickup-title"
      fullWidth
      maxWidth="sm"
    >
      <DialogTitle id="care-pickup-title">Verify Authorized Pickup — {studentName}</DialogTitle>
      <DialogContent dividers>
        <Typography variant="body1" sx={{ mb: 2 }}>
          Verify the person&apos;s identity against the school&apos;s active authorized pickup
          record before releasing this child. The staff attestation is recorded.
        </Typography>
        {activeContacts.length === 0 ? (
          <Alert severity="warning" sx={{ mb: 2 }}>
            No active authorized pickup contacts are on file. Checkout is blocked; contact school administration.
          </Alert>
        ) : (
          <>
            <TextField
              select
              fullWidth
              label="Authorized pickup contact"
              value={selectedContactId}
              disabled={busy}
              onChange={(event) => onSelectContact(event.target.value)}
              sx={{ mb: 2 }}
            >
              <MenuItem value="">Select a contact</MenuItem>
              {activeContacts.map((contact) => (
                <MenuItem key={contact.id} value={String(contact.id)}>
                  {contact.name} — {contact.relationship || "Authorized contact"}
                </MenuItem>
              ))}
            </TextField>
            <FormControlLabel
              control={
                <Checkbox
                  checked={verified}
                  disabled={busy || !selectedValid}
                  onChange={(event) => onVerify(event.target.checked)}
                />
              }
              label="I have checked this person's identity against the selected authorized pickup record."
            />
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel} disabled={busy}>Cancel</Button>
        <Button variant="contained" onClick={onConfirm} disabled={busy || !selectedValid || !verified}>
          {busy ? "Recording..." : "Confirm Checkout"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
