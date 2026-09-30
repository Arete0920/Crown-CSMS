import { useMemo, useState } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import { apiFetch } from '../lib/api.js';

const SECTIONS = [
  ['school_profile', 'School Profile'],
  ['geography', 'Geography'],
  ['economics', 'Economics & Affordability'],
  ['student_market', 'Student Market'],
  ['competition', 'Competition'],
  ['faith_community', 'Faith & Community'],
  ['enrollment_performance', 'Enrollment Performance'],
  ['financial_profile', 'Tuition & Financial Aid'],
  ['program_capacity', 'Programs & Capacity'],
  ['strategic_objectives', 'Strategic Objectives'],
];

const DEFAULTS = {
  school_profile: { study_name: '', analysis_year: String(new Date().getFullYear()), academic_year_id: '' },
  geography: { primary_market: '', drive_time_minutes: '20', zip_codes: '', geography_notes: '' },
  economics: { median_household_income: '', affordability_notes: '', employment_notes: '', housing_notes: '' },
  student_market: { school_age_population: '', growth_rate_pct: '', age_cohort_notes: '' },
  competition: { competitor_notes: '', private_school_notes: '', public_school_notes: '', homeschool_notes: '' },
  faith_community: { church_count: '', church_notes: '', preschool_feeder_notes: '' },
  enrollment_performance: { current_enrollment: '', market_penetration_notes: '', source_notes: '', retention_notes: '' },
  financial_profile: { annual_tuition: '', aid_budget: '', aid_participation_pct: '', net_tuition_notes: '' },
  program_capacity: { capacity_notes: '', program_opportunities: '', transportation_notes: '' },
  strategic_objectives: { enrollment_goal: '', priorities: '', expansion_questions: '' },
};

