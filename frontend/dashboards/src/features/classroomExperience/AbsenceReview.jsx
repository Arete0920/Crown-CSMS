import { useState } from 'react';
import PropTypes from 'prop-types';
import { Alert, Box, Button, Checkbox, FormControlLabel, TextField, Typography } from '@mui/material';

function Explanation({ row, roster, date, version, busy, save }) {
  const [reason, setReason] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const student = roster.find((s) => s.id === row.student_id);
  const undated = !row.metadata?.absence_date;
  const ready = student?.identity_verified && ['ABSENT', 'EXCUSED'].includes(student.attendance)
    && (!undated || confirmed) && reason.trim() && !busy;
  function review(decision) {
    save({ operation: 'review_absence', explanation_id: row.id, explanation_version: row.version,
      version, decision, reason, confirm_undated_date: confirmed });
  }
  return <Box sx={{ my: 2 }}>
    <Typography variant="subtitle2">{student?.name || 'Student unavailable'} · {row.title}</Typography>
    <Typography sx={{ whiteSpace: 'pre-wrap' }}>{row.body}</Typography>
    <Typography>Absence date: {row.metadata?.absence_date || 'Not supplied'}</Typography>
    {undated && <FormControlLabel control={<Checkbox checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} />}
      label={`I verified that this explanation applies to ${date}`} />}
    {!student?.identity_verified && <Typography>Verified student identity is required.</Typography>}
    {!['ABSENT', 'EXCUSED'].includes(student?.attendance) && <Typography>Record and confirm the official absence before reviewing this explanation.</Typography>}
    <TextField fullWidth multiline label={`Review reason shared with family for ${row.title}`}
      value={reason} onChange={(e) => setReason(e.target.value)} />
    <Button disabled={!ready} onClick={() => review('excuse')}>Excuse recorded absence</Button>
    <Button disabled={!ready} onClick={() => review('decline')}>Decline explanation; retain attendance</Button>
  </Box>;
}
Explanation.propTypes = { row: PropTypes.object.isRequired, roster: PropTypes.array.isRequired,
  date: PropTypes.string.isRequired, version: PropTypes.number.isRequired, busy: PropTypes.bool.isRequired, save: PropTypes.func.isRequired };

export default function AbsenceReview({ rows, total, roster, date, version, busy, save }) {
  return <details><summary>Review family absence explanations</summary>
    <Typography>Staff decisions update the existing attendance evidence. Explanations alone do not change attendance.</Typography>
    {rows.length === 0 && <Typography>No pending explanations for this roster date.</Typography>}
    {total > rows.length && <Alert severity="info">Showing {rows.length} of {total} pending explanations. Refresh after reviews to see the next items.</Alert>}
    {rows.map((row) => <Explanation key={`${row.id}:${row.version}:${date}`} {...{ row, roster, date, version, busy, save }} />)}
  </details>;
}
AbsenceReview.propTypes = { rows: PropTypes.array.isRequired, total: PropTypes.number.isRequired,
  roster: PropTypes.array.isRequired, date: PropTypes.string.isRequired, version: PropTypes.number.isRequired,
  busy: PropTypes.bool.isRequired, save: PropTypes.func.isRequired };
