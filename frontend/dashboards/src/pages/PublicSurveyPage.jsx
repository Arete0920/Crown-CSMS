import { useEffect, useState } from 'react';
import { useParams } from 'react-router';
import CrownLayout from '../components/crown/CrownLayout.jsx';

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

  if (state === 'loading') return <CrownLayout publicMode title="Survey"><p>Loading survey…</p></CrownLayout>;
  if (state === 'error') return <CrownLayout publicMode title="Survey unavailable"><p>{message}</p></CrownLayout>;
  if (state === 'done') return <CrownLayout publicMode title="Thank you"><p>Your response has been recorded.</p></CrownLayout>;

  return (
    <CrownLayout
      publicMode
      title={survey.name}
      subtitle="Your feedback helps the school improve enrollment, family experience, affordability planning, and retention."
    >
      <div className="crown-card" style={{ padding: 24, maxWidth: 720 }}>
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
          ) : q.question_type === 'multi' ? (
            <div style={{ display: 'grid', gap: 6 }}>
              {(q.choices || []).map((v) => {
                const selected = Array.isArray(answers[q.key]) ? answers[q.key] : [];
                return (
                  <label key={v} style={{ fontWeight: 400 }}>
                    <input
                      type="checkbox"
                      checked={selected.includes(v)}
                      onChange={(e) => setAnswers((a) => ({
                        ...a,
                        [q.key]: e.target.checked
                          ? [...selected, v]
                          : selected.filter((item) => item !== v),
                      }))}
                    />{' '}
                    {v.replaceAll('_',' ')}
                  </label>
                );
              })}
            </div>
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
      </div>
    </CrownLayout>
  );
}

const input = { padding: 10, border: '1px solid var(--crown-border)', borderRadius: 6, font: 'inherit' };
const button = { padding: '11px 20px', border: 0, borderRadius: 6, background: 'var(--crown-brand)', color: 'var(--crown-surface)', fontWeight: 700, cursor: 'pointer' };
