import { useEffect, useState } from 'react';
import { useParams } from 'react-router';

export default function PublicSurveyPage() {
  const { token } = useParams();
  const [survey, setSurvey] = useState(null);
  const [answers, setAnswers] = useState({});
  const [state, setState] = useState('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetch(`/api/v1/survey-sentiment/public/${token}/`)
      .then(async (response) => {
        const body = await response.json();
        if (!response.ok) throw new Error(body.detail || 'Survey unavailable.');
        setSurvey(body); setState('ready');
      })
      .catch((e) => { setMessage(e.message); setState('error'); });
  }, [token]);

  const submit = async () => {
    setState('submitting'); setMessage('');
    const response = await fetch(`/api/v1/survey-sentiment/public/${token}/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answers }),
    });
    const body = await response.json();
    if (!response.ok) { setMessage(body.detail || 'Unable to submit survey.'); setState('ready'); return; }
    setState('done');
  };

  if (state === 'loading') return <main style={shell}><p>Loading survey…</p></main>;
  if (state === 'error') return <main style={shell}><h1>Survey unavailable</h1><p>{message}</p></main>;
  if (state === 'done') return <main style={shell}><h1>Thank you</h1><p>Your response has been recorded.</p></main>;

  return (
    <main style={shell}>
      <h1>{survey.name}</h1>
      <p>Your feedback helps the school improve enrollment, family experience, affordability planning, and retention.</p>
      {(survey.questions || []).map((q) => (
        <label key={q.key} style={{ display: 'grid', gap: 7, margin: '20px 0', fontWeight: 600 }}>
          {q.prompt}{q.required ? ' *' : ''}
          {q.question_type === 'scale' ? (
            <select value={answers[q.key] ?? ''} onChange={(e) => setAnswers((a) => ({ ...a, [q.key]: Number(e.target.value) }))} style={input}>
              <option value="">Select</option>{[1,2,3,4,5].map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          ) : q.question_type === 'choice' ? (
            <select value={answers[q.key] ?? ''} onChange={(e) => setAnswers((a) => ({ ...a, [q.key]: e.target.value }))} style={input}>
              <option value="">Select</option>{(q.choices || []).map((v) => <option key={v} value={v}>{v.replaceAll('_',' ')}</option>)}
            </select>
          ) : q.question_type === 'boolean' ? (
            <select value={answers[q.key] ?? ''} onChange={(e) => setAnswers((a) => ({ ...a, [q.key]: e.target.value === 'yes' }))} style={input}>
              <option value="">Select</option><option value="yes">Yes</option><option value="no">No</option>
            </select>
          ) : (
            <textarea rows={4} value={answers[q.key] ?? ''} onChange={(e) => setAnswers((a) => ({ ...a, [q.key]: e.target.value }))} style={input} />
          )}
        </label>
      ))}
      {message && <p>{message}</p>}
      <button onClick={submit} disabled={state === 'submitting'} style={button}>{state === 'submitting' ? 'Submitting…' : 'Submit Survey'}</button>
    </main>
  );
}

const shell = { maxWidth: 720, margin: '40px auto', padding: 28, fontFamily: 'system-ui, sans-serif' };
const input = { padding: 10, border: '1px solid #bbb', borderRadius: 6, font: 'inherit' };
const button = { padding: '11px 20px', border: 0, borderRadius: 6, background: '#23395d', color: 'white', fontWeight: 700, cursor: 'pointer' };
