import { useEffect, useRef, useState } from 'react';
import PropTypes from 'prop-types';
import { Alert, Box, Button, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { crownApiClient as api } from '../../api/client';

export default function ClassroomInstruction({ audience, sections, students, assignments }) {
  const manager = audience === 'teacher' || audience === 'admin';
  const [data, setData] = useState(null);
  const [section, setSection] = useState('');
  const [assignment, setAssignment] = useState('');
  const [student, setStudent] = useState('');
  const [operation, setOperation] = useState('rubric');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [levels, setLevels] = useState('');
  const [criteria, setCriteria] = useState([]);
  const [reference, setReference] = useState('');
  const [date, setDate] = useState('');
  const [note, setNote] = useState('');
  const [reason, setReason] = useState('');
  const [urlValue, setUrlValue] = useState('');
  const [level, setLevel] = useState(1);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const retry = useRef(null);
  const url = `/api/v1/academics/classroom/instruction/?audience=${audience}`;
  useEffect(() => {
    let active = true;
    api.get(url).then((r) => {
      if (r.data.source !== 'live' || !['lessons', 'objectives', 'plans', 'rubrics', 'adjustments', 'resources', 'progress', 'mastery_history'].every((key) => Array.isArray(r.data[key]))) throw new Error('Invalid instruction response');
      if (active) setData(r.data);
    }).catch(() => { if (active) setError('Instruction evidence could not be loaded. Refresh to retry.'); });
    return () => { active = false; };
  }, [url, refresh]);
  async function save() {
    const payload = { operation, section_id: section, assignment_id: assignment, student_id: student };
    if (operation === 'rubric') Object.assign(payload, { title, criteria });
    if (operation === 'attach_rubric') payload.rubric_id = reference;
    if (operation === 'curriculum') payload.objective_id = reference;
    if (operation === 'copy_plan') Object.assign(payload, { plan_id: reference, plan_date: date });
    if (operation === 'deadline') Object.assign(payload, { due_date: date, instructions: note, reason_private: reason, version: data.adjustments.find((a) => a.assignment_id === assignment && a.student_id === student)?.version || 0 });
    if (operation === 'resource') Object.assign(payload, { lesson_id: reference, title, url: urlValue, accessible_description: description, alternative_instructions: note });
    if (operation === 'mastery') Object.assign(payload, { level, note });
    const signature = JSON.stringify(payload);
    if (retry.current?.signature !== signature) retry.current = { signature, payload: { ...payload, request_key: crypto.randomUUID() } };
    setBusy(true); setError(''); setMessage('');
    try { await api.post(url, retry.current.payload); retry.current = null; setMessage('Instruction change confirmed. Refresh classroom work to see updated assignment details.'); setRefresh((v) => v + 1); }
    catch (err) { setError(String(err.response?.data?.detail || 'Change not confirmed. Your notes are retained; retry or refresh the school version.')); }
    finally { setBusy(false); }
  }
  const needsAssignment = ['attach_rubric', 'curriculum', 'deadline', 'mastery'].includes(operation);
  const references = operation === 'attach_rubric' ? data?.rubrics : operation === 'curriculum' ? data?.objectives : operation === 'copy_plan' ? data?.plans : data?.lessons;
  return <Box sx={{ mt: 3 }}><Typography component="h3" variant="h6">Instruction, resources and progress evidence</Typography>
    {error && <Alert severity="warning">{error}</Alert>}{message && <Alert severity="success" role="status">{message}</Alert>}
    <Button disabled={busy} onClick={() => { setError(''); setRefresh((v) => v + 1); }}>Refresh instruction evidence</Button>
    {data && <>
      <details><summary>Recorded progress and category weights</summary>{data.progress.map((p) => <Box key={`${p.section_id}-${p.student_id}`} sx={{ my: 1 }}><Typography>{students.find((s) => s.id === p.student_id)?.first_name || 'Student'} · {sections.find((s) => s.id === p.section_id)?.['course__name']}</Typography><Typography>{p.weighted_preview_percent === null ? 'Weighted preview withheld: review weights, evidence coverage or grade conflicts.' : `Provisional weighted evidence: ${Number(p.weighted_preview_percent).toFixed(1)}%`}</Typography><Typography>{p.recorded_scored_assignments} scored of {p.published_assignments} published assignments · Active weights total {p.policy_weight_total}%</Typography>{p.categories.map((c) => <Typography key={c.name}>{c.name}: {c.weight_percent}% weight · {c.scored_assignments} scored assignments</Typography>)}<Typography variant="body2">{p.limitation}</Typography></Box>)}</details>
      <details><summary>Dated mastery evidence</summary>{data.mastery_history.map((e, i) => <Typography key={`${e.created_at}-${i}`}>{new Date(e.created_at).toLocaleString()} · {students.find((s) => s.id === e.record__student_id)?.first_name || 'Student'} · Level {e.level} · {e.note}</Typography>)}</details>
      <details><summary>Accessible classroom resources</summary>{data.resources.map((r) => <Box key={r.id}><Typography component="h4" variant="subtitle1">{r.title}</Typography>{r.url.startsWith('https://') && <a href={r.url} target="_blank" rel="noreferrer">Open {r.title}</a>}<Typography sx={{ whiteSpace: 'pre-wrap' }}>{r.accessible_description}</Typography><Typography sx={{ whiteSpace: 'pre-wrap' }}>{r.alternative_instructions}</Typography></Box>)}</details>
      {manager && <details><summary>Improve or reuse instruction</summary><Stack spacing={1} sx={{ mt: 1 }}>
        <TextField select label="Instruction action" value={operation} onChange={(e) => { setOperation(e.target.value); setReference(''); }}>{[['rubric','Create reusable rubric'],['attach_rubric','Attach rubric to assignment'],['curriculum','Link assignment objective'],['copy_plan','Reuse a lesson plan'],['deadline','Individual makeup deadline'],['resource','Add accessible resource'],['mastery','Record dated mastery evidence']].map(([value,name]) => <MenuItem key={value} value={value}>{name}</MenuItem>)}</TextField>
        <TextField select label="Instruction classroom" value={section} onChange={(e) => { setSection(e.target.value); setAssignment(''); }}><MenuItem value="">Choose classroom</MenuItem>{sections.map((s) => <MenuItem key={s.id} value={s.id}>{s['course__name'] || s.id}</MenuItem>)}</TextField>
        {needsAssignment && <TextField select label="Instruction assignment" value={assignment} onChange={(e) => setAssignment(e.target.value)}><MenuItem value="">Choose assignment</MenuItem>{[...new Map(assignments.filter((a) => a.section_id === section).map((a) => [a.id,a])).values()].map((a) => <MenuItem key={a.id} value={a.id}>{a.name}</MenuItem>)}</TextField>}
        {['deadline','mastery'].includes(operation) && <TextField select label="Instruction student" value={student} onChange={(e) => setStudent(e.target.value)}><MenuItem value="">Choose student</MenuItem>{students.map((s) => <MenuItem key={s.id} value={s.id}>{s.first_name} {s.last_name}</MenuItem>)}</TextField>}
        {['attach_rubric','curriculum','copy_plan','resource'].includes(operation) && <TextField select label="Instruction reference" value={reference} onChange={(e) => setReference(e.target.value)}><MenuItem value="">Choose reference</MenuItem>{references.map((r) => <MenuItem key={r.id} value={r.id}>{r.title || r.objective_code || `${r.plan_date}: ${r.objectives}`}</MenuItem>)}</TextField>}
        {['rubric','resource'].includes(operation) && <TextField label="Instruction title" value={title} onChange={(e) => setTitle(e.target.value)} />}
        {operation === 'rubric' && <><TextField label="Criterion name" value={reference} onChange={(e) => setReference(e.target.value)} /><TextField multiline label="Criterion description" value={description} onChange={(e) => setDescription(e.target.value)} /><TextField multiline minRows={3} label="Performance descriptions, one per line (2–6)" value={levels} onChange={(e) => setLevels(e.target.value)} /><Button disabled={!reference.trim() || !description.trim() || levels.split('\n').filter((v) => v.trim()).length < 2 || criteria.length >= 12} onClick={() => { setCriteria([...criteria, { name: reference, description, levels: levels.split('\n').filter((v) => v.trim()) }]); setReference(''); setDescription(''); setLevels(''); }}>Add criterion to rubric</Button>{criteria.map((c,i) => <Box key={`${c.name}-${i}`}><Typography>{c.name}: {c.description}</Typography><Button onClick={() => setCriteria(criteria.filter((_,index) => index !== i))}>Remove {c.name}</Button></Box>)}</>}
        {['copy_plan','deadline'].includes(operation) && <TextField type="date" label="Instruction date" InputLabelProps={{ shrink: true }} value={date} onChange={(e) => setDate(e.target.value)} />}
        {operation === 'deadline' && <TextField multiline label="Private staff reason for deadline" value={reason} onChange={(e) => setReason(e.target.value)} />}
        {operation === 'resource' && <><TextField label="HTTPS learning resource" value={urlValue} onChange={(e) => setUrlValue(e.target.value)} /><TextField multiline label="Accessible resource description" value={description} onChange={(e) => setDescription(e.target.value)} /></>}
        {operation === 'mastery' && <TextField select label="Academic mastery evidence level" value={level} onChange={(e) => setLevel(Number(e.target.value))}>{['Beginning','Developing','Proficient','Advanced'].map((name,i) => <MenuItem key={name} value={i+1}>{name}</MenuItem>)}</TextField>}
        {['deadline','resource','mastery'].includes(operation) && <TextField multiline minRows={3} label={operation === 'deadline' ? 'Student-visible makeup instructions' : operation === 'resource' ? 'Alternative learning instructions' : 'Student- and family-visible mastery evidence'} value={note} onChange={(e) => setNote(e.target.value)} />}
        <Button disabled={busy || !section || (needsAssignment && !assignment) || (operation === 'rubric' && !criteria.length)} onClick={save}>Save instruction change</Button>
      </Stack></details>}
    </>}
  </Box>;
}
ClassroomInstruction.propTypes = { audience: PropTypes.string.isRequired, sections: PropTypes.array.isRequired, students: PropTypes.array.isRequired, assignments: PropTypes.array.isRequired };
