import { useEffect, useRef, useState } from 'react';
import PropTypes from 'prop-types';
import { Alert, Box, Button, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { crownApiClient as api } from '../../api/client';

function FollowThrough({ row, restorative, busy, save, students }) {
  const [note, setNote] = useState('');
  const [review, setReview] = useState('');
  const closed = row.state === 'CLOSED' || row.state === 'closed';
  function act(operation) { save({ operation, section_id: row.section_id, case_id: restorative ? undefined : row.id, incident_id: restorative ? row.id : undefined, version: row.version, note, review_at: review ? new Date(review).toISOString() : null }); }
  return <Box sx={{ border: '1px solid', borderColor: 'divider', p: 2, my: 1 }}><Typography component="h4" variant="subtitle1">{row.reason || row.title}</Typography><Typography>{students.find((s) => s.id === row.student_id)?.first_name || 'Student'} · {row.state} · Review {new Date(row.review_at).toLocaleString()}</Typography>{row.overdue_review && <Alert severity="warning">Support review is overdue.</Alert>}{row.actions.map((a) => <Typography key={a.id} sx={{ whiteSpace: 'pre-wrap' }}>{new Date(a.created_at).toLocaleString()} · {a.action_type}: {a.note}</Typography>)}
    {(!closed || !restorative) && <Stack spacing={1}><TextField multiline minRows={2} label={`Follow-through evidence: ${row.reason || row.title}`} value={note} onChange={(e) => setNote(e.target.value)} /><TextField type="datetime-local" label={`Next support review: ${row.reason || row.title}`} InputLabelProps={{ shrink: true }} value={review} onChange={(e) => setReview(e.target.value)} /><Stack direction="row" spacing={1}><Button disabled={busy || !note.trim() || !review} onClick={() => act(restorative ? 'restorative_note' : closed ? 'reopen_case' : 'follow_up')}>{closed ? 'Reopen with review date' : 'Record reviewed next step'}</Button>{!closed && <Button disabled={busy || !note.trim()} onClick={() => act(restorative ? 'close_restorative' : 'close_case')}>Close with outcome evidence</Button>}</Stack></Stack>}
  </Box>;
}
FollowThrough.propTypes = { row: PropTypes.object.isRequired, restorative: PropTypes.bool.isRequired, busy: PropTypes.bool.isRequired, save: PropTypes.func.isRequired, students: PropTypes.array.isRequired };

export default function ClassroomSupport({ audience, sections, students }) {
  const [data, setData] = useState(null);
  const [section, setSection] = useState('');
  const [student, setStudent] = useState('');
  const [operation, setOperation] = useState('case');
  const [existingCase, setExistingCase] = useState('');
  const [title, setTitle] = useState('');
  const [note, setNote] = useState('');
  const [review, setReview] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const retry = useRef(null);
  const url = `/api/v1/academics/classroom/support/?audience=${audience}`;
  useEffect(() => {
    let active = true;
    api.get(url).then((r) => { if (r.data.source !== 'live' || !Array.isArray(r.data.cases) || !Array.isArray(r.data.restorative)) throw new Error('Invalid support response'); if (active) setData(r.data); }).catch(() => { if (active) setError('Support follow-through could not be loaded. Refresh to retry.'); });
    return () => { active = false; };
  }, [url, refresh]);
  async function save(payload) {
    const signature = JSON.stringify(payload);
    if (retry.current?.signature !== signature) retry.current = { signature, payload: { ...payload, request_key: crypto.randomUUID() } };
    setBusy(true); setError(''); setMessage('');
    try { await api.post(url, retry.current.payload); retry.current = null; setMessage('Support follow-through confirmed.'); setRefresh((v) => v + 1); }
    catch (err) { setError(String(err.response?.data?.detail || 'Save not confirmed. Your notes are retained; retry or refresh the case version.')); }
    finally { setBusy(false); }
  }
  return <Box sx={{ mt: 3 }}><Typography component="h3" variant="h6">Confidential support and restorative follow-through</Typography>
    {error && <Alert severity="warning">{error}</Alert>}{message && <Alert severity="success" role="status">{message}</Alert>}
    <Button disabled={busy} onClick={() => { setError(''); setRefresh((v) => v + 1); }}>Refresh support cases</Button>
    {data && <><details><summary>Open instructional support or a restorative plan</summary><Stack spacing={1} sx={{ mt: 1 }}>
      <TextField select label="Support workflow" value={operation} onChange={(e) => setOperation(e.target.value)}><MenuItem value="case">Instructional support case</MenuItem><MenuItem value="restorative">Restorative classroom plan</MenuItem><MenuItem value="link_case">Use an existing owned case</MenuItem></TextField>
      <TextField select label="Support classroom" value={section} onChange={(e) => setSection(e.target.value)}><MenuItem value="">Choose classroom</MenuItem>{sections.map((s) => <MenuItem key={s.id} value={s.id}>{s['course__name'] || s.id}</MenuItem>)}</TextField>
      <TextField select label="Support student" value={student} onChange={(e) => setStudent(e.target.value)}><MenuItem value="">Choose student</MenuItem>{students.map((s) => <MenuItem key={s.id} value={s.id}>{s.first_name} {s.last_name}</MenuItem>)}</TextField>
      {operation === 'link_case' && <TextField select label="Existing canonical support case" value={existingCase} onChange={(e) => setExistingCase(e.target.value)}><MenuItem value="">Choose case</MenuItem>{(data.available_cases || []).filter((c) => c.student_id === student).map((c) => <MenuItem key={c.id} value={c.id}>{c.reason}</MenuItem>)}</TextField>}
      <TextField label="Support concern or restorative goal" value={title} onChange={(e) => setTitle(e.target.value)} /><TextField multiline minRows={3} label="Observed evidence, action and success condition" value={note} onChange={(e) => setNote(e.target.value)} /><TextField type="datetime-local" label="Required support review" InputLabelProps={{ shrink: true }} value={review} onChange={(e) => setReview(e.target.value)} />
      <Typography variant="body2">These staff records are private. Share an approved family support plan through the classroom collaboration controls.</Typography>
      <Button disabled={busy || !section || !student || (operation === 'link_case' ? !existingCase : !title.trim() || !note.trim() || !review)} onClick={() => save({ operation, section_id: section, student_id: student, case_id: existingCase || undefined, title, note, review_at: review ? new Date(review).toISOString() : null })}>Open owned plan with review date</Button>
    </Stack></details>
      {data.cases.length === 0 && data.restorative.length === 0 && <Typography>No owned classroom support plans recorded.</Typography>}
      {data.cases.map((row) => <FollowThrough key={row.id} row={row} restorative={false} busy={busy} save={save} students={students} />)}{data.restorative.map((row) => <FollowThrough key={row.id} row={row} restorative busy={busy} save={save} students={students} />)}
    </>}
  </Box>;
}
ClassroomSupport.propTypes = { audience: PropTypes.string.isRequired, sections: PropTypes.array.isRequired, students: PropTypes.array.isRequired };
