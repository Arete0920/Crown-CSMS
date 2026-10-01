import { useCallback, useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { Alert, Box, Button, Card, CardContent, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { crownApiClient as api } from '../../api/client';

export default function ClassroomLeadership({ audience }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [term, setTerm] = useState('');
  const [target, setTarget] = useState('');
  const [from, setFrom] = useState(new Date().toISOString().slice(0, 10));
  const [to, setTo] = useState(new Date().toISOString().slice(0, 10));
  const load = useCallback(async (signal) => {
    setBusy(true); setError(''); setData(null);
    try {
      const r = await api.get('/api/v1/academics/classroom/leadership/', { params: { audience, term, from, to, target_class_size: target || undefined }, signal });
      if (r.data?.source !== 'live' || !r.data.summary?.definitions || !Array.isArray(r.data.provenance) || !Array.isArray(r.data.terms)) throw new Error('Invalid report contract');
      if (!signal?.aborted) setData(r.data);
    } catch (err) {
      if (!signal?.aborted) setError(String(err.response?.data?.detail || 'Classroom oversight could not be loaded. Retry with a valid date window.'));
    } finally { if (!signal?.aborted) setBusy(false); }
  }, [audience, term, from, to, target]);
  useEffect(() => { const c = new AbortController(); load(c.signal); return () => c.abort(); }, [load]);
  return <Box component="section" aria-label="Classroom oversight" sx={{ p: 2 }}>
    <Typography component="h2" variant="h5">Classroom oversight</Typography>
    <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ my: 2 }}>
      <TextField label="Report from" type="date" value={from} slotProps={{ inputLabel: { shrink: true } }} onChange={(e) => setFrom(e.target.value)} />
      <TextField label="Report through" type="date" value={to} slotProps={{ inputLabel: { shrink: true } }} onChange={(e) => setTo(e.target.value)} />
      <TextField select label="Report term" value={term} sx={{ minWidth: 180 }} onChange={(e) => setTerm(e.target.value)}><MenuItem value="">All recorded terms</MenuItem>{(data?.terms || []).map((v) => <MenuItem key={v} value={v}>{v}</MenuItem>)}</TextField>
      <TextField label="Planning target: students per section" type="number" value={target} slotProps={{ htmlInput: { min: 1, max: 1000 } }} onChange={(e) => setTarget(e.target.value)} helperText="Optional scenario using current rosters" />
      <Button disabled={busy} onClick={() => load()}>Refresh oversight</Button>
    </Stack>
    {busy && <Typography role="status">Loading recorded classroom evidence…</Typography>}
    {error && <Alert severity="warning">{error}</Alert>}
    {data && <>
      <Typography>Reporting window: {data.from} through {data.to}. Generated {new Date(data.generated_at).toLocaleString()}.</Typography>
      <Card sx={{ my: 2 }}><CardContent><dl>{Object.entries(data.summary).filter(([k]) => k !== 'definitions').map(([k, v]) => <div key={k}><dt>{k.replaceAll('_', ' ')}</dt><dd>{v === null ? 'No recorded value' : String(v)}</dd></div>)}</dl></CardContent></Card>
      {audience === 'admin' && <>
        <Typography component="h3" variant="h6">Section planning and delivery</Typography>
        {(data.sections || []).map((s) => <Typography key={s.id}>{s.course} · {s.term}: {s.roster_size} section enrollments; {s.verified_teachers} verified assigned teachers; {s.planned_lessons} planned lesson links; {s.confirmed_taught_lessons} confirmed taught lessons.</Typography>)}
        <Typography component="h3" variant="h6" sx={{ mt: 2 }}>Recorded teacher workload</Typography>
        {(data.teacher_workload || []).map((t) => <Typography key={t.teacher_id}>{t.teacher}: {t.sections} sections; {t.section_enrollments} section enrollments; {t.unique_students} unique students; {t.assignments_due} assignments due; {t.pending_grading} submissions awaiting grading; planned minutes {t.planned_minutes === null ? 'not recorded' : t.planned_minutes}.</Typography>)}
      </>}
      <Typography component="h3" variant="h6" sx={{ mt: 2 }}>Definitions and sources</Typography>
      {Object.entries(data.summary.definitions).map(([k, v]) => <Typography key={k} variant="body2" sx={{ mb: 1 }}>{v}</Typography>)}
      <Typography variant="body2">Sources: {data.provenance.join(', ')}</Typography>
      {(data.limitations || []).map((v) => <Typography key={v} variant="caption" display="block">{v}</Typography>)}
    </>}
  </Box>;
}
ClassroomLeadership.propTypes = { audience: PropTypes.oneOf(['admin', 'board']).isRequired };
