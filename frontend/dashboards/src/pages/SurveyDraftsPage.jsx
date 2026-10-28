import { useCallback, useEffect, useRef, useState } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import { getSelectedSchoolId } from '../utils/authClient.js';
import { createSurveyDraft, listSurveyDrafts, readSurveyDraft, replaceSurveyDraft } from '../api/surveyDrafts.js';
import '../styles/crown-wizard.css';

const PURPOSES = { inquiry: 'Inquiry', post_tour: 'Post-tour', new_family: 'New family', parent_pulse: 'Parent pulse', reenrollment_intent: 'Re-enrollment intent', lost_prospect: 'Lost prospect', exit: 'Exit', custom: 'Custom' };
const TYPES = { scale: 'Rating (1–5)', choice: 'Choose one', multi: 'Choose several', text: 'Written answer', boolean: 'Yes or no' };
const FIELD = { display: 'grid', gap: 6, marginBottom: 16 };
const INPUT = { width: '100%', maxWidth: '100%', boxSizing: 'border-box', padding: 10, font: 'inherit', color: 'var(--crown-text)', background: 'var(--crown-surface)', border: '1px solid var(--crown-border)', borderRadius: 6 };
const CARD = { padding: 20, marginBottom: 20 };
const question = (key) => ({ key, prompt: '', question_type: 'scale', choicesText: '', required: false });
const asPayload = (name, purpose, rows) => ({ name, purpose, questions: rows.map((row) => ({
  key: row.key, prompt: row.prompt, question_type: row.question_type, required: row.required,
  choices: ['choice', 'multi'].includes(row.question_type) ? row.choicesText.split('\n').map((s) => s.trim()).filter(Boolean) : [],
})) });

function canEditSaved(value) {
  return value?.status === 'draft' && /^[0-9a-f]{64}$/.test(value?.revision || '')
    && Array.isArray(value.questions) && value.questions.length > 0;
}

function editorFromSaved(value) {
  return {
    id: value.id, revision: value.revision, name: value.name, purpose: value.purpose,
    rows: value.questions.map((row) => ({
      key: row.key, prompt: row.prompt, question_type: row.question_type,
      choicesText: Array.isArray(row.choices) ? row.choices.join('\n') : '',
      required: row.required === true,
    })),
  };
}

function draftValidationError(draft) {
  if (!draft.name.trim() || draft.name.trim().length > 180) return 'Enter a survey name of 1 to 180 characters.';
  if (draft.questions.length < 1 || draft.questions.length > 40) return 'Provide 1 to 40 questions.';
  const keys = new Set();
  for (const row of draft.questions) {
    if (!/^[a-z][a-z0-9_]{0,63}$/.test(row.key) || keys.has(row.key)) return 'Question keys must be distinct.';
    keys.add(row.key);
    if (!row.prompt.trim() || row.prompt.trim().length > 300) return 'Each question needs text of 1 to 300 characters.';
    if (['choice', 'multi'].includes(row.question_type)) {
      if (row.choices.length < 2 || row.choices.length > 40
          || row.choices.some((choice) => !choice.trim() || choice.trim().length > 120)
          || new Set(row.choices.map((choice) => choice.trim().normalize('NFC').toLowerCase())).size !== row.choices.length) {
        return 'Choice questions require 2 to 40 distinct options of 1 to 120 characters.';
      }
    }
  }
  return '';
}

function Preview({ survey, heading }) {
  return <section className="crown-card" style={CARD} aria-label={heading}>
    <h2>{heading}</h2><h3>{survey.name || 'Untitled survey'}</h3>
    <p>{PURPOSES[survey.purpose] || survey.purpose}{survey.status ? ` · ${survey.status}` : ''}</p>
    <ol>{survey.questions.map((row) => <li key={row.key} style={{ marginBottom: 16 }}>
      <strong>{row.prompt || 'Question text'}{row.required ? ' (required)' : ''}</strong>
      <p>{TYPES[row.question_type] || row.question_type}</p>
      {row.choices?.length ? <ul>{row.choices.map((choice, index) => <li key={index}>{choice}</li>)}</ul> : null}
    </li>)}</ol>
    <p className="crown-muted">Preview only. No answers are collected here.</p>
  </section>;
}

