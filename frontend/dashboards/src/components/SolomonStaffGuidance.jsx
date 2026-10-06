import { useEffect, useRef, useState } from 'react';
import { getCurrentUserRoles } from '../auth/roleAdapter';
import { apiFetch } from '../lib/api';

const topics = [
  ['onboarding', 'Implementation'],
  ['interpretation', 'Understanding forecasts'],
  ['governance', 'Operating governance'],
  ['strategy', 'School-specific strategy'],
  ['knowledge', 'Documentation and support'],
  ['training', 'Staff training'],
  ['communications', 'General announcements'],
  ['teaching', 'Teacher preparation'],
  ['leadership', 'Leadership agendas'],
  ['outreach', 'Kingdom Path outreach'],
  ['care', 'Diadem, care, camps and activities'],
  ['accessibility', 'Clear instructions and language'],
  ['quality', 'Synthetic quality checks'],

];
const sourceDocument = 'docs/solomon/SOLOMON_APPROVED_ASSISTANCE.md';
const existingTopics = ['onboarding', 'interpretation', 'governance', 'strategy'];
const staffRoles = ['head_of_school', 'teacher', 'finance_director', 'aid_director', 'registrar', 'support'];

/** Optional curated guidance only. Backend tenant/role gates remain authoritative. */
export default function SolomonStaffGuidance() {
  const roles = getCurrentUserRoles();
  const enabled = import.meta.env.VITE_SOLOMON_GUIDANCE_ENABLED === 'true'
    && !roles.includes('student') && roles.some(role => staffRoles.includes(role));
  const [acknowledged, setAcknowledged] = useState(false);
  const [topic, setTopic] = useState('onboarding');
  const [status, setStatus] = useState('idle');
  const [guidance, setGuidance] = useState(null);
  const request = useRef(null);
  useEffect(() => () => request.current?.abort(), []);

  async function load(event) {
    event.preventDefault();
    if (!enabled || !acknowledged) return;
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setStatus('loading');
    setGuidance(null);
    try {
      const response = await apiFetch('/api/solomon/guidance/', {
        method: 'POST',
        body: JSON.stringify({ topic, human_review_acknowledged: true }),
        signal: controller.signal,
        validateStatus: code => (code >= 200 && code < 300) || code === 404,
      });
      if (controller.signal.aborted) return;
      if (response.status === 404) { setStatus('unavailable'); return; }
      if (!response.ok) throw new Error('Guidance unavailable');
      const payload = await response.json();
      if (controller.signal.aborted) return;
      if (payload.mode !== 'curated_guidance' || payload.content_origin !== 'curated_internal'
        || payload.human_review_required !== true || payload.topic !== topic
        || typeof payload.title !== 'string' || typeof payload.guidance !== 'string') {
        throw new Error('Invalid guidance response');
      }
      if ((payload.steps !== undefined && (!Array.isArray(payload.steps) || payload.steps.some(step => typeof step !== 'string')))
        || (payload.draft !== undefined && typeof payload.draft !== 'string')
        || (payload.source_document !== undefined && payload.source_document !== sourceDocument)
        || (payload.source_section !== undefined && payload.source_section !== (existingTopics.includes(topic) ? 'existing-guidance' : topic))) {
        throw new Error('Invalid assistance resource');
      }
      setGuidance(payload);
      setStatus('ready');
    } catch {
      if (!controller.signal.aborted) setStatus('error');
    }
  }

  function changeTopic(event) {
    request.current?.abort();
    setTopic(event.target.value);
    setGuidance(null);
    setStatus('idle');
    setAcknowledged(false);
  }

  if (!enabled) return null;
  return (
    <section className="solomon-staff-guidance" aria-label="General staff guidance">
      <h3>General staff guidance</h3>
      <p>Choose a topic for general CROWN guidance. School-specific decisions stay with your leadership and Arete Advisory Group.</p>
      <div className="solomon-guidance-controls">
        <label>Guidance topic
          <select value={topic} onChange={changeTopic}>
            {topics.map(([value, title]) => <option key={value} value={value}>{title}</option>)}
          </select>
        </label>
        <label className="solomon-guidance-review">
          <input type="checkbox" checked={acknowledged} onChange={event => {
            setAcknowledged(event.target.checked);
            if (!event.target.checked) {
              request.current?.abort();
              setGuidance(null);
              setStatus('idle');
            }
          }} />
          I will review this guidance before acting.
        </label>
        <button type="button" onClick={load} disabled={!acknowledged || status === 'loading'}>View guidance</button>
      </div>
      <div aria-live="polite" aria-busy={status === 'loading'}>
        {status === 'loading' && <p>Loading general guidance…</p>}
        {status === 'unavailable' && <p>Staff guidance is not enabled for this account or school.</p>}
        {status === 'error' && <p>Guidance could not be loaded. Please try again.</p>}
        {guidance && <>
          <h4>{guidance.title}</h4>
          <p>{guidance.guidance}</p>
          {guidance.steps?.length > 0 && <ol>{guidance.steps.map((step, index) => <li key={index}>{step}</li>)}</ol>}
          {guidance.draft && <section aria-label="Reusable draft">
            <h4>Reusable draft — review and complete before use</h4>
            <p className="solomon-guidance-draft">{guidance.draft}</p>
          </section>}
          {guidance.source_document === sourceDocument && <p><a href={`https://github.com/Arete0920/Crown-CSMS/blob/main/${sourceDocument}#${guidance.source_section || 'existing-guidance'}`} target="_blank" rel="noopener noreferrer">Read the maintained source</a></p>}
          <small>Curated CROWN guidance · Human review required</small>
        </>}
      </div>
    </section>
  );
}
