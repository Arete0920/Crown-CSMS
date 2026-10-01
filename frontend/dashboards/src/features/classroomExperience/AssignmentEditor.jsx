import { useState } from 'react';
import PropTypes from 'prop-types';
import { Alert, Button, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { crownApiClient as api } from '../../api/client';

export default function AssignmentEditor({ sections, categories, refresh }) {
  const [section, setSection] = useState('');
  const [category, setCategory] = useState('');
  const [fields, setFields] = useState({ name: '', purpose: '', instructions: '', success_criteria: '', home_support: '', due_date: '', points_possible: '10' });
  const [published, setPublished] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function save() {
    setBusy(true); setError('');
    try {
      await api.post(`/api/v1/academics/sections/${section}/assignments/`, { ...fields, due_date: fields.due_date || null, category_id: category, is_published: published });
      await refresh();
    } catch (err) { setError(String(err.response?.data?.detail || 'Assignment was not confirmed. Check the classroom records before retrying.')); }
    finally { setBusy(false); }
  }
  return <Stack spacing={1} sx={{ my: 2 }}>
    <Typography component="h3" variant="h6">Prepare a clear assignment</Typography>
    {error && <Alert severity="warning">{error}</Alert>}
    <TextField select label="Assignment section" value={section} onChange={(e) => { setSection(e.target.value); setCategory(''); }}><MenuItem value="">Choose section</MenuItem>{sections.map((s) => <MenuItem key={s.id} value={s.id}>{s.course__name} ({s.term})</MenuItem>)}</TextField>
    <TextField select label="Assignment category" value={category} onChange={(e) => setCategory(e.target.value)}><MenuItem value="">Choose category</MenuItem>{categories.filter((c) => c.section_id === section && c.is_active).map((c) => <MenuItem key={c.id} value={c.id}>{c.name} · {c.weight_percent}% weight</MenuItem>)}</TextField>
    {Object.entries({ name: 'Assignment name', purpose: 'Learning purpose', instructions: 'Directions and materials', success_criteria: 'Success criteria or rubric', home_support: 'How families can help', points_possible: 'Possible points' }).map(([key, label]) => <TextField key={key} label={label} value={fields[key]} multiline={key !== 'name' && key !== 'points_possible'} onChange={(e) => setFields((f) => ({ ...f, [key]: e.target.value }))} />)}
    <TextField type="date" label="Due date" slotProps={{ inputLabel: { shrink: true } }} value={fields.due_date} onChange={(e) => setFields((f) => ({ ...f, due_date: e.target.value }))} />
    <TextField select label="Publication" value={published ? 'published' : 'draft'} onChange={(e) => setPublished(e.target.value === 'published')}><MenuItem value="draft">Draft — teachers only</MenuItem><MenuItem value="published">Published — visible to enrolled families</MenuItem></TextField>
    <Button variant="contained" disabled={busy || !section || !category || !fields.name.trim()} onClick={save}>Save assignment</Button>
  </Stack>;
}
AssignmentEditor.propTypes = { sections: PropTypes.array.isRequired, categories: PropTypes.array.isRequired, refresh: PropTypes.func.isRequired };
