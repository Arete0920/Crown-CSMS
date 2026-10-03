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
    catch (err) { setError(String(err.…1721 tokens truncated…d === 'true', reason })}>Record disclosure decision</Button>{data.disclosures.map((d) => <Typography key={`${d.student_id}-${d.guardian_id}`}>{d.student_id} · {d.allowed ? 'Allowed' : 'Restricted'} · {d.reason}</Typography>)}</Stack></details>}
      {data.threads.length === 0 && <Typography>No family classroom conversations yet.</Typography>}
      {data.threads.map((row) => <Thread key={row.id} row={row} manager={manager} busy={busy} save={save} />)}
    </>}
  </Box>;
}
ClassroomFamily.propTypes = { audience: PropTypes.string.isRequired, sections: PropTypes.array.isRequired, students: PropTypes.array.isRequired, assignments: PropTypes.array.isRequired };
