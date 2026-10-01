import { useEffect, useRef, useState } from 'react';
import PropTypes from 'prop-types';
import { Alert, Box, Button, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { crownApiClient as api } from '../../api/client';

export default function AssignmentWork({ assignment, audience, students }) {
  const [student, setStudent] = useState(assignment.student_id || '');
  const [work, setWork] = useState(null);
  const [content, setContent] = useState('');
  const [feedback, setFeedback] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const retry = useRef(null);
  const url = `/api/v1/academics/assignments/${assignment.id}/work/?audience=${audience}`;
  useEffect(() => {
    let active = true;
    setWork(null);
    setContent('');
    setError('');
    setMessage('');
    retry.current = null;
    if (student) api.get(url, { params: { student_id: student } }).then((r) => {
      if (active) { setWork(r.data); setContent(r.data.content); }
    }).catch(() => { if (active) setError('Work could not be loaded. Close and reopen to retry.'); });
    return () => { active = false; };
  }, [student, url]);
  async function act(action) {
    const payload = { student_id: student, action, version: work.version, content, feedback };
    const serialized = JSON.stringify(payload);
    if (retry.current?.serialized !== serialized) retry.current = { serialized, payload: { ...payload, request_key: crypto.randomUUID() } };
    setBusy(true); setError(''); setMessage('');
    try {
      const response = await api.post(url, retry.current.payload);
      setWork(response.data);
      setContent(response.data.content);
      retry.current = null;
      setMessage(action === 'submit' ? `Submission confirmed at ${new Date(response.data.submitted_at).toLocaleString()}` : action === 'save_draft' ? 'Draft saved to your school account.' : 'Teacher response recorded.');
    } catch (err) {
      setError(String(err.response?.data?.detail || 'Action not confirmed. Your text is retained here; retry the same action.'));
    } finally { setBusy(false); }
  }
  const owner = audience === 'student';
  const manager = audience === 'teacher' || audience === 'admin';
  const editable = owner && work && ['assigned', 'draft', 'returned'].includes(work.state);
  return <Box sx={{ mt: 2 }}>
    {!assignment.student_id && <TextField select fullWidth label="Student work" value={student} onChange={(e) => setStudent(e.target.value)}>
      <MenuItem value="">Choose a student</MenuItem>{students.map((s) => <MenuItem key={s.id} value={s.id}>{s.first_name} {s.last_name}</MenuItem>)}
    </TextField>}
    {error && <Alert severity="warning">{error}</Alert>}
    {message && <Alert severity="success" role="status">{message}</Alert>}
    {work && <>
      {owner && <Button disabled={busy} onClick={async () => { try { const r = await api.get(url, { params: { student_id: student } }); setWork(r.data); retry.current = null; setMessage('School version refreshed. Your current text is retained; review before saving.'); } catch { setError('School version could not be refreshed. Your text is retained.'); } }}>Refresh saved version, keep my text</Button>}
      <Typography>Work state: {work.state} · Saved version {work.version}</Typography>
      {owner && <TextField fullWidth multiline minRows={4} label="Your work" value={content} disabled={!editable || busy} onChange={(e) => setContent(e.target.value)} />}
      {!owner && <Typography sx={{ whiteSpace: 'pre-wrap' }}>{work.content || 'No shared written work available.'}</Typography>}
      {editable && <Stack direction="row" spacing={1} sx={{ my: 1 }}><Button disabled={busy} onClick={() => act('save_draft')}>Save draft</Button><Button variant="contained" disabled={busy || !content.trim()} onClick={() => act('submit')}>Submit work</Button></Stack>}
      {manager && <><TextField fullWidth multiline label="Feedback or revision instructions" value={feedback} disabled={busy} onChange={(e) => setFeedback(e.target.value)} /><Stack direction="row" spacing={1}><Button disabled={busy || !feedback.trim()} onClick={() => act('feedback')}>Record feedback</Button><Button disabled={busy || !feedback.trim() || !['submitted', 'late', 'graded'].includes(work.state)} onClick={() => act('return')}>Return for revision</Button></Stack></>}
      <Typography component="h5" variant="subtitle2">Work and feedback history</Typography>
      {work.revisions.map((r) => <Box key={r.id} sx={{ my: 1 }}><Typography variant="body2">Version {r.sequence}: {r.action.replaceAll('_', ' ')} · {new Date(r.created_at).toLocaleString()}</Typography>{r.feedback && <Typography sx={{ whiteSpace: 'pre-wrap' }}>{r.feedback}</Typography>}</Box>)}
    </>}
  </Box>;
}
AssignmentWork.propTypes = { assignment: PropTypes.object.isRequired, audience: PropTypes.string.isRequired, students: PropTypes.array.isRequired };