export default function SurveyDraftsPage() {
  const schoolId = getSelectedSchoolId();
  const [library, setLibrary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [saved, setSaved] = useState(null);
  const [editing, setEditing] = useState(null);
  const [editGate, setEditGate] = useState('');
  const [editLatest, setEditLatest] = useState(null);
  const [editError, setEditError] = useState('');
  const [uncertain, setUncertain] = useState(false);
  const [name, setName] = useState('');
  const [purpose, setPurpose] = useState('parent_pulse');
  const [rows, setRows] = useState([question('question_1')]);
  const nextKey = useRef(2);
  const editNextKey = useRef(1);
  const pending = useRef(false);
  const version = useRef(0);
  const scope = useRef(schoolId);

  const reload = useCallback(async () => {
    const current = ++version.current;
    setLoading(true); setError(''); setSaved(null); setLibrary(null);
    try {
      const result = await listSurveyDrafts(schoolId);
      if (current === version.current) { setLibrary(result); setUncertain(false); }
    } catch (failure) {
      if (current === version.current) setError(failure?.status === 403 ? 'You do not have permission to view school surveys.' : 'Survey drafts could not be loaded. Check your school selection and try again.');
    } finally { if (current === version.current) setLoading(false); }
  }, [schoolId]);

  useEffect(() => {
    if (scope.current !== schoolId) {
      scope.current = schoolId;
      setName(''); setPurpose('parent_pulse');
      setRows([question(`question_${nextKey.current++}`)]);
      setMessage(''); setUncertain(false);
      setEditing(null); setEditGate(''); setEditLatest(null); setEditError('');
    }
    reload();
    return () => { version.current += 1; };
    // Each request is bound to the selected school; stale replies are discarded.
  }, [schoolId, reload]);

  async function select(id) {
    if (editing || pending.current) return;
    const current = ++version.current;
    setSaved(null); setError(''); setLoading(true);
    try {
      const result = await readSurveyDraft(schoolId, id);
      if (current === version.current) setSaved(result);
    } catch {
      if (current === version.current) setError('The selected survey could not be loaded. Refresh the library before continuing.');
    } finally { if (current === version.current) setLoading(false); }
  }

  async function save(event) {
    event.preventDefault();
    if (pending.current || !library?.can_create || uncertain) return;
    pending.current = true; setBusy(true); setError(''); setMessage('');
    const current = ++version.current;
    try {
      const result = await createSurveyDraft(schoolId, asPayload(name, purpose, rows));
      if (current !== version.current) return;
      setSaved(result); setLibrary((old) => ({ ...old, results: [result, ...old.results].slice(0, 100) }));
      setName(''); setRows([question(`question_${nextKey.current++}`)]);
      setMessage('Draft saved. It is not published and cannot collect responses.');
    } catch (failure) {
      if (current !== version.current) return;
      if (failure?.status === 400) setError('The draft was rejected. Check its name, question text and distinct choices before saving again.');
      else if (failure?.status === 403) { setLibrary((old) => ({ ...old, can_create: false })); setError('You do not have permission to create surveys for this school.'); }
      else { setUncertain(true); setError('Saving could not be confirmed. Refresh the library and check for the draft before trying again. Your text is still here.'); }
    } finally { pending.current = false; setBusy(false); }
  }

  function startEdit() {
    if (!library?.can_create || !canEditSaved(saved) || pending.current) return;
    editNextKey.current = 1;
    setEditing(editorFromSaved(saved));
    setEditGate(''); setEditLatest(null); setEditError(''); setMessage(''); setError('');
  }

  function cancelEdit() {
    if (pending.current) return;
    version.current += 1; // Discard any in-flight comparison readback.
    if (editLatest) setSaved(editLatest);
    setLoading(false);
    setEditing(null); setEditGate(''); setEditLatest(null); setEditError('');
  }

  function editSavedRow(index, changes) {
    setEditing((previous) => previous && ({
      ...previous, rows: previous.rows.map((row, i) => i === index ? { ...row, ...changes } : row),
    }));
  }

  function addSavedQuestion() {
    setEditing((previous) => {
      if (!previous || previous.rows.length >= 40) return previous;
      let key;
      do { key = `question_${editNextKey.current++}`; }
      while (previous.rows.some((row) => row.key === key));
      return { ...previous, rows: [...previous.rows, question(key)] };
    });
  }

  async function saveChanges(event) {
    event.preventDefault();
    if (!editing || pending.current || !library?.can_create || editGate) return;
    const draft = asPayload(editing.name, editing.purpose, editing.rows);
    const validationError = draftValidationError(draft);
    if (validationError) { setEditError(validationError); return; }
    pending.current = true; setBusy(true); setEditError(''); setError(''); setMessage('');
    const current = ++version.current;
    try {
      const result = await replaceSurveyDraft(schoolId, editing.id, editing.revision, draft);
      if (current !== version.current) return;
      setSaved(result);
      setLibrary((old) => ({ ...old, results: old.results.map((item) => item.id === result.id ? result : item) }));
      setEditing(null); setEditGate(''); setEditLatest(null);
      setMessage('Saved changes to this draft. It is not published and cannot collect responses.');
    } catch (failure) {
      if (current !== version.current) return;
      if (failure?.status === 400) {
        setEditError('The changes were rejected. Check the survey name, questions and distinct choices.');
      } else if (failure?.status === 412 || failure?.status === 428) {
        setEditGate('stale');
        setEditError('This draft has a stale revision. Your changes are preserved. Check the latest saved version; no overwrite was attempted.');
      } else if (failure?.status === 409) {
        setEditGate('blocked');
        setEditError('This survey is no longer eligible for editing (it may have been published or received responses). Your changes were not saved.');
      } else if ([401, 403, 404].includes(failure?.status)) {
        setEditGate('blocked');
        setEditError('This draft is no longer accessible for editing. Your changes were not confirmed.');
      } else {
        setEditGate('uncertain');
        setEditError('The save result is unknown. Do not retry. Check the latest saved version before continuing; your edits are preserved.');
      }
    } finally { pending.current = false; setBusy(false); }
  }

  async function checkLatest() {
    if (!editing || pending.current) return;
    const serverBlocked = editGate === 'blocked';
    const current = ++version.current;
    setLoading(true); setEditError('');
    try {
      const latest = await readSurveyDraft(schoolId, editing.id);
      if (current !== version.current) return;
      setEditLatest(latest); setEditGate(serverBlocked ? 'blocked' : 'review');
      setEditError(serverBlocked
        ? 'The server denied editing this survey. Readback is for comparison only; cancel editing to leave.'
        : canEditSaved(latest)
          ? 'Compare the current saved version below with your unsaved edits. To continue, explicitly discard your edits and use the latest revision.'
          : 'The current saved survey cannot be edited. Your unsaved changes remain visible until you cancel.');
    } catch {
      if (current === version.current) {
        setEditGate(serverBlocked ? 'blocked' : 'uncertain');
        setEditError('The latest saved survey could not be read. Editing remains blocked; try checking again.');
      }
    } finally { if (current === version.current) setLoading(false); }
  }

  function useLatest() {
    if (editGate !== 'review' || !editLatest || !canEditSaved(editLatest) || !library?.can_create || pending.current || loading) return;
    editNextKey.current = 1;
    setSaved(editLatest); setEditing(editorFromSaved(editLatest));
    setLibrary((old) => ({ ...old, results: old.results.map((item) => item.id === editLatest.id ? editLatest : item) }));
    setEditGate(''); setEditLatest(null); setEditError('');
  }

  function edit(index, changes) { setRows((previous) => previous.map((row, i) => i === index ? { ...row, ...changes } : row)); }
  const payload = asPayload(name, purpose, rows);
  return <CrownLayout title="Survey drafts" subtitle="Prepare school questionnaires and review saved definitions">
    <p>Draft preparation only. Publishing, invitations and response collection require separate approval and are unavailable here.</p>
    {error ? <p role="alert" className="crown-alert">{error}</p> : null}
    {message ? <p role="status">{message}</p> : null}
    <section className="crown-card" style={CARD} aria-label="School survey library">
      <h2>School survey library</h2>
      <button type="button" className="crown-btn" onClick={reload} disabled={busy || loading || !!editing}>Refresh library</button>
      {loading ? <p role="status">Loading surveys…</p> : null}
      {library && !library.results.length ? <p>No saved surveys for this school.</p> : null}
      {library?.results.length ? <><p>Showing up to 100 saved definitions. Select one to read its current questions.</p><ul>{library.results.map((survey) => <li key={survey.id}>
        <button type="button" onClick={() => select(survey.id)} disabled={busy || loading || !!editing}>{survey.name} · {survey.status}</button>
      </li>)}</ul></> : null}
    </section>
    {saved ? <Preview survey={saved} heading="Saved survey preview" /> : null}
    {saved && library?.can_create && !editing ? <>
      <button type="button" className="crown-btn" onClick={startEdit} disabled={!canEditSaved(saved) || busy || loading}>Edit saved draft</button>
      {!canEditSaved(saved) ? <p>Editing is available only for saved draft definitions with a current revision. Published and non-draft surveys cannot be edited here.</p> : null}
    </> : null}
    {editing ? <>
      <form className="crown-card" style={CARD} onSubmit={saveChanges} aria-label="Edit saved survey draft">
        <h2>Edit saved draft</h2>
        <p>Only eligible unpublished, response-free drafts can be saved. Changing a survey never publishes it.</p>
        {editError ? <p className="crown-alert" role="alert">{editError}</p> : null}
        <fieldset disabled={busy || loading || !!editGate} style={{ border: 0, padding: 0, minWidth: 0 }}>
          <label style={FIELD}>Survey name<input style={INPUT} maxLength={180} required value={editing.name} onChange={(e) => setEditing((old) => ({ ...old, name: e.target.value }))} /></label>
          <label style={FIELD}>Purpose<select style={INPUT} value={editing.purpose} onChange={(e) => setEditing((old) => ({ ...old, purpose: e.target.value }))}>{Object.entries(PURPOSES).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
          {editing.rows.map((row, index) => <fieldset key={row.key} style={{ marginBottom: 20 }}>
            <legend>Question {index + 1}</legend>
            <label style={FIELD}>Question text<textarea style={INPUT} maxLength={300} required value={row.prompt} onChange={(e) => editSavedRow(index, { prompt: e.target.value })} /></label>
            <label style={FIELD}>Answer type<select style={INPUT} value={row.question_type} onChange={(e) => editSavedRow(index, { question_type: e.target.value })}>{Object.entries(TYPES).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
            {['choice', 'multi'].includes(row.question_type) ? <label style={FIELD}>Choices (one per line, 2-40 distinct choices)<textarea style={INPUT} value={row.choicesText} required onChange={(e) => editSavedRow(index, { choicesText: e.target.value })} /></label> : null}
            <label><input type="checkbox" checked={row.required} onChange={(e) => editSavedRow(index, { required: e.target.checked })} /> Required question</label>{' '}
            <button type="button" disabled={editing.rows.length === 1} onClick={() => setEditing((old) => ({ ...old, rows: old.rows.filter((item) => item.key !== row.key) }))}>Remove question {index + 1}</button>
          </fieldset>)}
          <button type="button" className="crown-btn" disabled={editing.rows.length >= 40} onClick={addSavedQuestion}>Add question</button>{' '}
          <button type="submit" className="crown-btn" disabled={busy || loading || !!editGate}>{busy ? 'Saving changes...' : 'Save changes'}</button>
        </fieldset>
        <button type="button" className="crown-btn" onClick={cancelEdit} disabled={busy}>Cancel editing</button>{' '}
        {editGate ? <button type="button" className="crown-btn" onClick={checkLatest} disabled={busy || loading}>Check latest saved version</button> : null}
      </form>
      <Preview survey={{ ...asPayload(editing.name, editing.purpose, editing.rows), status: 'draft' }} heading="Unsaved changes preview" />
      {editLatest ? <Preview survey={editLatest} heading="Current saved survey (server)" /> : null}
      {editGate === 'review' && editLatest && canEditSaved(editLatest) ? <button type="button" className="crown-btn" onClick={useLatest} disabled={busy || loading}>Discard my edits and use latest saved version</button> : null}
    </> : null}
    {library && !library.can_create ? <p>You have read-only survey access.</p> : null}
    {library?.can_create && !editing ? <>
      <form className="crown-card" style={CARD} onSubmit={save} aria-label="Create survey draft">
        <h2>Create a draft</h2>
        <fieldset disabled={busy || loading} style={{ border: 0, padding: 0, minWidth: 0 }}>
          <label style={FIELD}>Survey name<input style={INPUT} value={name} maxLength={180} required onChange={(e) => setName(e.target.value)} /></label>
          <label style={FIELD}>Purpose<select style={INPUT} value={purpose} onChange={(e) => setPurpose(e.target.value)}>{Object.entries(PURPOSES).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
          {rows.map((row, index) => <fieldset key={row.key} style={{ marginBottom: 20 }}>
            <legend>Question {index + 1}</legend>
            <label style={FIELD}>Question text<textarea style={INPUT} value={row.prompt} maxLength={300} required onChange={(e) => edit(index, { prompt: e.target.value })} /></label>
            <label style={FIELD}>Answer type<select style={INPUT} value={row.question_type} onChange={(e) => edit(index, { question_type: e.target.value })}>{Object.entries(TYPES).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
            {['choice', 'multi'].includes(row.question_type) ? <label style={FIELD}>Choices (one per line, 2–40 distinct choices)<textarea style={INPUT} value={row.choicesText} required onChange={(e) => edit(index, { choicesText: e.target.value })} /></label> : null}
            <label><input type="checkbox" checked={row.required} onChange={(e) => edit(index, { required: e.target.checked })} /> Required question</label>{' '}
            <button type="button" disabled={rows.length === 1} onClick={() => setRows((old) => old.filter((item) => item.key !== row.key))}>Remove question {index + 1}</button>
          </fieldset>)}
          <button type="button" className="crown-btn" disabled={rows.length >= 40} onClick={() => setRows((old) => [...old, question(`question_${nextKey.current++}`)])}>Add question</button>{' '}
          <button type="submit" className="crown-btn" disabled={uncertain}>{busy ? 'Saving…' : 'Save draft'}</button>
        </fieldset>
      </form>
      <Preview survey={payload} heading="Draft preview" />
    </> : null}
  </CrownLayout>;
}
