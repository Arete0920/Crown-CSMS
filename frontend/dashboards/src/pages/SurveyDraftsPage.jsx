import { useCallback, useEffect, useRef, useState } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import { getSelectedSchoolId } from '../utils/authClient.js';
import { createSurveyDraft, listSurveyDrafts, readSurveyDraft } from '../api/surveyDrafts.js';
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
  const [uncertain, setUncertain] = useState(false);
  const [name, setName] = useState('');
  const [purpose, setPurpose] = useState('parent_pulse');
  const [rows, setRows] = useState([question('question_1')]);
  const nextKey = useRef(2);
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
    }
    reload();
    return () => { version.current += 1; };
    // Each request is bound to the selected school; stale replies are discarded.
  }, [schoolId, reload]);

  async function select(id) {
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

  function edit(index, changes) { setRows((previous) => previous.map((row, i) => i === index ? { ...row, ...changes } : row)); }
  const payload = asPayload(name, purpose, rows);
  return <CrownLayout title="Survey drafts" subtitle="Prepare school questionnaires and review saved definitions">
    <p>Draft preparation only. Publishing, invitations and response collection require separate approval and are unavailable here.</p>
    {error ? <p role="alert" className="crown-alert">{error}</p> : null}
    {message ? <p role="status">{message}</p> : null}
    <section className="crown-card" style={CARD} aria-label="School survey library">
      <h2>School survey library</h2>
      <button type="button" className="crown-btn" onClick={reload} disabled={busy || loading}>Refresh library</button>
      {loading ? <p role="status">Loading surveys…</p> : null}
      {library && !library.results.length ? <p>No saved surveys for this school.</p> : null}
      {library?.results.length ? <><p>Showing up to 100 saved definitions. Select one to read its current questions.</p><ul>{library.results.map((survey) => <li key={survey.id}>
        <button type="button" onClick={() => select(survey.id)} disabled={busy || loading}>{survey.name} · {survey.status}</button>
      </li>)}</ul></> : null}
    </section>
    {saved ? <Preview survey={saved} heading="Saved survey preview" /> : null}
    {library && !library.can_create ? <p>You have read-only survey access.</p> : null}
    {library?.can_create ? <>
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
