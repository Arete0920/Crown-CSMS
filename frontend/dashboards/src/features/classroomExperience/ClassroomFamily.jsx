import { useEffect, useRef, useState } from 'react';
import PropTypes from 'prop-types';
import { Alert, Box, Button, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { crownApiClient as api } from '../../api/client';
import FamilyWeeklyAgenda from './FamilyWeeklyAgenda';

function Thread({ row, manager, busy, save }) {
  const [reply, setReply] = useState('');
  const act = (operation, decision) => save({ operation, thread_id: row.id, version: row.version, content: reply, decision });
  return <Box sx={{ border: '1px solid', borderColor: 'divider', p: 2, my: 1 }}>
    <Typography component="h4" variant="subtitle1">{row.title}</Typography><Typography>{row.kind} · {row.state}</Typography>
    {row.conference && <Typography>Conference: {new Date(row.conference.starts_at).toLocaleString()}–{new Date(row.conference.ends_at).toLocaleTimeString()} · {row.conference.location}</Typography>}
    {row.messages.map((m) => <Box key={m.id} sx={{ my: 1 }}><Typography variant="body2">{m.own ? 'You' : 'Classroom participant'} · {new Date(m.created_at).toLocaleString()}{m.decision ? ` · ${m.decision}` : ''}</Typography><Typography sx={{ whiteSpace: 'pre-wrap' }}>{m.content}</Typography></Box>)}
    <TextField fullWidth multiline minRows={2} label={`Reply or follow-up for ${row.title}`} value={reply} onChange={(e) => setReply(e.target.value)} />
    <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap' }}>
      {row.state === 'open' && <Button disabled={busy || !reply.trim()} onClick={() => act('reply')}>Send classroom reply</Button>}
      {manager && row.kind !== 'consent' && <Button disabled={busy || !reply.trim()} onClick={() => act(row.state === 'open' ? 'resolve' : 'reopen')}>{row.state === 'open' ? 'Record resolution' : 'Reopen concern'}</Button>}
      {!manager && row.kind === 'consent' && row.state === 'open' && ['agreed', 'declined'].map((decision) => <Button key={decision} disabled={busy || !reply.trim()} onClick={() => act('consent', decision)}>{decision === 'agreed' ? 'Grant permission' : 'Decline permission'}</Button>)}
      {row.kind === 'conference' && row.state !== 'cancelled' && <Button disabled={busy || !reply.trim()} onClick={() => act('cancel')}>Cancel conference with note</Button>}
    </Stack>
  </Box>;
}
Thread.propTypes = { row: PropTypes.object.isRequired, manager: PropTypes.bool.isRequired, busy: PropTypes.bool.isRequired, save: PropTypes.func.isRequired };

export default function ClassroomFamily({ audience, sections, students, assignments }) {
  const manager = audience === 'teacher' || audience === 'admin';
  const [snapshot, setSnapshot] = useState(null);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const [kind, setKind] = useState('conversation');
  const [section, setSection] = useState('');
  const [student, setStudent] = useState('');
  const [guardian, setGuardian] = useState('');
  const [assignment, setAssignment] = useState('');
  const [slot, setSlot] = useState('');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [location, setLocation] = useState('');
  const [preferences, setPreferences] = useState(null);
  const [allowed, setAllowed] = useState('false');
  const [reason, setReason] = useState('');
  const retry = useRef(null);
  const url = `/api/v1/academics/classroom/family/?audience=${audience}`;
  const data = snapshot?.url === url ? snapshot.data : null;
  useEffect(() => {
    let active = true;
    api.get(url).then((r) => {
      if (r.data.source !== 'live' || !Array.isArray(r.data.threads) || !Array.isArray(r.data.slots) || !Array.isArray(r.data.notices) || !Array.isArray(r.data.guardians) || !Array.isArray(r.data.digest?.assignments)) throw new Error('Invalid family response');
      if (active) { setSnapshot({ url, data: r.data }); setError(''); setPreferences((p) => p || r.data.preferences); }
    }).catch(() => { if (active) { setSnapshot(null); setError('Family workspace could not be loaded. Refresh to retry.'); } });
    return () => { active = false; };
  }, [url, refresh]);
  async function save(payload) {
    const signature = JSON.stringify(payload);
    if (retry.current?.signature !== signature) retry.current = { signature, payload: { ...payload, request_key: crypto.randomUUID() } };
    setBusy(true); setError(''); setMessage('');
    try { await api.post(url, retry.current.payload); retry.current = null; setMessage('Saved to your classroom.'); setRefresh((v) => v + 1); }
    catch (err) { setError(String(err.response?.data?.detail || 'Save not confirmed. Your text is retained; retry or refresh before changing a conversation.')); }
    finally { setBusy(false); }
  }
  const studentSelect = <TextField select label="Student for family communication" value={student} onChange={(e) => setStudent(e.target.value)}><MenuItem value="">Choose student</MenuItem>{students.map((s) => <MenuItem key={s.id} value={s.id}>{s.first_name} {s.last_name}</MenuItem>)}</TextField>;
  const guardianSelect = <TextField select label="Designated guardian" value={guardian} onChange={(e) => setGuardian(e.target.value)}><MenuItem value="">Choose guardian</MenuItem>{data?.guardians.map((g) => <MenuItem key={g.id} value={g.id}>{g.first_name} {g.last_name}</MenuItem>)}</TextField>;
  return <Box sx={{ mt: 3 }}><Typography component="h3" variant="h6">Family classroom partnership</Typography>
    {error && <Alert severity="warning">{error}</Alert>}{message && <Alert severity="success" role="status">{message}</Alert>}
    <Button disabled={busy} onClick={() => { setError(''); setRefresh((v) => v + 1); }}>Refresh family workspace</Button>
    {data && <>
      {data.notices.map((n) => <Alert key={n.id} severity="info" action={<Button disabled={busy} onClick={() => save({ operation: 'dismiss', notice_id: n.id })}>Dismiss</Button>}>{n.title}</Alert>)}
      <FamilyWeeklyAgenda digest={data.digest} manager={manager} />
      {data.truncated && <Alert severity="info">This view shows up to 100 items per list.</Alert>}
      <details><summary>Start a conversation, request permission or book a conference</summary><Stack spacing={1} sx={{ mt: 1 }}>
        <TextField select label="Family action" value={kind} onChange={(e) => setKind(e.target.value)}><MenuItem value="conversation">Conversation</MenuItem>{manager && <MenuItem value="consent">Permission request</MenuItem>}<MenuItem value="conference">Conference</MenuItem></TextField>
        <TextField select label="Family classroom" value={section} onChange={(e) => { setSection(e.target.value); setAssignment(''); setSlot(''); }}><MenuItem value="">Choose classroom</MenuItem>{sections.map((s) => <MenuItem key={s.id} value={s.id}>{s['course__name'] || s.course_name || s.id}</MenuItem>)}</TextField>
        {studentSelect}{manager && guardianSelect}
        <TextField select label="Assignment context (optional)" value={assignment} onChange={(e) => setAssignment(e.target.value)}><MenuItem value="">General classroom topic</MenuItem>{[...new Map(assignments.filter((a) => a.section_id === section && a.published !== false).map((a) => [a.id, a])).values()].map((a) => <MenuItem key={a.id} value={a.id}>{a.name}</MenuItem>)}</TextField>
        {kind === 'conference' && <TextField select label="Available conference time" value={slot} onChange={(e) => setSlot(e.target.value)}><MenuItem value="">Choose time</MenuItem>{data.slots.filter((s) => s.section_id === section).map((s) => <MenuItem key={s.id} value={s.id}>{new Date(s.starts_at).toLocaleString()} · {s.location}</MenuItem>)}</TextField>}
        <TextField label="Family topic" value={title} onChange={(e) => setTitle(e.target.value)} /><TextField multiline minRows={3} label="Question, consent details or conference goals" value={content} onChange={(e) => setContent(e.target.value)} />
        <Button disabled={busy || !section || !student || (manager && !guardian) || !title.trim() || !content.trim() || (kind === 'conference' && !slot)} onClick={() => save({ operation: kind === 'conference' ? 'book' : 'create', kind, section_id: section, student_id: student, guardian_id: guardian, assignment_id: assignment || null, slot_id: slot, title, content })}>{kind === 'conference' ? 'Book conference' : 'Start classroom conversation'}</Button>
      </Stack></details>
      {manager && <details><summary>Publish conference availability</summary><Stack spacing={1}><TextField select label="Conference classroom" value={section} onChange={(e) => setSection(e.target.value)}><MenuItem value="">Choose classroom</MenuItem>{sections.map((s) => <MenuItem key={s.id} value={s.id}>{s['course__name'] || s.id}</MenuItem>)}</TextField><TextField type="datetime-local" label="Conference start" InputLabelProps={{ shrink: true }} value={start} onChange={(e) => setStart(e.target.value)} /><TextField type="datetime-local" label="Conference end" InputLabelProps={{ shrink: true }} value={end} onChange={(e) => setEnd(e.target.value)} /><TextField label="Conference location" value={location} onChange={(e) => setLocation(e.target.value)} /><Button disabled={busy || !start || !end || !location || !section} onClick={() => save({ operation: 'slot', section_id: section, starts_at: new Date(start).toISOString(), ends_at: new Date(end).toISOString(), location })}>Publish available time</Button></Stack></details>}
      {preferences && <details><summary>Classroom notification preferences</summary><Stack spacing={1}><TextField select label="In-app notices" value={String(preferences.in_app)} onChange={(e) => setPreferences({ ...preferences, in_app: e.target.value === 'true' })}><MenuItem value="true">Enabled</MenuItem><MenuItem value="false">Disabled</MenuItem></TextField><TextField select label="Preferred digest day" value={preferences.digest_day} onChange={(e) => setPreferences({ ...preferences, digest_day: Number(e.target.value) })}>{['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map((day, i) => <MenuItem key={day} value={i}>{day}</MenuItem>)}</TextField><TextField label="Notification timezone" value={preferences.timezone} onChange={(e) => setPreferences({ ...preferences, timezone: e.target.value })} />{['quiet_start', 'quiet_end'].map((key) => <TextField key={key} type="time" label={key === 'quiet_start' ? 'Quiet hours start' : 'Quiet hours end'} InputLabelProps={{ shrink: true }} value={preferences[key]?.slice(0, 5) || ''} onChange={(e) => setPreferences({ ...preferences, [key]: e.target.value || null })} />)}<Button disabled={busy} onClick={() => save({ operation: 'preferences', ...preferences })}>Save notification preferences</Button></Stack></details>}
      {audience === 'admin' && <details><summary>School-verified classroom disclosure restrictions</summary><Stack spacing={1}>{studentSelect}{guardianSelect}<TextField select label="Classroom disclosure allowed" value={allowed} onChange={(e) => setAllowed(e.target.value)}><MenuItem value="false">Restricted</MenuItem><MenuItem value="true">Allowed</MenuItem></TextField><TextField multiline label="Verified restriction or restoration reason" value={reason} onChange={(e) => setReason(e.target.value)} /><Button disabled={busy || !student || !guardian || !reason.trim()} onClick={() => save({ operation: 'disclosure', student_id: student, guardian_id: guardian, allowed: allowed === 'true', reason })}>Record disclosure decision</Button>{data.disclosures.map((d) => <Typography key={`${d.student_id}-${d.guardian_id}`}>{d.student_id} · {d.allowed ? 'Allowed' : 'Restricted'} · {d.reason}</Typography>)}</Stack></details>}
      {data.threads.length === 0 && <Typography>No family classroom conversations yet.</Typography>}
      {data.threads.map((row) => <Thread key={row.id} row={row} manager={manager} busy={busy} save={save} />)}
    </>}
  </Box>;
}
ClassroomFamily.propTypes = { audience: PropTypes.string.isRequired, sections: PropTypes.array.isRequired, students: PropTypes.array.isRequired, assignments: PropTypes.array.isRequired };
