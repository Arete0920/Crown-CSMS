import { useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router';
import CrownPublicLayout from '../components/crown/CrownPublicLayout.jsx';
import { createInquiryRequestKey, startInquiryApplication, submitAdmissionsInquiry } from '../api/admissionsInquiries.js';
import {
  clearAdmissionsInquiry,
  clearPendingAdmissionsInquiry,
  INQUIRY_SOURCE_OPTIONS,
  inquiryApplicationPath,
  loadAdmissionsInquiry,
  loadPendingAdmissionsInquiry,
  saveAdmissionsInquiry,
  savePendingAdmissionsInquiry,
} from '../lib/admissionsInquiryState.js';
import '../styles/crown-wizard.css';

const GRID = { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 240px), 1fr))', gap: 16 };
const FIELD = { display: 'grid', gap: 6, fontSize: 14 };
const INPUT = { width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--crown-border)', background: 'var(--crown-surface)', color: 'var(--crown-text)', boxSizing: 'border-box', font: 'inherit' };
const GRADES = ['Pre-K', 'K', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'];

function safePageAddress(value) {
  try {
    const url = new URL(value);
    return `${url.origin}${url.pathname}`;
  } catch {
    return '';
  }
}

function initialInquiry() {
  const params = new URLSearchParams(globalThis.location?.search || '');
  const schoolId = params.get('school_id') || '';
  const pending = loadPendingAdmissionsInquiry(schoolId);
  const campus = params.get('campus') || params.get('school_name') || '';
  if (pending && (!campus || pending.payload.campus === campus)) return pending.payload;
  const utm = {};
  for (const field of ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content']) {
    if (params.get(field)) utm[field] = params.get(field).slice(0, 200);
  }
  utm.landing_page = safePageAddress(globalThis.location?.href || '');
  utm.referrer = safePageAddress(globalThis.document?.referrer || '');
  const requestedType = params.get('request_type');
  return {
    school_id: schoolId,
    parent_name: '',
    email: '',
    phone: '',
    campus,
    grade_interest: params.get('grade') || '',
    entry_year: params.get('entry_year') || '',
    request_type: ['info', 'tour', 'open_house'].includes(requestedType) ? requestedType : 'info',
    contact_preference: 'email',
    response_consent: false,
    follow_up_consent: false,
    source: params.get('source') || 'website',
    referral_type: '',
    referral_detail: '',
    utm,
    ...(params.get('campaign_id') ? { campaign_id: params.get('campaign_id') } : {}),
    website: '',
  };
}

export default function AdmissionsInquiryPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState(initialInquiry);
  const [receipt, setReceipt] = useState(() => {
    const saved = loadAdmissionsInquiry(form.school_id);
    return !form.campus || [saved?.school_name, saved?.intake?.campus].includes(form.campus) ? saved : null;
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const pendingRef = useRef(loadPendingAdmissionsInquiry(form.school_id));

  function update(field, value) {
    setForm((previous) => ({ ...previous, [field]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    setError('');
    if (!form.response_consent || !form.parent_name.trim() || !form.email.trim()
      || !form.grade_interest || !form.entry_year.trim() || (!form.school_id && !form.campus.trim())) {
      setError('Complete the required fields and allow admissions to respond to your request.');
      return;
    }
    if (form.contact_preference !== 'email' && !form.phone.trim()) {
      setError('Enter a phone number for your selected contact method.');
      return;
    }
    if (form.contact_preference === 'sms' && !/^\+[1-9]\d{6,14}$/.test(form.phone.trim())) {
      setError('For SMS, use a country code and digits, for example +13025550100.');
      return;
    }
    const payload = { ...form, parent_name: form.parent_name.trim(), email: form.email.trim(), phone: form.phone.trim(), campus: form.campus.trim(), entry_year: form.entry_year.trim() };
    const fingerprint = JSON.stringify(payload);
    if (!pendingRef.current || JSON.stringify(pendingRef.current.payload) !== fingerprint) {
      pendingRef.current = { payload, idempotencyKey: createInquiryRequestKey() };
    }
    savePendingAdmissionsInquiry(pendingRef.current);
    setBusy(true);
    try {
      const result = await submitAdmissionsInquiry(payload, pendingRef.current.idempotencyKey);
      setReceipt(saveAdmissionsInquiry(result, payload));
    } catch (failure) {
      setError(failure?.message || 'We could not confirm receipt. Your entries are still here; please try again.');
    } finally {
      setBusy(false);
    }
  }

  async function continueApplication() {
    if (busy || !receipt) return;
    setBusy(true);
    setError('');
    try {
      const result = await startInquiryApplication(receipt);
      const saved = saveAdmissionsInquiry({ ...receipt, ...result }, receipt.intake);
      navigate(inquiryApplicationPath(saved));
    } catch (failure) {
      setError(failure?.message || 'Your inquiry is saved, but the application could not be started. Please try again.');
    } finally {
      setBusy(false);
    }
  }

  function startAnotherRequest() {
    clearAdmissionsInquiry();
    clearPendingAdmissionsInquiry();
    pendingRef.current = null;
    setReceipt(null);
    setForm(initialInquiry());
    setError('');
  }

  const directApplication = `/admissions/apply${form.school_id ? `?school_id=${encodeURIComponent(form.school_id)}` : ''}`;

  return (
    <CrownPublicLayout
      title={receipt ? 'Your inquiry is saved' : 'Let’s begin a conversation'}
      subtitle={receipt ? receipt.school_name || receipt.intake?.campus : 'Request information or a campus visit before completing an application.'}
      right={<Link className="crown-btn" to={receipt ? inquiryApplicationPath(receipt) : directApplication}>Application</Link>}
    >
      {error ? <div className="crown-alert" role="alert">{error}</div> : null}
      {receipt ? (
        <section className="crown-card" style={{ padding: 24 }} aria-label="Inquiry receipt">
          <div className="crown-alert success" role="status">Your request has been recorded by the school.</div>
          <h2 style={{ marginTop: 16 }}>What happens next</h2>
          <p>{receipt.next_step || 'The admissions team will review your request and contact you using your selected contact method.'}</p>
          {receipt.intake?.request_type !== 'info' ? <p>A visit date is confirmed only after the admissions team agrees on a time with you.</p> : null}
          <p>Reference: <strong>{receipt.inquiry_id}</strong></p>
          <p className="crown-muted">This browser can reconnect your inquiry to an application until {new Date(receipt.expires_at).toLocaleDateString()}. Your request is already saved even if you choose to apply later.</p>
          <div className="crown-wizard-actions" style={{ flexWrap: 'wrap' }}>
            <button className="crown-btn" type="button" onClick={startAnotherRequest} disabled={busy}>Start another inquiry</button>
            <button className="crown-btn crown-btn-primary" type="button" onClick={continueApplication} disabled={busy}>{busy ? 'Opening application…' : 'Continue to application'}</button>
          </div>
        </section>
      ) : (
        <form className="crown-card" style={{ padding: 24 }} onSubmit={submit} aria-label="Admissions inquiry">
          <fieldset disabled={busy} style={{ border: 0, padding: 0, margin: 0, minWidth: 0 }}>
            <legend style={{ fontWeight: 700, marginBottom: 16 }}>How can admissions help?</legend>
            <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap', marginBottom: 22 }}>
              {[['info', 'Request information'], ['tour', 'Request a campus visit'], ['open_house', 'Ask about an open house']].map(([value, label]) => (
                <label key={value} style={{ display: 'flex', gap: 7, alignItems: 'center' }}>
                  <input type="radio" name="request_type" value={value} checked={form.request_type === value} onChange={() => update('request_type', value)} />{label}
                </label>
              ))}
            </div>
            <div style={GRID}>
              <label style={FIELD}>School or campus{!form.school_id ? ' *' : ''}
                <input style={INPUT} name="campus" value={form.campus} onChange={(e) => update('campus', e.target.value)} required={!form.school_id} maxLength={120} autoComplete="organization" />
              </label>
              <label style={FIELD}>Parent or guardian name *
                <input style={INPUT} name="parent_name" value={form.parent_name} onChange={(e) => update('parent_name', e.target.value)} required maxLength={160} autoComplete="name" />
              </label>
              <label style={FIELD}>Email address *
                <input style={INPUT} name="email" type="email" value={form.email} onChange={(e) => update('email', e.target.value)} required maxLength={254} autoComplete="email" />
              </label>
              <label style={FIELD}>Phone number{form.contact_preference !== 'email' ? ' *' : ''}
                <input style={INPUT} name="phone" type="tel" value={form.phone} onChange={(e) => update('phone', e.target.value)} required={form.contact_preference !== 'email'} maxLength={32} autoComplete="tel" aria-describedby={form.contact_preference === 'sms' ? 'inquiry-sms-hint' : undefined} />
                {form.contact_preference === 'sms' ? <span id="inquiry-sms-hint" className="crown-muted">For text messages, include + and your country code, for example +13025550100.</span> : null}
              </label>
              <label style={FIELD}>Grade of interest *
                <select style={INPUT} name="grade_interest" value={form.grade_interest} onChange={(e) => update('grade_interest', e.target.value)} required>
                  <option value="">Select a grade</option>
                  {GRADES.map((grade) => <option key={grade} value={grade}>{['Pre-K', 'K'].includes(grade) ? grade : `Grade ${grade}`}</option>)}
                </select>
              </label>
              <label style={FIELD}>School year of interest *
                <input style={INPUT} name="entry_year" value={form.entry_year} onChange={(e) => update('entry_year', e.target.value)} required maxLength={32} placeholder="For example, 2027-2028" />
              </label>
              <label style={FIELD}>Preferred contact method
                <select style={INPUT} name="contact_preference" value={form.contact_preference} onChange={(e) => update('contact_preference', e.target.value)}>
                  <option value="email">Email</option><option value="phone">Phone call</option><option value="sms">Text message</option>
                </select>
              </label>
              <label style={FIELD}>How did you hear about us?
                <select style={INPUT} name="source" value={form.source} onChange={(e) => update('source', e.target.value)}>
                  {!INQUIRY_SOURCE_OPTIONS.some((option) => option.value === form.source) ? <option value={form.source}>{form.source}</option> : null}
                  {INQUIRY_SOURCE_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                </select>
              </label>
              <label style={{ ...FIELD, gridColumn: '1 / -1' }}>Referral or event details (optional)
                <input style={INPUT} name="referral_detail" value={form.referral_detail} onChange={(e) => update('referral_detail', e.target.value)} maxLength={180} placeholder="Name of the church, referring family, or event" />
              </label>
            </div>
            <div hidden aria-hidden="true"><label>Website<input name="website" tabIndex={-1} value={form.website} onChange={(e) => update('website', e.target.value)} autoComplete="off" /></label></div>
            <div style={{ display: 'grid', gap: 14, marginTop: 22 }}>
              <label style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                <input name="response_consent" type="checkbox" checked={form.response_consent} onChange={(e) => update('response_consent', e.target.checked)} required />
                <span>I allow this school to use these details to respond to my admissions request through my selected contact method. *</span>
              </label>
              <label style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                <input name="follow_up_consent" type="checkbox" checked={form.follow_up_consent} onChange={(e) => update('follow_up_consent', e.target.checked)} />
                <span>Send me admissions follow-up reminders by my selected contact method. I can ask admissions to stop these reminders.</span>
              </label>
            </div>
            <div className="crown-wizard-actions" style={{ flexWrap: 'wrap' }}>
              <span className="crown-muted">* Required. This request does not submit an application.</span>
              <button className="crown-btn crown-btn-primary" type="submit" disabled={busy}>{busy ? 'Saving request…' : 'Send my request'}</button>
            </div>
          </fieldset>
        </form>
      )}
    </CrownPublicLayout>
  );
}
