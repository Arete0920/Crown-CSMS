import { useCallback, useEffect, useRef, useState } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import { fetchAdmissionsInquiries, updateAdmissionsInquiry } from '../api/admissionsInquiries.js';
import { inquirySourceLabel } from '../lib/admissionsInquiryState.js';
import '../styles/crown-wizard.css';

const INPUT = { padding: '9px 11px', border: '1px solid var(--crown-border)', borderRadius: 8, color: 'var(--crown-text)', background: 'var(--crown-surface)', font: 'inherit', maxWidth: '100%' };
const ROW = { display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' };
const STAGES = { inquiry: 'Inquiry', tour_scheduled: 'Tour scheduled', application_started: 'Application started', application_submitted: 'Application submitted', accepted: 'Accepted', enrolled: 'Enrolled', lost: 'Closed' };

function dateText(value) {
  if (!value) return 'Not set';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Invalid date' : date.toLocaleString();
}

function localDateInput(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return new Date(date.getTime() - date.getTimezoneOffset() * 60_000).toISOString().slice(0, 16);
}

function InquiryDetails({ inquiry, owners, canEdit, onSaved }) {
  const [owner, setOwner] = useState(inquiry.assigned_to_user_id || '');
  const [nextDate, setNextDate] = useState(localDateInput(inquiry.next_follow_up_at));
  const [stage, setStage] = useState(inquiry.stage);
  const [followUpEnabled, setFollowUpEnabled] = useState(Boolean(inquiry.family_follow_up_enabled));
  const [withdrawConsent, setWithdrawConsent] = useState(false);
  const [channel, setChannel] = useState('phone');
  const [summary, setSummary] = useState('');
  const [outcome, setOutcome] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const editableStages = ['inquiry', 'tour_scheduled', 'application_started', 'lost'];

  async function save(event) {
    event.preventDefault();
    if (busy || !canEdit) return;
    setError('');
    const changes = {
      assigned_to_user_id: owner || null,
      next_follow_up_at: nextDate ? new Date(nextDate).toISOString() : null,
    };
    if (stage !== inquiry.stage) changes.stage = stage;
    if (followUpEnabled !== Boolean(inquiry.family_follow_up_enabled)) changes.family_follow_up_enabled = followUpEnabled;
    if (withdrawConsent) Object.assign(changes, { follow_up_consent: false, family_follow_up_enabled: false });
    if (summary.trim()) changes.touchpoint = { channel, summary: summary.trim(), outcome: outcome.trim() };
    setBusy(true);
    try {
      await updateAdmissionsInquiry(inquiry.id, changes);
      await onSaved();
    } catch (failure) {
      setError(failure?.message || 'The follow-up could not be saved. Your changes are still here.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="crown-card" style={{ padding: 22, marginTop: 20 }} aria-label={`Inquiry details for ${inquiry.parent_name}`}>
      <h2 style={{ marginTop: 0 }}>{inquiry.parent_name}</h2>
      <p>{inquiry.email}{inquiry.phone ? ` · ${inquiry.phone}` : ''}</p>
      <p>{inquiry.campus} · Grade {inquiry.grade_interest} · {inquiry.entry_year}</p>
      <p><strong>Request:</strong> {inquiry.request_type === 'tour' ? 'Campus visit' : inquiry.request_type === 'open_house' ? 'Open house' : 'Information'} · <strong>Contact by:</strong> {inquiry.contact_preference}</p>
      <p><strong>First source:</strong> {inquirySourceLabel(inquiry.first_source)} · <strong>Current source:</strong> {inquirySourceLabel(inquiry.primary_source)}</p>
      {inquiry.referral_detail ? <p><strong>Referral:</strong> {inquiry.referral_detail}</p> : null}
      {inquiry.utm?.utm_campaign ? <p><strong>Campaign attribution:</strong> {[inquiry.utm.utm_source, inquiry.utm.utm_medium, inquiry.utm.utm_campaign].filter(Boolean).join(' / ')}</p> : null}
      <p><strong>Last contact:</strong> {dateText(inquiry.last_touch_at)} · <strong>Received:</strong> {dateText(inquiry.created_at)}</p>
      {inquiry.notification_status?.notifications?.length ? <details>
        <summary>Communication status</summary>
        <ul>{inquiry.notification_status.notifications.slice(0, 8).map((notice, index) => <li key={`${notice.event}-${notice.channel}-${index}`}>
          {notice.audience === 'family' ? 'Family' : 'Staff'} · {notice.channel} · {notice.status === 'provider_accepted' ? 'Accepted by provider' : notice.status.replaceAll('_', ' ')}{notice.reason ? `: ${notice.reason}` : ''}
        </li>)}</ul>
      </details> : null}
      {inquiry.application_ids?.length ? <p>{inquiry.application_ids.length} application(s) linked. <a href="/admissions/pipeline">Open the admissions pipeline</a>.</p> : null}
      {inquiry.duplicate_candidates?.length ? (
        <div className="crown-alert" role="note">
          <strong>Possible matching inquiries:</strong>
          <ul>{inquiry.duplicate_candidates.map((candidate) => <li key={candidate.id}>{candidate.parent_name} · {candidate.email} · {STAGES[candidate.stage] || candidate.stage}</li>)}</ul>
          Check these records before contacting the family again. They remain separate until reviewed.
        </div>
      ) : null}
      {!canEdit ? <p className="crown-muted">You have read-only access to this queue.</p> : (
        <form onSubmit={save} aria-label="Update inquiry follow-up">
          {error ? <div className="crown-alert" role="alert">{error}</div> : null}
          <fieldset disabled={busy} style={{ border: 0, padding: 0, margin: '20px 0 0', minWidth: 0 }}>
            <legend style={{ fontWeight: 700, marginBottom: 12 }}>Ownership and next action</legend>
            <div style={ROW}>
              <label style={{ display: 'grid', gap: 6 }}>Assigned counselor
                <select style={INPUT} value={owner} onChange={(event) => setOwner(event.target.value)}>
                  <option value="">Unassigned</option>
                  {owners.map((person) => <option key={person.id} value={person.id}>{person.name || person.email}</option>)}
                </select>
              </label>
              <label style={{ display: 'grid', gap: 6 }}>Next follow-up
                <input style={INPUT} type="datetime-local" value={nextDate} onChange={(event) => setNextDate(event.target.value)} />
              </label>
              <label style={{ display: 'grid', gap: 6 }}>Inquiry stage
                <select style={INPUT} value={stage} onChange={(event) => setStage(event.target.value)} disabled={!editableStages.includes(inquiry.stage)}>
                  {!editableStages.includes(inquiry.stage) ? <option value={inquiry.stage}>{STAGES[inquiry.stage] || inquiry.stage}</option> : null}
                  {editableStages.map((value) => <option key={value} value={value}>{STAGES[value]}</option>)}
                </select>
              </label>
            </div>
            <label style={{ display: 'flex', gap: 8, alignItems: 'flex-start', marginTop: 18 }}>
              <input type="checkbox" checked={followUpEnabled} disabled={!inquiry.follow_up_consent || withdrawConsent} onChange={(event) => setFollowUpEnabled(event.target.checked)} />
              <span>Family follow-up reminders enabled{!inquiry.follow_up_consent ? ' — family permission is not active.' : ' (clear to pause)'}</span>
            </label>
            {inquiry.follow_up_consent ? <div style={{ marginTop: 12 }}>
              <label style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                <input type="checkbox" checked={withdrawConsent} onChange={(event) => { setWithdrawConsent(event.target.checked); if (event.target.checked) setFollowUpEnabled(false); }} />
                <span>Family asked to stop reminders</span>
              </label>
              <p className="crown-muted" style={{ margin: '6px 0 0' }}>Saving this stop request withdraws reminder permission. Staff cannot restore that permission.</p>
            </div> : null}
            <h3 style={{ marginBottom: 10 }}>Record a completed contact</h3>
            <div style={ROW}>
              <label style={{ display: 'grid', gap: 6 }}>Contact method
                <select style={INPUT} value={channel} onChange={(event) => setChannel(event.target.value)}>
                  {['phone', 'email', 'sms', 'tour', 'event', 'referral', 'church'].map((value) => <option key={value} value={value}>{value === 'sms' ? 'Text message' : value[0].toUpperCase() + value.slice(1)}</option>)}
                </select>
              </label>
              <label style={{ display: 'grid', gap: 6, flex: '1 1 250px' }}>Contact summary
                <input style={INPUT} value={summary} onChange={(event) => setSummary(event.target.value)} maxLength={240} placeholder="For example, called family and offered two visit times" />
              </label>
              <label style={{ display: 'grid', gap: 6 }}>Outcome
                <input style={INPUT} value={outcome} onChange={(event) => setOutcome(event.target.value)} maxLength={120} placeholder="For example, awaiting preferred time" />
              </label>
            </div>
            <div className="crown-wizard-actions"><span className="crown-muted">Times use your local timezone.</span><button type="submit" className="crown-btn crown-btn-primary" disabled={busy}>{busy ? 'Saving…' : 'Save follow-up'}</button></div>
          </fieldset>
        </form>
      )}
    </section>
  );
}

export default function AdmissionsInquiryQueue() {
  const [filters, setFilters] = useState({ stage: '', unassigned: false, overdue: false });
  const [payload, setPayload] = useState(null);
  const [selectedId, setSelectedId] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [savedMessage, setSavedMessage] = useState('');
  const loadVersion = useRef(0);

  const reload = useCallback(async () => {
    const version = ++loadVersion.current;
    setLoading(true);
    setError('');
    try {
      const result = await fetchAdmissionsInquiries({ stage: filters.stage, unassigned: filters.unassigned ? 1 : '', overdue: filters.overdue ? 1 : '' });
      if (version === loadVersion.current) setPayload(result);
    } catch (failure) {
      if (version === loadVersion.current) {
        setPayload(null);
        setError(failure?.message || 'The school inquiry queue could not be loaded.');
      }
    } finally {
      if (version === loadVersion.current) setLoading(false);
    }
  }, [filters]);

  useEffect(() => { reload(); }, [reload]);
  const inquiries = Array.isArray(payload?.results) ? payload.results : [];
  const owners = Array.isArray(payload?.owners) ? payload.owners : [];
  const selected = inquiries.find((item) => item.id === selectedId);
  const ownerName = (id) => owners.find((owner) => owner.id === id)?.name || (id ? 'Assigned counselor' : 'Unassigned');

  async function afterSave() {
    await reload();
    setSavedMessage('Inquiry ownership and follow-up saved.');
  }

  return (
    <CrownLayout title="Admissions Inquiries" subtitle="Contact families, assign ownership, and guide the next step toward enrollment" right={<a className="crown-btn" href="/admissions/pipeline">Applications</a>}>
      <div className="crown-card" style={{ padding: 20 }}>
        <div style={{ ...ROW, justifyContent: 'space-between', marginBottom: 18 }}>
          <div style={ROW}>
            <label style={{ display: 'grid', gap: 5 }}>Stage
              <select style={INPUT} value={filters.stage} onChange={(event) => setFilters((previous) => ({ ...previous, stage: event.target.value }))}>
                <option value="">Active inquiries</option><option value="all">All stages and history</option>{Object.entries(STAGES).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
              </select>
            </label>
            <label><input type="checkbox" checked={filters.unassigned} onChange={(event) => setFilters((previous) => ({ ...previous, unassigned: event.target.checked }))} /> Unassigned</label>
            <label><input type="checkbox" checked={filters.overdue} onChange={(event) => setFilters((previous) => ({ ...previous, overdue: event.target.checked }))} /> Follow-up due</label>
          </div>
          <button className="crown-btn" type="button" onClick={reload} disabled={loading}>Refresh queue</button>
        </div>
        {savedMessage ? <p role="status">{savedMessage}</p> : null}
        {error ? <div className="crown-alert" role="alert">{error}<button className="crown-btn" type="button" onClick={reload}>Try again</button></div> : null}
        {loading ? <p role="status">Loading school inquiries…</p> : null}
        {!loading && !error && inquiries.length === 0 ? <p>No inquiries match these filters.</p> : null}
        {!loading && !error && inquiries.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table className="crown-table">
              <caption style={{ textAlign: 'left', paddingBottom: 10 }}>{inquiries.length} of {payload.count ?? inquiries.length} matching inquiry record(s) shown. The queue displays up to 100 records.</caption>
              <thead><tr>{['Family contact', 'Interest', 'Source', 'Stage', 'Owner', 'Next follow-up', 'Action'].map((heading) => <th scope="col" key={heading}>{heading}</th>)}</tr></thead>
              <tbody>{inquiries.map((inquiry) => (
                <tr key={inquiry.id}>
                  <td><strong>{inquiry.parent_name}</strong><div>{inquiry.email}</div></td>
                  <td>Grade {inquiry.grade_interest}<div>{inquiry.entry_year}</div></td>
                  <td>{inquirySourceLabel(inquiry.first_source)}</td>
                  <td>{STAGES[inquiry.stage] || inquiry.stage}</td>
                  <td>{ownerName(inquiry.assigned_to_user_id)}</td>
                  <td>{dateText(inquiry.next_follow_up_at)}</td>
                  <td><button className="crown-btn" type="button" onClick={() => { setSelectedId(inquiry.id); setSavedMessage(''); }} aria-expanded={selectedId === inquiry.id}>Open {inquiry.parent_name}</button></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        ) : null}
      </div>
      {selected && !loading && !error ? <InquiryDetails key={`${selected.id}-${selected.updated_at || selected.next_follow_up_at || ''}`} inquiry={selected} owners={owners} canEdit={payload?.can_edit === true} onSaved={afterSave} /> : null}
    </CrownLayout>
  );
}
