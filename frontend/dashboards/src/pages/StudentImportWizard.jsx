import { useState } from 'react';
import { Alert, Button, Checkbox, FormControlLabel, Stack, TextField, Typography } from '@mui/material';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import { apiFetch } from '../lib/api.js';

const BASE = '/api/v1/student-import-wizard/sessions/';
const columns = { StudentNumber: 'student_number', FirstName: 'first_name', LastName: 'last_name',
  BirthDate: 'dob', Status: 'status', FamilyId: 'family_id', HouseholdId: 'household_id', Grade: 'grade_level' };
const sample = [{ StudentNumber: 'SYNTHETIC-001', FirstName: 'Sample', LastName: 'Student',
  BirthDate: '2014-01-01', Status: 'ACTIVE', FamilyId: '', HouseholdId: '', Grade: '' }];

async function request(path, payload) {
  const response = await apiFetch(path, payload === undefined ? { method: 'GET' } : { method: 'POST', body: JSON.stringify(payload) });
  const value = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(String(value.error || value.detail || `HTTP ${response.status}`));
    error.status = response.status; throw error;
  }
  return value;
}

export default function StudentImportWizard() {
  const [phase, setPhase] = useState('configure'); const [session, setSession] = useState(null);
  const [mapping, setMapping] = useState(JSON.stringify(columns, null, 2));
  const [rows, setRows] = useState(JSON.stringify(sample, null, 2));
  const [preview, setPreview] = useState(null); const [result, setResult] = useState(null);
  const [reason, setReason] = useState(''); const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false); const [page, setPage] = useState(0);
  function fail(err) {
    if ([401, 403, 404].includes(err.status)) { setPreview(null); setResult(null); setPhase('blocked'); }
    setError(err.message);
  }
  async function configure(event) {
    event.preventDefault(); setBusy(true); setError('');
    try {
      const columnMap = JSON.parse(mapping); const stagedRows = JSON.parse(rows);
      let id = session;
      if (!id) { const created = await request(BASE, {}); id = created.session_id; setSession(id); }
      await request(`${BASE}${id}/configure/`, { column_map: columnMap, staged_rows: stagedRows });
      setPreview(null); setResult(null); setConfirmed(false); setPage(0); setPhase('preview');
    } catch (err) { fail(err); } finally { setBusy(false); }
  }
  async function review() {
    setBusy(true); setError('');
    try {
      const value = await request(`${BASE}${session}/preview/`, {});
      if (value.schema !== 2 || !Array.isArray(value.rows) || !Array.isArray(value.errors) || !value.fingerprint) throw new Error('Complete canonical preview unavailable.');
      setPreview(value); setConfirmed(false); setPage(0); setPhase('commit');
    } catch (err) { fail(err); } finally { setBusy(false); }
  }
  async function verify() {
    const value = await request(`${BASE}${session}/verify/`);
    if (value.schema !== 2 || value.source !== 'live' || value.session_id !== session || !Array.isArray(value.records) || !Array.isArray(value.differences) || typeof value.verified !== 'boolean' || !Number.isInteger(value.verified_count) || value.verified_count < 0 || value.verified_count > value.records.length || (value.verified && value.verified_count !== value.records.length)) throw new Error('Canonical verification evidence unavailable. Retry verification.');
    setResult(value); setPhase(value.verified ? 'done' : 'reconcile');
  }
  async function commit() {
    setBusy(true); setError('');
    try {
      const saved = await request(`${BASE}${session}/commit/`, { confirm: true, fingerprint: preview.fingerprint, reason });
      setResult(saved); setPhase('verify');
      await verify();
    } catch (err) { fail(err); } finally { setBusy(false); }
  }
  async function retryVerification() {
    setBusy(true); setError(''); try { await verify(); } catch (err) { fail(err); } finally { setBusy(false); }
  }
  const valid = preview?.errors.length === 0 && preview?.valid > 0;
  return <CrownLayout title="Student Import" subtitle="Review canonical identity, commit the complete batch, and verify saved records">
    {error && <Alert severity="warning">{error}</Alert>}
    {phase === 'blocked' && <Typography>Records are hidden because access or school context changed. Refresh after restoring authorized access.</Typography>}
    {phase === 'verify' && <Stack spacing={2}><Typography>The batch was saved; canonical verification is still pending.</Typography><Button disabled={busy} onClick={retryVerification}>Recheck canonical records</Button></Stack>}
    {phase === 'configure' && <form onSubmit={configure}><Stack spacing={2}>
      <Typography component="h2" variant="h6">Configure school source data</Typography>
      <Typography>Supply existing school family and household IDs with their recorded bridge, actual birth dates, student numbers and explicit status. This import creates student identities; it does not enroll students in courses or create families/accounts.</Typography>
      <TextField multiline minRows={8} label="Source column mapping" value={mapping} disabled={busy} onChange={(e) => setMapping(e.target.value)} />
      <TextField multiline minRows={8} label="Staged source rows" value={rows} disabled={busy} onChange={(e) => setRows(e.target.value)} />
      <Typography variant="body2">Status: APPLICANT, ACTIVE, WITHDRAWN or ALUMNI. Grade codes must belong to this school. Source identifiers remain strings, including leading zeros. For an existing unmapped identity, include its explicit compatibility_student_id; names never select an identity.</Typography>
      <Button type="submit" disabled={busy}>Configure import</Button>
    </Stack></form>}
    {phase === 'preview' && <><Typography component="h2" variant="h6">Preview every proposed change</Typography><Button disabled={busy} onClick={review}>Run canonical preview</Button><Button disabled={busy} onClick={() => setPhase('configure')}>Edit source data</Button></>}
    {phase === 'commit' && preview && <Stack spacing={2}>
      <Typography component="h2" variant="h6">Review before committing</Typography>
      <Typography>{preview.valid} valid rows · {preview.errors.length} rows requiring correction. Any unresolved row blocks the whole batch.</Typography>
      {preview.errors.map((e) => <Alert severity="warning" key={e.row}>Row {e.row + 1}: {e.messages.join(' ')}</Alert>)}
      <Typography>Showing proposed rows {page * 100 + 1}–{Math.min((page + 1) * 100, preview.rows.length)} of {preview.rows.length}</Typography>
      {preview.rows.slice(page * 100, (page + 1) * 100).map((row) => <details key={row.row}><summary>Row {row.row + 1} · {row.action} · {row.after.student_number} · {row.after.first_name} {row.after.last_name}</summary>
        <Typography>Before: {row.before ? JSON.stringify(row.before) : 'New canonical student'}</Typography><Typography>After: {JSON.stringify(row.after)}</Typography>
        <Typography>Reviewed household {row.household_id} · Grade {row.grade_code || 'Unassigned'}</Typography>
      </details>)}
      <Stack direction="row"><Button disabled={busy || page === 0} onClick={() => setPage((v) => v - 1)}>Previous proposed rows</Button><Button disabled={busy || (page + 1) * 100 >= preview.rows.length} onClick={() => setPage((v) => v + 1)}>Next proposed rows</Button></Stack>
      <TextField multiline label="Import review reason" value={reason} disabled={busy} onChange={(e) => setReason(e.target.value)} />
      <FormControlLabel control={<Checkbox disabled={busy || !valid} checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} />} label="I reviewed every proposed change and its identity mappings" />
      <Button disabled={busy || !valid || !confirmed || !reason.trim()} onClick={commit}>Commit reviewed batch and verify</Button>
      <Button disabled={busy} onClick={() => { setPreview(null); setConfirmed(false); setPhase('configure'); }}>Correct source data</Button>
      <Button disabled={busy} onClick={review}>Refresh canonical preview</Button>
    </Stack>}
    {(phase === 'done' || phase === 'reconcile') && result && <Stack spacing={2}>
      <Alert severity={result.verified ? 'success' : 'warning'}>{result.verified ? 'Canonical import verified' : 'Imported records need reconciliation'}</Alert>
      <Typography>{result.created} created · {result.updated} updated · {result.verified_count} verified against saved canonical records.</Typography>
      {result.differences.map((d) => <Typography key={d.row}>Row {d.row + 1} · {d.detail}</Typography>)}
      <Typography variant="body2">Verification reflects the saved rows at {result.verified_at}. It does not certify provider export completeness or historical grade migration.</Typography>
      <Button disabled={busy} onClick={retryVerification}>Recheck canonical records</Button>
      <Button disabled={busy} onClick={() => { setSession(null); setPreview(null); setResult(null); setReason(''); setConfirmed(false); setPhase('configure'); }}>Start another reviewed import</Button>
    </Stack>}
  </CrownLayout>;
}
