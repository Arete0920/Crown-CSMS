import { useEffect, useRef, useState } from 'react';
import PropTypes from 'prop-types';
import { Alert, Box, Button, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { crownApiClient as api } from '../../api/client';

const teacherKinds = ['announcement', 'home_support', 'practice', 'formative_check', 'group_project', 'positive_observation', 'accommodation', 'support_plan', 'service', 'resource', 'interruption'];
const studentKinds = ['help_request', 'goal', 'reflection', 'portfolio'];
const individualKinds = [...studentKinds, 'absence_explanation', 'family_service', 'positive_observation', 'accommodation', 'support_plan'];
const responseKinds = ['practice', 'formative_check', 'group_project', 'service', 'resource', 'announcement', 'home_support'];
const label = (value) => value.replaceAll('_', ' ');

function RecordCard({ record, audience, students, busy, act }) {
  const [text, setText] = useState('');
  const [student, setStudent] = useState(students.length === 1 ? students[0].id : '');
  const [response, setResponse] = useState('');
  const canRespond = audience === 'student' && record.state !== 'resolved' && responseKinds.includes(record.kind);
  return <Box sx={{ border: '1px solid', borderColor: 'divider', p: 2, my: 1 }}>
    <Typography component="h4" variant="subtitle1">{record.title}</Typography>
    <Typography variant="body2">{label(record.kind)} · {record.visibility} · {record.state}{record.due_at ? ` · Review ${new Date(record.due_at).toLocaleString()}` : ''}</Typography>
    <Typography sx={{ whiteSpace: 'pre-wrap' }}>{record.body}</Typography>
    {(record.metadata.questions || record.metadata.milestones || []).map((item, i) => <Typography key={`${i}-${item}`}>{i + 1}. {item}</Typography>)}
    {record.metadata.scripture_reference && <Typography>Scripture reference: {record.metadata.scripture_reference}</Typography>}
    {record.metadata.reference && <a href={record.metadata.reference} target="_blank" rel="noreferrer">Open classroom resource</a>}
    {record.responses.map((r) => <Box key={r.id} sx={{ mt: 1 }}><Typography sx={{ whiteSpace: 'pre-wrap' }}>{r.content}</Typography>{r.feedback && <Typography>Teacher feedback: {r.feedback}</Typography>}</Box>)}
    {(canRespond || record.can_manage) && <>
      {canRespond && <TextField select fullWidth label="Responding student" value={student} onChange={(e) => setStudent(e.target.value)}><MenuItem value="">Choose student</MenuItem>{students.map((s) => <MenuItem key={s.id} value={s.id}>{s.first_name} {s.last_name}</MenuItem>)}</TextField>}
      <TextField fullWidth multiline minRows={2} label={canRespond ? 'Your response or contribution' : 'Follow-through note or feedback'} value={text} onChange={(e) => setText(e.target.value)} />
      {canRespond && <Button disabled={busy || !text.trim() || !student} onClick={() => act(record, { action: 'respond', content: text, student_id: student })}>Save response</Button>}
      {record.can_manage && <><Stack direction="row" spacing={1}>{(record.can_close === false ? ['acknowledge'] : ['acknowledge', record.state === 'resolved' ? 'reopen' : 'resolve']).map((action) => <Button key={action} disabled={busy || !text.trim()} onClick={() => act(record, { action, note: text })}>{label(action)}</Button>)}</Stack>
        {record.responses.length > 0 && <><TextField select fullWidth label="Response to review" value={response} onChange={(e) => setResponse(e.target.value)}><MenuItem value="">Choose response</MenuItem>{record.responses.map((r) => <MenuItem key={r.id} value={r.id}>{students.find((s) => s.id === r.student_id)?.first_name || 'Student'} · {r.state}</MenuItem>)}</TextField><Button disabled={busy || !response || !text.trim()} onClick={() => act(record, { action: 'feedback', response_id: response, note: text })}>Save feedback</Button></>}
      </>}
    </>}
    {record.history.length > 0 && <details><summary>Follow-through history</summary>{record.history.map((e, i) => <Typography key={`${e.created_at}-${i}`} variant="body2">{new Date(e.created_at).toLocaleString()} · {label(e.action)}{e.payload.note ? `: ${e.payload.note}` : ''}</Typography>)}</details>}
  </Box>;
}
RecordCard.propTypes = { record: PropTypes.object.isRequired, audience: PropTypes.string.isRequired, students: PropTypes.array.isRequired, busy: PropTypes.bool.isRequired, act: PropTypes.func.isRequired };

export default function ClassroomRecords({ audience, sections, students, assignments }) {
  const kinds = audience === 'student' ? studentKinds : audience === 'parent' ? ['absence_explanation', 'family_service'] : audience === 'admin' ? [...teacherKinds, 'coaching'] : teacherKinds;
  const [kind, setKind] = useState(kinds[0]);
  const [section, setSection] = useState('');
  const [student, setStudent] = useState('');
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [due, setDue] = useState('');
  const [visibility, setVisibility] = useState('private');
  const [extra, setExtra] = useState('');
  const [members, setMembers] = useState([]);
  const [roles, setRoles] = useState({});
  const [portrait, setPortrait] = useState('');
  const [worldview, setWorldview] = useState('');
  const [scripture, setScripture] = useState('');
  const [coachingTeacher, setCoachingTeacher] = useState('');
  const [cost, setCost] = useState('0');
  const [records, setRecords] = useState(null);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const retry = useRef(null);
  const url = `/api/v1/academics/classroom/records/?audience=${audience}`;
  useEffect(() => {
    let active = true;
    api.get(url).then((r) => {
      if (r.data.source !== 'live' || !Array.isArray(r.data.records)) throw new Error('Invalid classroom response');
      if (active) setRecords(r.data);
    }).catch(() => { if (active) setError('Classroom records could not be loaded. Retry to check the school version.'); });
    return () => { active = false; };
  }, [url, refresh]);
  async function save(endpoint, payload) {
    const signature = JSON.stringify([endpoint, payload]);
    if (retry.current?.signature !== signature) retry.current = { signature, payload: { ...payload, request_key: crypto.randomUUID() } };
    setBusy(true); setError(''); setMessage('');
    try {
      await api.post(endpoint, retry.current.payload);
      retry.current = null; setRefresh((v) => v + 1); setMessage('Saved to your classroom.');
    } catch (err) { setError(String(err.response?.data?.detail || 'Save not confirmed. Your text is retained; retry or refresh the school version.')); }
    finally { setBusy(false); }
  }
  function create() {
    const metadata = kind === 'formative_check' ? { questions: extra.split('\n').filter((v) => v.trim()) } : kind === 'group_project' ? { members, roles, milestones: extra.split('\n').filter((v) => v.trim()) } : kind === 'portfolio' ? { assignment_id: extra } : kind === 'resource' ? { reference: extra, cost_cents: Number(cost) } : kind === 'interruption' ? { minutes: Number(extra) } : {};
    if (['service', 'family_service'].includes(kind)) { if (portrait) metadata.portrait_domain_id = portrait; if (worldview) metadata.worldview_priority_id = worldview; metadata.scripture_reference = scripture; }
    if (kind === 'coaching') metadata.teacher_account_id = coachingTeacher;
    save(url, { kind, section_id: section, student_id: student || null, title, body, metadata, visibility: audience === 'student' ? visibility : individualKinds.includes(kind) ? 'family' : 'class', due_at: due ? new Date(due).toISOString() : null });
  }
  return <Box sx={{ mt: 3 }}>
    <Typography component="h3" variant="h6">Classroom collaboration and follow-through</Typography>
    {error && <Alert severity="warning">{error}</Alert>}{message && <Alert severity="success" role="status">{message}</Alert>}
    <Button disabled={busy} onClick={() => { setError(''); setRefresh((v) => v + 1); }}>Refresh school records</Button>
    <details><summary>Add a classroom record</summary><Stack spacing={1} sx={{ mt: 1 }}>
      <TextField select label="Record type" value={kind} onChange={(e) => { setKind(e.target.value); setExtra(''); setMembers([]); }}>{kinds.map((k) => <MenuItem key={k} value={k}>{label(k)}</MenuItem>)}</TextField>
      <TextField select label="Classroom" value={section} onChange={(e) => { setSection(e.target.value); setExtra(''); }}><MenuItem value="">Choose classroom</MenuItem>{sections.map((s) => <MenuItem key={s.id} value={s.id}>{s.course_name || s['course__name'] || s.course_code || s.id}</MenuItem>)}</TextField>
      {individualKinds.includes(kind) && <TextField select label="Student" value={student} onChange={(e) => setStudent(e.target.value)}><MenuItem value="">Choose student</MenuItem>{students.map((s) => <MenuItem key={s.id} value={s.id}>{s.first_name} {s.last_name}</MenuItem>)}</TextField>}
      <TextField label="Title" value={title} inputProps={{ maxLength: 160 }} onChange={(e) => setTitle(e.target.value)} />
      <TextField multiline minRows={3} label="Details, evidence or next steps" value={body} onChange={(e) => setBody(e.target.value)} />
      <TextField label="Review or due date" type="datetime-local" InputLabelProps={{ shrink: true }} value={due} onChange={(e) => setDue(e.target.value)} />
      {audience === 'student' && kind !== 'help_request' && <TextField select label="Share with" value={visibility} onChange={(e) => setVisibility(e.target.value)}>{['private', 'staff', 'family'].map((v) => <MenuItem key={v} value={v}>{v === 'private' ? 'Only me' : v === 'staff' ? 'My classroom staff' : 'My classroom staff and family'}</MenuItem>)}</TextField>}
      {kind === 'help_request' && <Typography variant="body2">Your request is shared with your classroom staff.</Typography>}
      {['formative_check', 'group_project', 'resource', 'interruption'].includes(kind) && <TextField multiline={kind === 'formative_check' || kind === 'group_project'} label={kind === 'formative_check' ? 'Questions, one per line' : kind === 'group_project' ? 'Milestones, one per line' : kind === 'resource' ? 'HTTPS resource link' : 'Minutes interrupted'} value={extra} onChange={(e) => setExtra(e.target.value)} />}
      {kind === 'group_project' && <TextField select SelectProps={{ multiple: true }} label="Group members" value={members} onChange={(e) => { const ids = e.target.value; setMembers(ids); setRoles((v) => Object.fromEntries(Object.entries(v).filter(([id]) => ids.includes(id)))); }}>{students.map((s) => <MenuItem key={s.id} value={s.id}>{s.first_name} {s.last_name}</MenuItem>)}</TextField>}
      {kind === 'group_project' && members.map((id) => <TextField key={id} label={`Role for ${students.find((s) => s.id === id)?.first_name || 'member'}`} value={roles[id] || ''} onChange={(e) => setRoles((v) => ({ ...v, [id]: e.target.value }))} />)}
      {['service', 'family_service'].includes(kind) && <>
        <TextField select label="Portrait of the Graduate domain" value={portrait} onChange={(e) => setPortrait(e.target.value)}><MenuItem value="">No domain selected</MenuItem>{(records?.portrait_domains || []).map((v) => <MenuItem key={v.id} value={v.id}>{v.name}</MenuItem>)}</TextField>
        <TextField select label="Biblical worldview priority" value={worldview} onChange={(e) => setWorldview(e.target.value)}><MenuItem value="">No priority selected</MenuItem>{(records?.worldview_priorities || []).map((v) => <MenuItem key={v.id} value={v.id}>{v.title}</MenuItem>)}</TextField>
        <TextField label="Scripture reference" value={scripture} onChange={(e) => setScripture(e.target.value)} />
        <Typography variant="body2">Record service participation and reflection. These records do not measure personal faith.</Typography>
      </>}
      {kind === 'coaching' && <TextField select label="Teacher receiving coaching" value={coachingTeacher} onChange={(e) => setCoachingTeacher(e.target.value)}><MenuItem value="">Choose teacher</MenuItem>{(records?.coaching_teachers || []).map((v) => <MenuItem key={v.id} value={v.id}>{v.name}</MenuItem>)}</TextField>}
      {kind === 'resource' && <TextField type="number" label="Recorded resource cost in cents" value={cost} onChange={(e) => setCost(e.target.value)} />}
      {kind === 'portfolio' && <TextField select label="Assignment evidence" value={extra} onChange={(e) => setExtra(e.target.value)}><MenuItem value="">Choose assignment</MenuItem>{assignments.filter((a) => a.section_id === section && a.is_published !== false).map((a) => <MenuItem key={`${a.id}-${a.student_id || ''}`} value={a.id}>{a.name}</MenuItem>)}</TextField>}
      <Button disabled={busy || !section || !title.trim() || !body.trim() || (individualKinds.includes(kind) && !student)} onClick={create}>Save classroom record</Button>
    </Stack></details>
    {records?.truncated && <Alert severity="info">Showing the latest 100 of {records.total} records.</Alert>}
    {records && records.records.length === 0 && <Typography>No classroom records yet.</Typography>}
    {records?.records.map((r) => <RecordCard key={r.id} record={r} audience={audience} students={students} busy={busy} act={(record, payload) => save(`/api/v1/academics/classroom/records/${record.id}/actions/?audience=${audience}`, { ...payload, version: record.version })} />)}
  </Box>;
}
ClassroomRecords.propTypes = { audience: PropTypes.string.isRequired, sections: PropTypes.array.isRequired, students: PropTypes.array.isRequired, assignments: PropTypes.array.isRequired };
