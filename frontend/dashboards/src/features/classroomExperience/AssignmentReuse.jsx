import { useState } from 'react';
import PropTypes from 'prop-types';
import { Alert, Button, MenuItem, Stack, TextField } from '@mui/material';
import { crownApiClient as api } from '../../api/client';
export default function AssignmentReuse({ assignment, sections, categories, refresh }) {
  const [section, setSection] = useState('');
  const [category, setCategory] = useState('');
  const [name, setName] = useState(assignment.name);
  const [due, setDue] = useState(assignment.due_date || '');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  return <Stack spacing={1} sx={{ mt: 2 }}>
    {error && <Alert severity="warning">{error}</Alert>}
    <TextField select label="Reuse in section" value={section} onChange={(e) => { setSection(e.target.value); setCategory(''); }}><MenuItem value="">Choose section</MenuItem>{sections.map((s) => <MenuItem key={s.id} value={s.id}>{s.course__name} ({s.term})</MenuItem>)}</TextField>
    <TextField select label="Reuse category" value={category} onChange={(e) => setCategory(e.target.value)}><MenuItem value="">Choose category</MenuItem>{categories.filter((c) => c.section_id === section && c.is_active).map((c) => <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>)}</TextField>
    <TextField label="Copied assignment name" value={name} onChange={(e) => setName(e.target.value)} />
    <TextField label="Copied due date" type="date" slotProps={{ inputLabel: { shrink: true } }} value={due} onChange={(e) => setDue(e.target.value)} />
    <Button disabled={busy || !section || !category || !name.trim()} onClick={async () => { setBusy(true); setError(''); try { await api.post(`/api/v1/academics/assignments/${assignment.id}/copy/`, { name, targets: [{ section_id: section, category_id: category, due_date: due || null }] }); await refresh(); } catch (err) { setError(String(err.response?.data?.detail || 'Copy was not confirmed. Check assignments before retrying.')); } finally { setBusy(false); } }}>Copy as a draft</Button>
  </Stack>;
}
AssignmentReuse.propTypes = { assignment: PropTypes.object.isRequired, sections: PropTypes.array.isRequired, categories: PropTypes.array.isRequired, refresh: PropTypes.func.isRequired };
