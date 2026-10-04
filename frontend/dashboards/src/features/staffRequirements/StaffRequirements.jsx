import { useEffect, useRef, useState } from 'react';
import PropTypes from 'prop-types';
import { Alert, Box, Button, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { crownApiClient as api } from '../../api/client';

const endpoint = '/api/v1/hr/staff-requirements/';
const today = () => new Date().toLocaleDateString('en-CA');

function Requirement({ row, canEdit, busy, save }) {
  const [reason, setReason] = useState('');
  const [completed, setCompleted] = useState(row.today || today());
  const [expiry, setExpiry] = useState('');
  const [evidence, setEvidence] = useState('');
  const [due, setDue] = useState(row.due_date);
  const [history, setHistory] = useState(null);
  const [historyError, setHistoryError] = useState('');
  const active = useRef(true);
  useEffect(() => { active.current = true; return () => { active.current = false; }; }, []);
  const act = (operation, extra = {}) => save({ operation, requirement_id: row.id, version: row.version, reason, ...extra });
  async function loadHistory(offset = 0) {
    setHistory(null); setHistoryError('');
    try {
      const r = await api.get(`${endpoint}?requirement_id=${encodeURIComponent(row.id)}&history_offset=${offset}`);
      if (r.data.source !== 'live' || r.data.history?.requirement_id !== row.id || !Array.isArray(r.data.history.events)) throw new Error('Invalid history');
      if (active.current) setHistory(r.data.history);
    } catch { if (active.current) setHistoryError('Requirement history could not be loaded. Retry.'); }
  }
  return <Box sx={{ my: 2, p: 2, border: '1px solid', borderColor: 'divider' }}>
    <Typography component="h3" variant="subtitle1">{row.staff_name} · {row.title}</Typography>
    <Typography>{row.category} · {row.status} · Due {row.due_date}</Typography>
    {row.staff_status !== 'ACTIVE' && <Typography>Staff record is inactive; retained requirements remain in the history.</Typography>}
    {row.completed_on && <Typography>Completion recorded {row.completed_on}{row.valid_until ? ` · Valid until ${row.valid_until}` : ''} · Evidence: {row.evidence_reference}</Typography>}
    {canEdit && <Stack spacing={1} sx={{ mt: 1 }}>
      <TextField multiline label={`Review reason for ${row.title}`} value={reason} onChange={(e) => setReason(e.target.value)} />
      {!row.completed_on && <>
        <TextField type="date" label={`Completion date for ${row.title}`} InputLabelProps={{ shrink: true }} value={completed} onChange={(e) => setCompleted(e.target.value)} />
        <TextField type="date" label={`Expiry date for ${row.title} (optional)`} InputLabelProps={{ shrink: true }} value={expiry} onChange={(e) => setExpiry(e.target.value)} />
        <TextField label={`Evidence reference for ${row.title}`} value={evidence} onChange={(e) => setEvidence(e.target.value)} />
        <Typography variant="body2">Reference the school’s verified record. Store sensitive source documents in the authorized document system.</Typography>
        <Button disabled={busy || !reason.trim() || !evidence.trim() || !completed} onClick={() => act('complete', { completed_on: completed, valid_until: expiry || null, evidence_reference: evidence })}>Record reviewed completion</Button>
      </>}
      {row.completed_on && <Button disabled={busy || !reason.trim()} onClick={() => act('reopen')}>Reopen; retain prior evidence in history</Button>}
      <TextField type="date" label={`New due date for ${row.title}`} InputLabelProps={{ shrink: true }} value={due} onChange={(e) => setDue(e.target.value)} />
      <Button disabled={busy || !reason.trim() || !due || due === row.due_date} onClick={() => act('reschedule', { due_date: due })}>Change due date with reason</Button>
    </Stack>}
    <Button onClick={() => loadHistory()}>Load review history</Button>
    {historyError && <Alert severity="warning">{historyError}</Alert>}
    {history && <Box><Typography>Showing {history.offset + 1}–{history.offset + history.events.length} of {history.total} review events.</Typography>
      <Button disabled={!history.offset} onClick={() => loadHistory(Math.max(0, history.offset - 100))}>Previous history page</Button>
      <Button disabled={history.next_offset == null} onClick={() => loadHistory(history.next_offset)}>Next history page</Button>
      {history.events.map((event) => <Typography key={event.version}>Version {event.version} · {event.action} · {event.reason}{event.created_at ? ` · Recorded ${event.created_at}` : ''}{event.before.evidence_reference ? ` · Previous evidence: ${event.before.evidence_reference}` : ''}</Typography>)}</Box>}
  </Box>;
}
Requirement.propTypes = { row: PropTypes.object.isRequired, canEdit: PropTypes.bool.isRequired, busy: PropTypes.bool.isRequired, save: PropTypes.func.isRequired };

export default function StaffRequirements() {
  const [snapshot, setSnapshot] = useState(null);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState('');
  const [filterStaff, setFilterStaff] = useState('');
  const [staff, setStaff] = useState('');
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('training');
  const [due, setDue] = useState('');
  const [reason, setReason] = useState('');
  const retry = useRef(null);
  const url = `${endpoint}?${new URLSearchParams({ offset: String(offset), staff_search: search, ...(filterStaff ? { staff_id: filterStaff } : {}) })}`;
  const data = snapshot?.url === url ? snapshot.data : null;
  useEffect(() => {
    let active = true; setSnapshot(null);
    api.get(url).then((r) => {
      if (r.data.source !== 'live' || !Array.isArray(r.data.requirements) || !Array.isArray(r.data.staff) || !r.data.summary) throw new Error('Invalid requirements response');
      if (active) { setSnapshot({ url, data: r.data }); setError(''); }
    }).catch(() => { if (active) { setSnapshot(null); setError('Staff requirements could not be loaded. Check HR access and refresh.'); } });
    return () => { active = false; };
  }, [url, refresh]);
  async function save(payload) {
    const signature = JSON.stringify(payload);
    if (retry.current?.signature !== signature) retry.current = { signature, payload: { ...payload, request_key: crypto.randomUUID() } };
    setBusy(true); setError(''); setMessage('');
    try { await api.post(endpoint, retry.current.payload); retry.current = null; setSnapshot(null); setMessage('Staff requirement record saved.'); setRefresh((v) => v + 1); }
    catch (err) {
      if ([401, 403, 404].includes(err.response?.status)) { setSnapshot(null); retry.current = null; }
      setError(String(err.response?.data?.detail || 'Save not confirmed. Your entries are retained; retry or refresh before changing this record.'));
    }
    finally { setBusy(false); }
  }
  return <Box sx={{ p: 2 }}><Typography component="h2" variant="h6">Staff requirements and renewals</Typography>
    {error && <Alert severity="warning">{error}</Alert>}{message && <Alert severity="success" role="status">{message}</Alert>}
    <Button disabled={busy} onClick={() => setRefresh((v) => v + 1)}>Refresh staff requirements</Button>
    <TextField label="Search canonical staff choices" value={search} onChange={(e) => { setSearch(e.target.value); setStaff(''); setFilterStaff(''); setOffset(0); }} />
    {data && <>
      <Typography>{data.total} requirements · {data.summary.overdue || 0} overdue · {data.summary.expired || 0} expired · {data.summary.expiring || 0} expiring within 30 days</Typography>
      <TextField select label="Requirements for staff" value={filterStaff} onChange={(e) => { setFilterStaff(e.target.value); setOffset(0); }}>
        <MenuItem value="">All staff</MenuItem>{data.staff.map((s) => <MenuItem key={s.id} value={s.id}>{s.first_name} {s.last_name}</MenuItem>)}</TextField>
      {data.staff_total > data.staff.length && <Alert severity="info">Showing {data.staff.length} of {data.staff_total} matching active staff choices. Refine the staff search.</Alert>}
      {data.can_edit && <details><summary>Add a staff requirement</summary><Stack spacing={1}>
        <TextField select label="Canonical staff member" value={staff} onChange={(e) => setStaff(e.target.value)}><MenuItem value="">Choose staff</MenuItem>{data.staff.map((s) => <MenuItem key={s.id} value={s.id}>{s.first_name} {s.last_name}</MenuItem>)}</TextField>
        <TextField label="Requirement title" value={title} onChange={(e) => setTitle(e.target.value)} />
        <TextField select label="Requirement category" value={category} onChange={(e) => setCategory(e.target.value)}>{['training', 'certification', 'clearance', 'acknowledgment'].map((v) => <MenuItem key={v} value={v}>{v}</MenuItem>)}</TextField>
        <TextField type="date" label="Requirement due date" InputLabelProps={{ shrink: true }} value={due} onChange={(e) => setDue(e.target.value)} />
        <TextField multiline label="Assignment reason" value={reason} onChange={(e) => setReason(e.target.value)} />
        <Button disabled={busy || !staff || !title.trim() || !due || !reason.trim()} onClick={() => save({ operation: 'create', staff_id: staff, title, category, due_date: due, reason })}>Assign staff requirement</Button>
      </Stack></details>}
      {data.requirements.length === 0 && <Typography>No requirements recorded for this selection.</Typography>}
      <Typography>Showing {data.requirements.length ? data.offset + 1 : 0}–{data.offset + data.requirements.length} of {data.total} requirements</Typography>
      <Button disabled={busy || offset === 0} onClick={() => setOffset(Math.max(0, offset - 100))}>Previous requirement page</Button>
      <Button disabled={busy || data.next_offset === null} onClick={() => setOffset(data.next_offset)}>Next requirement page</Button>
      {data.requirements.map((row) => <Requirement key={`${row.id}:${row.version}`} row={{ ...row, today: data.today }} canEdit={data.can_edit} busy={busy} save={save} />)}
    </>}
  </Box>;
}
