import { useEffect, useState } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import { apiFetch } from '../lib/api.js';

const PURPOSES = [
  ['inquiry', 'Inquiry'],
  ['post_tour', 'Post Tour'],
  ['new_family', 'New Family'],
  ['parent_pulse', 'Parent Pulse'],
  ['reenrollment_intent', 'Re-enrollment Intent'],
  ['lost_prospect', 'Lost Prospect'],
  ['exit', 'Exit'],
];

export default function SurveySentimentPage() {
  const [surveys, setSurveys] = useState([]);
  const [purpose, setPurpose] = useState('parent_pulse');
  const [name, setName] = useState('Parent Pulse Survey');
  const [insights, setInsights] = useState(null);
  const [error, setError] = useState('');

  const load = async () => {
    const response = await apiFetch('/api/v1/survey-sentiment/surveys/');
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || 'Unable to load surveys.');
    setSurveys(body.results || []);
  };

  useEffect(() => { load().catch((e) => setError(e.message)); }, []);

  const create = async () => {
    setError('');
    const response = await apiFetch('/api/v1/survey-sentiment/surveys/', {
      method: 'POST',
      body: JSON.stringify({ name, purpose, anonymous_allowed: true }),
    });
    const body = await response.json();
    if (!response.ok) return setError(body.detail || 'Unable to create survey.');
    await load();
  };

  const setState = async (survey, status, publicEnabled) => {
    const response = await apiFetch(`/api/v1/survey-sentiment/surveys/${survey.id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ status, public_enabled: publicEnabled }),
    });
    const body = await response.json();
    if (!response.ok) return setError(body.detail || 'Unable to update survey.');
    await load();
  };

  const loadInsights = async (surveyPurpose) => {
    const response = await apiFetch(`/api/v1/survey-sentiment/insights/?purpose=${encodeURIComponent(surveyPurpose)}`);
    const body = await response.json();
    if (!response.ok) return setError(body.detail || 'Unable to load insights.');
    setInsights({ purpose: surveyPurpose, ...body });
  };

  return (
    <CrownLayout title="Survey Intelligence" subtitle="Retention, affordability, enrollment motivation, and growth research">
      <div style={{ display: 'grid', gap: 18 }}>
        <div className="crown-card" style={{ padding: 22 }}>
          <h2>Create Standard Survey</h2>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr auto', gap: 10, alignItems: 'end' }}>
            <label style={labelStyle}>Name<input value={name} onChange={(e) => setName(e.target.value)} style={inputStyle} /></label>
            <label style={labelStyle}>Purpose<select value={purpose} onChange={(e) => setPurpose(e.target.value)} style={inputStyle}>{PURPOSES.map(([value,label]) => <option key={value} value={value}>{label}</option>)}</select></label>
            <button onClick={create} style={btnStyle}>Create</button>
          </div>
          {error && <p style={{ color: 'var(--crown-danger)' }}>{error}</p>}
        </div>

        <div className="crown-card" style={{ padding: 22 }}>
          <h2>Surveys</h2>
          {surveys.length === 0 ? <p>No surveys configured.</p> : surveys.map((survey) => (
            <div key={survey.id} style={{ padding: '14px 0', borderBottom: '1px solid var(--crown-border)' }}>
              <strong>{survey.name}</strong> · {survey.purpose} · {survey.status}
              <div style={{ marginTop: 8, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {survey.status !== 'active' && <button style={smallBtn} onClick={() => setState(survey, 'active', survey.public_enabled)}>Activate</button>}
                <button style={smallBtn} onClick={() => setState(survey, survey.status, !survey.public_enabled)}>
                  {survey.public_enabled ? 'Disable Public Link' : 'Enable Public Link'}
                </button>
                <button style={smallBtn} onClick={() => loadInsights(survey.purpose)}>View Insights</button>
              </div>
              {survey.public_enabled && survey.status === 'active' && (
                <p style={{ marginTop: 8 }}>
                  Public link: <code>{window.location.origin}/survey/{survey.public_token}</code>
                </p>
              )}
            </div>
          ))}
        </div>

        {insights && (
          <div className="crown-card" style={{ padding: 22 }}>
            <h2>Insights — {insights.purpose}</h2>
            <p>Responses: <strong>{insights.response_count}</strong></p>
            <p>Retention attention: <strong>{insights.retention_attention_recommended ? 'Recommended' : 'No current aggregate signal'}</strong></p>
            <h3>Scale averages</h3>
            <pre style={preStyle}>{JSON.stringify(insights.scale_averages, null, 2)}</pre>
            <h3>Choice counts</h3>
            <pre style={preStyle}>{JSON.stringify(insights.choice_counts, null, 2)}</pre>
            <p>{insights.guardrail}</p>
          </div>
        )}
      </div>
    </CrownLayout>
  );
}

const labelStyle = { display: 'grid', gap: 5, fontWeight: 600 };
const inputStyle = { padding: 9, border: '1px solid var(--crown-border)', borderRadius: 6, font: 'inherit' };
const btnStyle = { padding: '10px 18px', border: 0, borderRadius: 6, background: 'var(--crown-brand)', color: 'white', fontWeight: 700, cursor: 'pointer' };
const smallBtn = { ...btnStyle, padding: '7px 11px', fontSize: 13 };
const preStyle = { whiteSpace: 'pre-wrap', background: 'var(--crown-surface-2)', padding: 12, borderRadius: 6 };
