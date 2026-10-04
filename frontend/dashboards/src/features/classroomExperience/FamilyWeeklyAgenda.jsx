import { useState } from 'react';
import PropTypes from 'prop-types';
import { Alert, Box, MenuItem, TextField, Typography } from '@mui/material';

const submissionLabels = {
  assigned: 'Not submitted', draft: 'Draft in progress', returned: 'Returned for revision',
  submitted: 'Submitted', late: 'Submitted late', missing: 'Marked missing', graded: 'Graded',
};

export default function FamilyWeeklyAgenda({ digest, manager }) {
  const [student, setStudent] = useState('');
  const children = [...new Map(digest.assignments.filter((a) => a.student_id)
    .map((a) => [a.student_id, a.student_name])).entries()];
  const selection = children.some(([id]) => id === student) ? student : '';
  const rows = selection ? digest.assignments.filter((a) => a.student_id === selection) : digest.assignments;
  return <details open={!manager}>
    <summary>Next seven days: classroom digest</summary>
    <Typography>{digest.from}–{digest.to} · Prepared {new Date(digest.prepared_at).toLocaleString()}</Typography>
    {children.length > 1 && <TextField select label="Homework for child" value={selection}
      onChange={(e) => setStudent(e.target.value)} sx={{ my: 1, minWidth: 220 }}>
      <MenuItem value="">All children</MenuItem>
      {children.map(([id, name]) => <MenuItem key={id} value={id}>{name}</MenuItem>)}
    </TextField>}
    {rows.map((a) => <Box key={`${a.id}:${a.student_id || 'class'}`} sx={{ my: 1, p: 1, borderLeft: '3px solid', borderColor: 'divider' }}>
      {a.student_name && <Typography variant="subtitle2">{a.student_name}{a.course ? ` · ${a.course}` : ''}</Typography>}
      <Typography>{a.name} · Due {a.due_date}</Typography>
      {a.original_due_date && a.original_due_date !== a.due_date && <Typography variant="body2">Adjusted deadline · Class due date {a.original_due_date}</Typography>}
      {a.submission_state && <Typography variant="body2">{submissionLabels[a.submission_state] || 'Submission status unavailable'}</Typography>}
      {a.makeup_instructions && <Typography sx={{ whiteSpace: 'pre-wrap' }}>Makeup instructions: {a.makeup_instructions}</Typography>}
      {a.home_support && <Typography sx={{ whiteSpace: 'pre-wrap' }}>Support at home: {a.home_support}</Typography>}
    </Box>)}
    {rows.length === 0 && <Typography>{digest.truncated
      ? 'No assignments for this child in the displayed items.'
      : 'No published assignments with a due date in this seven-day window.'}</Typography>}
    <Typography>{digest.recorded_submissions} recorded submissions · {digest.open_conversations} open conversations</Typography>
    {digest.truncated && <Alert severity="info">Showing the first {digest.assignments.length} of {digest.assignments_total} assignment items. Each child’s assignment counts separately. Open Student Work for a wider date range.</Alert>}
  </details>;
}

FamilyWeeklyAgenda.propTypes = { digest: PropTypes.object.isRequired, manager: PropTypes.bool.isRequired };
