import ClassroomFamily from './ClassroomFamily.jsx';
import ClassroomRecords from './ClassroomRecords.jsx';
import AssignmentReuse from './AssignmentReuse.jsx';
import AssignmentWork from './AssignmentWork.jsx';
import AssignmentEditor from './AssignmentEditor.jsx';
import { useCallback, useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { Alert, Box, Button, Card, CardContent, FormControl, InputLabel, MenuItem, Select, Stack, TextField, Typography } from '@mui/material';
import { crownApiClient as api } from '../../api/client';

const labels = { teacher: "Today's Classroom", student: 'My Classroom', parent: 'My Children’s Classrooms', admin: 'Classroom Operations', board: 'Classroom Evidence' };
const statuses = { assigned: 'Assigned', draft: 'Draft — not visible to families', awaiting_grading: 'Submitted — awaiting grading', graded: 'Graded', grade_conflict: 'Grade records disagree — teacher review required', returned: 'Returned for revision', missing: 'Marked missing', overdue_unconfirmed: 'Past due — submission not confirmed' };

export default function ClassroomWorkspace({ audience }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [term, setTerm] = useState('');
  const [student, setStudent] = useState('');
  const [openWork, setOpenWork] = useState('');
  const [section, setSection] = useState('');
  const load = useCallback(async (signal) => {
    setLoading(true);
    setError('');
    setData(null);
    try {
      const response = await api.get('/api/v1/academics/classroom/workspace/', { params: { audience, term, student_id: student || undefined, section_id: section || undefined }, signal });
      const payload = response.data;
      const arrays = audience === 'board' ? ['terms', 'limitations'] : ['terms', 'limitations', 'sections', 'students', 'assignments', 'lesson_plans'];
      if (!payload || payload.source !== 'live' || arrays.some((key) => !Array.isArray(payload[key]))
          || (audience === 'board' && (!payload.summary || typeof payload.summary.definitions !== 'object'))) {
        throw new Error('Invalid classroom record contract');
      }
      if (!signal?.aborted) setData(payload);
    } catch (err) {
      if (!signal?.aborted) setError(err.response?.data?.detail || 'Classroom records could not be loaded. Retry or contact your school.');
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, [audience, term, student, section]);
  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    return () => controller.abort();
  }, [load]);
  return <Box component="section" aria-label={labels[audience]} sx={{ p: 2 }}>
    <Stack direction="row" justifyContent="space-between" alignItems="center" gap={2}>
      <Typography variant="h5" component="h2">{labels[audience]}</Typography>
      <Button onClick={() => load()} disabled={loading}>Refresh classroom records</Button>
    </Stack>
    {loading && <Typography role="status">Loading classroom records…</Typography>}
    {error && <Alert severity="warning">{String(error)}</Alert>}
    {data && <>
      <Typography variant="body2">Reporting window: {data.from} through {data.to}. Updated {new Date(data.generated_at).toLocaleString()}.</Typography>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ my: 2 }}>
        <FormControl fullWidth><InputLabel id={`classroom-term-${audience}`}>Term</InputLabel>
          <Select labelId={`classroom-term-${audience}`} label="Term" value={term} onChange={(e) => { setTerm(e.target.value); setSection(''); }}>
            <MenuItem value="">All recorded terms</MenuItem>{data.terms.map((v) => <MenuItem key={v} value={v}>{v}</MenuItem>)}
          </Select></FormControl>
        {audience !== 'board' && <TextField select fullWidth label="Section" value={section} onChange={(e) => setSection(e.target.value)}>
          <MenuItem value="">All authorized sections</MenuItem>{data.sections.map((s) => <MenuItem key={s.id} value={s.id}>{s.course__name} ({s.term})</MenuItem>)}
        </TextField>}
        {audience === 'parent' && <TextField select fullWidth label="Child" value={student} onChange={(e) => setStudent(e.target.value)}>
          <MenuItem value="">All authorized children</MenuItem>{data.students.map((s) => <MenuItem key={s.id} value={s.id}>{s.first_name} {s.last_name}</MenuItem>)}
        </TextField>}
      </Stack>
      {audience === 'board' ? <Card><CardContent>
        <Typography component="h3" variant="h6">Recorded classroom operations</Typography>
        <dl>{Object.entries(data.summary).filter(([, v]) => typeof v === 'number').map(([k, v]) => <div key={k}><dt>{k.replaceAll('_', ' ')}</dt><dd>{v}</dd></div>)}</dl>
        {Object.entries(data.summary.definitions).map(([key, value]) => <Typography variant="body2" key={key}>{value}</Typography>)}
        <Typography>No classroom quality score is inferred from these counts.</Typography>
      </CardContent></Card> : <>
        <Typography component="h3" variant="h6">Assignments and workload</Typography>
        {data.can_manage && <details><summary>Create an assignment</summary><AssignmentEditor sections={data.sections} categories={data.categories} refresh={() => load()} /></details>}
        {data.truncated && <Alert severity="info">This view reached its record limit. Select a section or child to narrow the results.</Alert>}
        {!data.assignments.length && <Typography>No assignments recorded in this window for this selection.</Typography>}
        <Stack spacing={1} sx={{ my: 2 }}>{data.assignments.map((a) => <Card key={`${a.id}-${a.student_id || 'section'}`}><CardContent>
          <Typography component="h4" variant="subtitle1">{a.name}</Typography>
          <Typography>{a.course} · {a.due_date ? `Due ${a.due_date}` : 'Due date not set'}</Typography>
          {a.student_id && <Typography>{data.students.find((s) => s.id === a.student_id)?.first_name || 'Student'}</Typography>}
          <Typography>{statuses[a.state] || a.state}</Typography>
          {a.submitted_at && <Typography>Submission recorded {new Date(a.submitted_at).toLocaleString()}</Typography>}
          {a.points_earned !== null && <Typography>Recorded points: {a.points_earned} / {a.points_possible}</Typography>}
          {['purpose', 'instructions', 'success_criteria', 'home_support'].map((key) => a[key] && <Typography key={key} sx={{ whiteSpace: 'pre-wrap' }}>{key.replaceAll('_', ' ')}: {a[key]}</Typography>)}
          {data.can_manage && <details><summary>Reuse this assignment</summary><AssignmentReuse assignment={a} sections={data.sections} categories={data.categories} refresh={() => load()} /></details>}
          <Button onClick={() => setOpenWork(openWork === `${a.id}-${a.student_id || 'section'}` ? '' : `${a.id}-${a.student_id || 'section'}`)}>Open work and feedback</Button>
          {openWork === `${a.id}-${a.student_id || 'section'}` && <AssignmentWork assignment={a} audience={audience} students={data.students} />}
          <Typography variant="body2">{a.category} · {a.points_possible} possible points</Typography>
        </CardContent></Card>)}</Stack>
        {audience !== 'student' && <ClassroomFamily audience={audience} sections={data.sections} students={data.students} assignments={data.assignments} />}
      <ClassroomRecords audience={audience} sections={data.sections} students={data.students} assignments={data.assignments} />
        <Typography component="h3" variant="h6">Learning and absence recovery</Typography>
        {!data.lesson_plans.length && <Typography>No lesson plans recorded in this window.</Typography>}
        {data.lesson_plans.map((p) => <Card key={p.id} sx={{ my: 1 }}><CardContent>
          <Typography component="h4" variant="subtitle1">{p.plan_date} · {data.sections.find((s) => s.id === p.section_id)?.course__name}</Typography>
          {['objectives', 'materials', 'activities', 'homework'].map((key) => <Box key={key} sx={{ whiteSpace: 'pre-wrap', mb: 1 }}><Typography component="strong">{key[0].toUpperCase() + key.slice(1)}: </Typography>{p[key] || 'Not recorded'}</Box>)}
        </CardContent></Card>)}
        {data.can_manage && <Stack direction="row" spacing={1} flexWrap="wrap"><Button href="/teacher/attendance">Attendance</Button><Button href="/teacher/lesson-plans/today">Lesson planning</Button><Button href="/academics/teacher-grading">Grading</Button></Stack>}
      </>}
      <Box sx={{ mt: 2 }}>{data.limitations.map((note) => <Typography variant="caption" display="block" key={note}>{note}</Typography>)}</Box>
    </>}
  </Box>;
}
ClassroomWorkspace.propTypes = { audience: PropTypes.oneOf(['teacher', 'student', 'parent', 'admin', 'board']).isRequired };
