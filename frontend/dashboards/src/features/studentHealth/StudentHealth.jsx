import { useEffect, useRef, useState } from 'react';
import PropTypes from 'prop-types';
import { Alert, Box, Button, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { crownApiClient as api } from '../../api/client';

const endpoint = '/api/v1/student-health/workspace/';
const kinds = ['visit', 'administration', 'immunization', 'care_plan'];
const dateInput = (label, value, set) => <TextField type="date" label={label} value={value} onChange={(e) => set(e.target.value)} InputLabelProps={{ shrink: true }} />;

function EntryForm({ data, correction, busy, save, cancel }) {
  const [kind, setKind] = useState(correction?.kind || 'visit');
  const [stamp, setStamp] = useState(correction?.occurred_at || '');
  const [topic, setTopic] = useState(correction?.topic || '');
  const [summary, setSummary] = useState(correction?.summary || '');
  const [followUp, setFollowUp] = useState(correction?.follow_up_on || '');
  const [evidence, setEvidence] = useState(correction?.evidence_reference || '');
  const [authorization, setAuthorization] = useState(correction?.authorization_id || '');
  const [state, setState] = useState(correction?.administration_state || 'not_given');
  const [dose, setDose] = useState(correction?.administered_dose || '');
  const [unit, setUnit] = useState(correction?.administered_unit || '');
  const [reason, setReason] = useState('');
  const orders = data.authorizations;
  const selectedMissing = authorization && !orders.some((o) => o.id === authorization);
  return <Stack spacing={1} sx={{ my: 2 }}>
    <Typography component="h3" variant="subtitle1">{correction ? 'Append a correction; retain the original entry' : 'Record a health entry'}</Typography>
    {correction && <Typography>Correcting entry {correction.id}</Typography>}
    <TextField select label="Health record kind" value={kind} disabled={!!correction || busy} onChange={(e) => setKind(e.target.value)}>{kinds.map((v) => <MenuItem key={v} value={v}>{v.replace('_', ' ')}</MenuItem>)}</TextField>
    <TextField label="Event timestamp with timezone" helperText="Enter the actual event time, for example 2026-10-03T10:30:00-04:00." value={stamp} onChange={(e) => setStamp(e.target.value)} />
    <TextField label="Record topic" value={topic} onChange={(e) => setTopic(e.target.value)} />
    <TextField multiline label="Recorded observations or source details" value={summary} onChange={(e) => setSummary(e.target.value)} />
    {dateInput('Follow-up date (optional)', followUp, setFollowUp)}
    <TextField label="Source evidence reference" helperText="Required for immunization and care-plan records. Keep documents in the authorized document system." value={evidence} onChange={(e) => setEvidence(e.target.value)} />
    {kind === 'administration' && <>
      <TextField select label="Documented medication authorization" value={authorization} onChange={(e) => setAuthorization(e.target.value)}><MenuItem value="">Choose authorization</MenuItem>{selectedMissing && <MenuItem value={authorization}>{authorization} · Load its authorization page to review evidence</MenuItem>}{orders.map((o) => <MenuItem key={o.id} value={o.id}>{o.medication} · {o.state} · {o.id}</MenuItem>)}</TextField>
      <TextField select label="Administration outcome" value={state} onChange={(e) => setState(e.target.value)}>{['given', 'refused', 'not_given'].map((v) => <MenuItem key={v} value={v}>{v.replace('_', ' ')}</MenuItem>)}</TextField>
      {state === 'given' && <><TextField label="Actual administered dose" value={dose} onChange={(e) => setDose(e.target.value)} /><TextField label="Actual administered unit" value={unit} onChange={(e) => setUnit(e.target.value)} /></>}
      <Typography variant="body2">Transcribe the reviewed source order and actual event. CROWN does not calculate doses or convert units.</Typography>
    </>}
    <TextField multiline label="Record or correction reason" value={reason} onChange={(e) => setReason(e.target.value)} />
    <Button disabled={busy || !stamp || !topic.trim() || !summary.trim() || !reason.trim() || ((kind === 'care_plan' || kind === 'immunization') && !evidence.trim()) || (kind === 'administration' && (!authorization || (state === 'given' && (!dose || !unit))))}
      onClick={() => save({ operation: 'record', kind, occurred_at: stamp, topic, summary, follow_up_on: followUp || null, evidence_reference: evidence, reason,
        ...(correction ? { corrects_id: correction.id } : {}), ...(kind === 'administration' ? { authorization_id: authorization, administration_state: state, ...(state === 'given' ? { administered_dose: dose, administered_unit: unit } : {}) } : {}) })}>Save health entry</Button>
    {correction && <Button disabled={busy} onClick={cancel}>Cancel correction</Button>}
  </Stack>;
}
EntryForm.propTypes = { data: PropTypes.object.isRequired, correction: PropTypes.object, busy: PropTypes.bool.isRequired, save: PropTypes.func.isRequired, cancel: PropTypes.func.isRequired };

function AuthorizationForm({ data, busy, save }) {
  const [fields, setFields] = useState({ guardian_id: '', medication: '', dose: '', unit: '', route: '', directions: '', order_evidence: '', consent_evidence: '', starts_on: '', ends_on: '', reason: '' });
  const [verified, setVerified] = useState(false);
  const change = (name, value) => setFields((f) => ({ ...f, [name]: value }));
  return <details><summary>Record a reviewed medication authorization</summary><Stack spacing={1}>
    <TextField select label="Canonical guardian for consent" value={fields.guardian_id} onChange={(e) => change('guardian_id', e.target.value)}><MenuItem value="">Choose guardian</MenuItem>{data.guardians.map((g) => <MenuItem key={g.id} value={g.id}>{g.first_name} {g.last_name}</MenuItem>)}</TextField>
    <TextField select label="Guardian authority verified from school evidence" value={verified ? 'yes' : 'no'} onChange={(e) => setVerified(e.target.value === 'yes')}><MenuItem value="no">Verification pending</MenuItem><MenuItem value="yes">Verified by authorized staff</MenuItem></TextField>
    {['medication', 'dose', 'unit', 'route', 'directions', 'order_evidence', 'consent_evidence', 'reason'].map((name) => <TextField key={name} label={`Authorization ${name.replaceAll('_', ' ')}`} value={fields[name]} onChange={(e) => change(name, e.target.value)} />)}
    {dateInput('Authorization starts on', fields.starts_on, (v) => change('starts_on', v))}{dateInput('Authorization ends on', fields.ends_on, (v) => change('ends_on', v))}
    <Button disabled={busy || !verified || Object.values(fields).some((v) => !v.trim())} onClick={() => save({ operation: 'authorize', ...fields, guardian_authority_verified: true })}>Save reviewed authorization</Button>
  </Stack></details>;
}
AuthorizationForm.propTypes = { data: PropTypes.object.isRequired, busy: PropTypes.bool.isRequired, save: PropTypes.func.isRequired };

function Authorization({ row, busy, canEdit, save }) {
  const [reason, setReason] = useState('');
  return <Box sx={{ my: 2 }}><Typography component="h4" variant="subtitle2">{row.medication} · {row.state}</Typography>
    <Typography>Authorization {row.id} · {row.starts_on} through {row.ends_on} · Documented dose {row.dose} {row.unit} · Route {row.route}</Typography>
    <Typography>{row.directions} · Order evidence {row.order_evidence} · Consent evidence {row.consent_evidence}</Typography>
    {row.revoked_at && <Typography>Revoked {row.revoked_at} · {row.revocation_reason}</Typography>}
    {canEdit && !row.revoked_at && <><TextField label={`Revocation reason for ${row.id}`} value={reason} onChange={(e) => setReason(e.target.value)} /><Button disabled={busy || !reason.trim()} onClick={() => save({ operation: 'revoke', authorization_id: row.id, version: row.version, reason })}>Revoke authorization</Button></>}
  </Box>;
}
Authorization.propTypes = { row: PropTypes.object.isRequired, busy: PropTypes.bool.isRequired, canEdit: PropTypes.bool.isRequired, save: PropTypes.func.isRequired };

export default function StudentHealth() {
  const [student, setStudent] = useState(''); const [search, setSearch] = useState('');
  const [offset, setOffset] = useState(0); const [orderOffset, setOrderOffset] = useState(0); const [historyOffset, setHistoryOffset] = useState(0);
  const [snapshot, setSnapshot] = useState(null); const [error, setError] = useState(''); const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false); const [refresh, setRefresh] = useState(0); const [correction, setCorrection] = useState(null);
  const retry = useRef(null);
  const url = `${endpoint}?${new URLSearchParams({ search, offset: String(offset), authorization_offset: String(orderOffset), history_offset: String(historyOffset), ...(student ? { student_id: student } : {}) })}`;
  const data = snapshot?.url === url ? snapshot.data : null;
  useEffect(() => {
    let active = true;
    api.get(url).then((r) => {
      if (r.data.source !== 'live' || !Array.isArray(r.data.students) || (student && (r.data.student_id !== student || !Array.isArray(r.data.entries) || !Array.isArray(r.data.authorizations) || !Array.isArray(r.data.history)))) throw new Error('Invalid clinical response');
      if (active) { setSnapshot({ url, data: r.data }); setError(''); }
    }).catch(() => { if (active) { setSnapshot(null); setError('Health workspace unavailable. Check clinical access and refresh.'); } });
    return () => { active = false; };
  }, [url, refresh, student]);
  async function save(payload) {
    const values = { ...payload, student_id: student }; const signature = JSON.stringify(values);
    if (retry.current?.signature !== signature) retry.current = { signature, payload: { ...values, request_key: crypto.randomUUID() } };
    setBusy(true); setError(''); setMessage('');
    try { await api.post(endpoint, retry.current.payload); retry.current = null; setCorrection(null); setSnapshot(null); setMessage('Health record saved.'); setRefresh((v) => v + 1); }
    catch (err) {
      if ([401, 403, 404].includes(err.response?.status)) { setSnapshot(null); setCorrection(null); retry.current = null; }
      setError(String(err.response?.data?.detail || 'Save not confirmed. Entries are retained; retry or refresh.'));
    }
    finally { setBusy(false); }
  }
  const refreshData = () => { setSnapshot(null); setRefresh((v) => v + 1); };
  return <Box sx={{ p: 2 }}><Typography component="h2" variant="h6">Restricted student health workspace</Typography>
    {error && <Alert severity="warning">{error}</Alert>}{message && <Alert severity="success" role="status">{message}</Alert>}
    <Button disabled={busy} onClick={refreshData}>Refresh health records</Button>
    <TextField disabled={busy} label="Search canonical students" value={search} onChange={(e) => { setSearch(e.target.value); setStudent(''); setCorrection(null); setOffset(0); setOrderOffset(0); setHistoryOffset(0); setMessage(''); }} />
    {data && <><TextField select disabled={busy} label="Canonical student health record" value={student} onChange={(e) => { setStudent(e.target.value); setCorrection(null); setOffset(0); setOrderOffset(0); setHistoryOffset(0); setMessage(''); }}><MenuItem value="">Choose student</MenuItem>{data.students.map((s) => <MenuItem key={s.id} value={s.id}>{s.first_name} {s.last_name} · {s.student_number} · {s.status}</MenuItem>)}</TextField>
      {data.students_total > data.students.length && <Alert severity="info">Showing {data.students.length} of {data.students_total} students. Refine the search.</Alert>}
      {student && <>
        <Typography>{data.entries_total} retained entries · {data.follow_up_due} current entries with follow-up due · {Object.entries(data.summary).map(([k, n]) => `${n} ${k.replace('_', ' ')}`).join(' · ')}</Typography>
        {data.can_edit && (data.student_status === 'ACTIVE' || correction) && <EntryForm key={`${student}:${correction?.id || 'new'}`} data={data} correction={correction} busy={busy} save={save} cancel={() => setCorrection(null)} />}
        {data.can_edit && data.student_status === 'ACTIVE' && <AuthorizationForm key={student} data={data} busy={busy} save={save} />}
        <Typography component="h3" variant="subtitle1">Retained chart entries</Typography>
        {data.entries.map((entry) => <Box key={entry.id} sx={{ my: 2, p: 2, border: '1px solid', borderColor: 'divider' }}>
          <Typography>{entry.topic} · {entry.kind.replace('_', ' ')} · {entry.occurred_at}{entry.superseded ? ' · Superseded; original retained' : ''}</Typography>
          <Typography>{entry.summary}</Typography>{entry.corrects_id && <Typography>Corrects entry {entry.corrects_id}</Typography>}
          {entry.evidence_reference && <Typography>Evidence {entry.evidence_reference}</Typography>}{entry.follow_up_on && <Typography>Follow-up {entry.follow_up_on}</Typography>}
          {entry.kind === 'administration' && <Typography>Authorization {entry.authorization_id} · {entry.administration_state}{entry.administered_dose ? ` · Recorded ${entry.administered_dose} ${entry.administered_unit}` : ''}</Typography>}
          {data.can_edit && !entry.superseded && <Button disabled={busy} onClick={() => setCorrection(entry)}>Correct entry {entry.id}</Button>}
        </Box>)}
        <Button disabled={busy || offset === 0} onClick={() => setOffset(Math.max(0, offset - 100))}>Previous chart page</Button><Button disabled={busy || data.next_offset === null} onClick={() => setOffset(data.next_offset)}>Next chart page</Button>
        <Typography component="h3" variant="subtitle1">Medication authorizations · {data.authorizations_total} retained</Typography>
        {data.authorizations.map((o) => <Authorization key={`${o.id}:${o.version}`} row={o} busy={busy} canEdit={data.can_edit} save={save} />)}
        <Button disabled={busy || orderOffset === 0} onClick={() => setOrderOffset(Math.max(0, orderOffset - 100))}>Previous authorization page</Button><Button disabled={busy || data.authorizations_next_offset === null} onClick={() => setOrderOffset(data.authorizations_next_offset)}>Next authorization page</Button>
        <Typography component="h3" variant="subtitle1">Audit reasons · {data.history_total} events</Typography>
        {data.history.map((event, i) => <Typography key={`${event.created_at}:${i}`}>{event.operation} · {event.created_at} · Actor {event.actor_id} · {event.reason} · Record {event.result.entry_id || event.result.authorization_id}</Typography>)}
        <Button disabled={busy || historyOffset === 0} onClick={() => setHistoryOffset(Math.max(0, historyOffset - 100))}>Previous audit page</Button><Button disabled={busy || data.history_next_offset === null} onClick={() => setHistoryOffset(data.history_next_offset)}>Next audit page</Button>
      </>}
    </>}
  </Box>;
}