function SectionEditor({ value, onChange }) {
  return (
    <div style={{ display: 'grid', gap: 14 }}>
      {Object.entries(value).map(([key, current]) => (
        <label key={key} style={{ display: 'grid', gap: 5, fontWeight: 600 }}>
          {key.replaceAll('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
          {String(key).endsWith('notes') || key === 'priorities' || key === 'expansion_questions' || key === 'program_opportunities' ? (
            <textarea
              value={current}
              onChange={(e) => onChange(key, e.target.value)}
              rows={4}
              style={inputStyle}
            />
          ) : (
            <input value={current} onChange={(e) => onChange(key, e.target.value)} style={inputStyle} />
          )}
        </label>
      ))}
    </div>
  );
}

export default function MarketStudyWizardPage() {
  const [step, setStep] = useState(0);
  const [sessionId, setSessionId] = useState(null);
  const [data, setData] = useState(DEFAULTS);
  const [sources, setSources] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const [sectionKey, sectionLabel] = SECTIONS[step];
  const progress = useMemo(() => Math.round(((step + 1) / SECTIONS.length) * 100), [step]);

  const updateField = (field, value) => {
    setData((prev) => ({ ...prev, [sectionKey]: { ...prev[sectionKey], [field]: value } }));
  };

  const ensureSession = async () => {
    if (sessionId) return sessionId;
    const response = await apiFetch('/api/v1/market-intelligence/wizard/', {
      method: 'POST',
      body: JSON.stringify({ draft_data: {} }),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || 'Unable to start market study.');
    setSessionId(body.id);
    return body.id;
  };

  const saveStep = async (goForward = true) => {
    setBusy(true); setError('');
    try {
      const id = await ensureSession();
      const payload = { draft_data: { [sectionKey]: data[sectionKey] }, current_step: step + 1 };
      const response = await apiFetch(`/api/v1/market-intelligence/wizard/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || 'Unable to save this section.');
      if (goForward && step < SECTIONS.length - 1) setStep((v) => v + 1);
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  };

  const commitStudy = async () => {
    setBusy(true); setError('');
    try {
      const id = await ensureSession();
      const sourceList = sources.split('\n').map((value) => value.trim()).filter(Boolean).map((label) => ({ label }));
      const save = await apiFetch(`/api/v1/market-intelligence/wizard/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify({ draft_data: { [sectionKey]: data[sectionKey], source_provenance: sourceList }, current_step: 10 }),
      });
      if (!save.ok) throw new Error((await save.json()).detail || 'Unable to save final section.');
      const response = await apiFetch(`/api/v1/market-intelligence/wizard/${id}/`, { method: 'POST', body: '{}' });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || 'Study is not ready to commit.');
      setResult(body);
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  };

  if (result) {
    return (
      <CrownLayout title="Kingdom Path Strategic Market Study" subtitle="Committed strategic evidence foundation">
        <div className="crown-card" style={{ padding: 24, maxWidth: 900 }}>
          <h2>{result.name}</h2>
          <p>Status: <strong>{result.status}</strong> · Analysis year: {result.analysis_year}</p>
          <h3>Decision domains</h3>
          <p>{(result.decision_domains || []).join(' · ')}</p>
          <h3>Current enrollment context</h3>
          <pre style={preStyle}>{JSON.stringify(result.layers?.internal_context || {}, null, 2)}</pre>
        </div>
      </CrownLayout>
    );
  }

  return (
    <CrownLayout title="Kingdom Path Strategic Market Study" subtitle="Prepare evidence for tuition, affordability, aid, enrollment, programs, and expansion">
      <div style={{ maxWidth: 920 }}>
        <div className="crown-card" style={{ padding: 20, marginBottom: 16 }}>
          <strong>Step {step + 1} of {SECTIONS.length}: {sectionLabel}</strong>
          <div style={{ height: 8, background: 'var(--crown-surface-2)', marginTop: 10, borderRadius: 6 }}>
            <div style={{ height: '100%', width: `${progress}%`, background: 'var(--crown-brand)', borderRadius: 6 }} />
          </div>
        </div>

        <div className="crown-card" style={{ padding: 24 }}>
          <SectionEditor value={data[sectionKey]} onChange={updateField} />
          {step === SECTIONS.length - 1 && (
            <label style={{ display: 'grid', gap: 5, marginTop: 18, fontWeight: 600 }}>
              Source provenance — one verified source per line
              <textarea
                rows={5}
                value={sources}
                onChange={(e) => setSources(e.target.value)}
                placeholder="2020–2024 ACS 5-year\nNCES PSS 2023–24\nLocal planning/building permits"
                style={inputStyle}
              />
            </label>
          )}
          {error && <p style={{ color: 'var(--crown-danger)' }}>{error}</p>}
          <div style={{ display: 'flex', gap: 10, marginTop: 22 }}>
            <button disabled={busy || step === 0} onClick={() => setStep((v) => Math.max(0, v - 1))} style={secondaryBtn}>Back</button>
            {step < SECTIONS.length - 1 ? (
              <button disabled={busy} onClick={() => saveStep(true)} style={primaryBtn}>{busy ? 'Saving…' : 'Save & Continue'}</button>
            ) : (
              <button disabled={busy} onClick={commitStudy} style={primaryBtn}>{busy ? 'Committing…' : 'Commit Strategic Study'}</button>
            )}
          </div>
        </div>
      </div>
    </CrownLayout>
  );
}

const inputStyle = { padding: 10, border: '1px solid var(--crown-border)', borderRadius: 6, font: 'inherit', width: '100%', boxSizing: 'border-box' };
const primaryBtn = { padding: '10px 18px', border: 0, borderRadius: 6, background: 'var(--crown-brand)', color: 'white', fontWeight: 700, cursor: 'pointer' };
const secondaryBtn = { ...primaryBtn, background: 'var(--crown-muted)' };
const preStyle = { whiteSpace: 'pre-wrap', background: 'var(--crown-surface-2)', padding: 14, borderRadius: 6, overflow: 'auto' };
