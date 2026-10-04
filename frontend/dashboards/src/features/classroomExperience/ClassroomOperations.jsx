import { useEffect, useRef, useState } from 'react';
import PropTypes from 'prop-types';
import { Alert, Box, Button, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { crownApiClient as api } from '../../api/client';
import AbsenceReview from './AbsenceReview';

function Emergency({ session, roster, busy, save }) {
  const [student, setStudent] = useState('');
  const [state, setState] = useState('present');
  const [note, setNote] = useState('');
  return <Box sx={{ border: '1px solid', borderColor: 'divider', p: 2, my: 1 }}><Typography component="h4" variant="subtitle1">{session.title} · {session.kind}</Typography>
    {session.checks.map((c) => <Typography key={c.student_id}>{roster.find((r) => r.id === c.student_id)?.name || c.student_id}: {c.state}{c.note ? ` · ${c.note}` : ''}</Typography>)}
    {session.completed_at ? <Typography>Completed {new Date(session.completed_at).toLocaleString()} · {session.completion_note}</Typography> : <Stack spacing={1}>
      <TextField select label={`Accountability student: ${session.title}`} value={student} onChange={(e) => setStudent(e.target.value)}><MenuItem value="">Choose student</MenuItem>{session.checks.map((c) => <MenuItem key={c.student_id} value={c.student_id}>{roster.find((r) => r.id === c.student_id)?.name || c.student_id}</MenuItem>)}</TextField>
      <TextField select label={`Accountability status: ${session.title}`} value={state} onChange={(e) => setState(e.target.value)}><MenuItem value="present">Confirmed present</MenuItem><MenuItem value="missing">Missing / unaccounted</MenuItem><MenuItem value="released">Accounted elsewhere</MenuItem></TextField>
      <TextField multiline label={`Verification or completion note: ${session.title}`} value={note} onChange={(e) => setNote(e.target.value)} />
      <Stack direction="row" spacing={1}><Button disabled={busy || !student || !note.trim()} onClick={() => save({ operation: 'check', session_id: session.id, version: session.version, student_id: student, state, note })}>Record individual check</Button><Button disabled={busy || !note.trim() || session.checks.some((c) => ['unknown', 'missing'].includes(c.state))} onClick={() => save({ operation: 'complete', session_id: session.id, version: session.version, note })}>Complete accountability</Button></Stack>
    </Stack>}
  </Box>;
}
Emergency.propTypes = { session: PropTypes.object.isRequired, roster: PropTypes.array.isRequired, busy: PropTypes.bool.isRequired, save: PropTypes.func.isRequired };

export default function ClassroomOperations({ audience }) {
  const [data, setData] = useState(null);
  const [section, setSection] = useState('');
  const [date, setDate] = useState(new Date().toLocaleDateString('en-CA'));
  const [marks, setMarks] = useState({});
  const [reason, setReason] = useState('');
  const [account, setAccount] = useState('');
  const [start, setStart] = useState('');
  const [expiry, setExpiry] = useState('');
  const [instructions, setInstructions] = useState('');
  const [title, setTitle] = useState('');
  const [kind, setKind] = useState('drill');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const retry = useRef(null);
  const url = '/api/v1/academics/classroom/operations/';
  useEffect(() => {
    let active = true; setData(null); setError(''); retry.current = null;
    api.get(url, { params: { section_id: section || undefined, date } }).then((r) => {
      if (r.data.source !== 'live' || !Array.isArray(r.data.sections) || (section && !Array.isArray(r.data.roster))) throw new Error('Invalid operations response');
      if (active) { setData(r.data); setMarks(Object.fromEntries((r.data.roster || []).filter((v) => v.attendance).map((v) => [v.id, v.attendance]))); }
    }).catch(() => { if (active) setError('Classroom operations could not be loaded. Check your section access and retry.'); });
    return () => { active = false; };
  }, [section, date, refresh]);
  async function save(extra) {
    const payload = { section_id: section, date, ...extra };
    const signature = JSON.stringify(payload);
    if (retry.current?.signature !== signature) retry.current = { signature, payload: { ...payload, request_key: crypto.randomUUID() } };
    setBusy(true); setError(''); setMessage('');
    try { await api.post(url, retry.current.payload); retry.current = null; setMessage('Classroom operation confirmed.'); setRefresh((v) => v + 1); }
    catch (err) { setError(String(err.response?.data?.detail || 'Action not confirmed. Your notes are retained; retry or refresh the school version.')); }
    finally { setBusy(false); }
  }
  return <Box sx={{ p: 2 }}><Typography component="h2" variant="h6">{audience === 'admin' ? 'School classroom operations' : 'Classroom attendance and preparation'}</Typography>
    {error && <Alert severity="warning">{error}</Alert>}{message && <Alert severity="success" role="status">{message}</Alert>}
    <Button disabled={busy} onClick={() => setRefresh((v) => v + 1)}>Refresh operational records</Button>
    {data && <><Stack direction="row" spacing={1}><TextField select fullWidth label="Operational classroom" value={section} onChange={(e) => setSection(e.target.value)}><MenuItem value="">Choose classroom</MenuItem>{data.sections.map((s) => <MenuItem key={s.id} value={s.id}>{s['course__name']} · {s.term}</MenuItem>)}</TextField><TextField type="date" label="Roster date" InputLabelProps={{ shrink: true }} value={date} onChange={(e) => setDate(e.target.value)} /></Stack>
      {data.roster && <>
        {data.can_review_absences && <AbsenceReview rows={data.absence_explanations || []}
          total={data.absence_explanations_total || 0} roster={data.roster} date={date}
          version={data.attendance_version} busy={busy} save={save} />}
        <details><summary>Roll call and attendance corrections</summary><Button onClick={() => setMarks(Object.fromEntries(data.roster.filter((r) => r.identity_verified).map((r) => [r.id, 'PRESENT'])))}>Set verified roster present; review before saving</Button>
          {data.roster.map((r) => <TextField key={r.id} select fullWidth label={`${r.name}${r.identity_verified ? '' : ' — verified identity required'}`} disabled={!r.identity_verified || busy} value={marks[r.id] || ''} onChange={(e) => setMarks({ ...marks, [r.id]: e.target.value })}><MenuItem value="">Unmarked</MenuItem>{['PRESENT', 'ABSENT', 'TARDY', 'EXCUSED'].map((v) => <MenuItem key={v} value={v}>{v}</MenuItem>)}</TextField>)}
          <TextField fullWidth multiline label="Attendance confirmation or correction reason" value={reason} onChange={(e) => setReason(e.target.value)} /><Button disabled={busy || !reason.trim() || !Object.keys(marks).length} onClick={() => save({ operation: 'attendance', version: data.attendance_version, reason, items: Object.entries(marks).map(([student_id, status]) => ({ student_id, status })) })}>Save confirmed attendance</Button>
          <details><summary>Attendance evidence history</summary>{data.attendance_history.map((h) => <Typography key={h.version}>Version {h.version} · {new Date(h.created_at).toLocaleString()} · {h.reason} · {h.changes.length} roster entries</Typography>)}</details>
        </details>
        <details><summary>Printable classroom and substitute packet</summary><Button onClick={() => window.print()}>Print selected packet</Button><Box className="classroom-print-packet"><Typography variant="h6">{data.sections.find((s) => s.id === section)?.['course__name']} · {date}</Typography><Typography>Prepared {new Date(data.packet.prepared_at).toLocaleString()}</Typography>{data.roster.map((r) => <Typography key={r.id}>{r.name} · Attendance: {r.attendance || 'Unmarked'}</Typography>)}{data.packet.lesson_plans.map((p) => <Box key={p.plan_date}><Typography>Objectives: {p.objectives}</Typography><Typography>Materials: {p.materials}</Typography><Typography>Activities: {p.activities}</Typography><Typography>Homework: {p.homework}</Typography></Box>)}{data.packet.substitute_instructions.map((v, i) => <Typography key={i}>{v}</Typography>)}{data.packet.limitations.map((v) => <Typography key={v} variant="body2">{v}</Typography>)}</Box></details>
        {data.can_delegate && <details><summary>Time-limited substitute access</summary><Stack spacing={1}><TextField select label="School-authorized substitute" value={account} onChange={(e) => setAccount(e.target.value)}><MenuItem value="">Choose account</MenuItem>{data.substitute_candidates.map((s) => <MenuItem key={s.id} value={s.id}>{s.username}</MenuItem>)}</TextField><TextField type="datetime-local" label="Substitute access begins" InputLabelProps={{ shrink: true }} value={start} onChange={(e) => setStart(e.target.value)} /><TextField type="datetime-local" label="Substitute access expires" InputLabelProps={{ shrink: true }} value={expiry} onChange={(e) => setExpiry(e.target.value)} /><TextField multiline label="Substitute instructions" value={instructions} onChange={(e) => setInstructions(e.target.value)} /><Button disabled={busy || !account || !start || !expiry || !instructions.trim()} onClick={() => save({ operation: 'grant', account_id: account, starts_at: new Date(start).toISOString(), expires_at: new Date(expiry).toISOString(), instructions })}>Grant expiring packet and roll-call access</Button>{data.delegations.map((g) => <Box key={g.id}><Typography>{g.account_id} · Expires {new Date(g.expires_at).toLocaleString()}{g.revoked_at ? ' · Revoked' : ''}</Typography>{!g.revoked_at && <Button disabled={busy || !instructions.trim()} onClick={() => save({ operation: 'revoke', grant_id: g.id, reason: instructions })}>Revoke with current instruction note</Button>}</Box>)}</Stack></details>}
        <details><summary>Drill or incident accountability</summary><Stack spacing={1}><TextField label="Accountability session title" value={title} onChange={(e) => setTitle(e.target.value)} /><TextField select label="Accountability session type" value={kind} onChange={(e) => setKind(e.target.value)}><MenuItem value="drill">Drill</MenuItem><MenuItem value="incident">Incident</MenuItem></TextField><Button disabled={busy || !title.trim()} onClick={() => save({ operation: 'emergency', title, kind })}>Start unconfirmed roster checks</Button></Stack>{data.emergencies.map((s) => <Emergency key={s.id} session={s} roster={data.roster} busy={busy} save={save} />)}</details>
      </>}
    </>}
    <style>{'@media print { body * { visibility: hidden; } .classroom-print-packet, .classroom-print-packet * { visibility: visible; } .classroom-print-packet { position: absolute; left: 0; top: 0; width: 100%; } }'}</style>
  </Box>;
}
ClassroomOperations.propTypes = { audience: PropTypes.string.isRequired };
