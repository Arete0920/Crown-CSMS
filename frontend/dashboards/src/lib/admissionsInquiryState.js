// The school-scoped capability is never placed in a URL. Contact drafts stay in this tab.
const RECEIPT_KEY = 'crown_admissions_inquiry_receipt:';
const ACTIVE_SCHOOL_KEY = 'crown_admissions_inquiry_school';
const PENDING_KEY = 'crown_admissions_inquiry_pending';
let receiptMemory = null;
let pendingMemory = null;

function readSession(key) {
  try {
    const raw = globalThis.sessionStorage.getItem(key);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function writeSession(key, value) {
  try {
    if (value) globalThis.sessionStorage.setItem(key, JSON.stringify(value));
    else globalThis.sessionStorage.removeItem(key);
  } catch {
    // In-memory continuity remains available when tab storage is disabled.
  }
}

function readLocal(key) {
  try { return JSON.parse(globalThis.localStorage.getItem(key) || 'null'); } catch { return null; }
}

function writeLocal(key, value) {
  try {
    if (value) globalThis.localStorage.setItem(key, JSON.stringify(value));
    else globalThis.localStorage.removeItem(key);
  } catch { /* The current tab can continue if persistent storage is unavailable. */ }
}

export function loadAdmissionsInquiry(schoolId = '') {
  const school = schoolId || receiptMemory?.school_id || readLocal(ACTIVE_SCHOOL_KEY);
  const saved = (receiptMemory?.school_id === school ? receiptMemory : null)
    || readSession(`${RECEIPT_KEY}${school}`) || readLocal(`${RECEIPT_KEY}${school}`);
  if (!saved?.inquiry_id || !saved?.continuation_token || !saved?.school_id) return null;
  if (schoolId && String(saved.school_id) !== String(schoolId)) return null;
  if (!Number.isFinite(Date.parse(saved.expires_at)) || Date.parse(saved.expires_at) <= Date.now()) {
    clearAdmissionsInquiry(saved.school_id);
    return null;
  }
  return saved;
}

export function saveAdmissionsInquiry(receipt, intake) {
  if (!receipt?.inquiry_id || !receipt?.continuation_token || !receipt?.school_id) {
    throw new Error('The school did not return a complete request receipt. Please retry.');
  }
  receiptMemory = { ...receipt, intake, saved_at: receipt.saved_at || new Date().toISOString(), expires_at: receipt.expires_at || new Date(Date.now() + 30 * 86400_000).toISOString() };
  writeSession(`${RECEIPT_KEY}${receipt.school_id}`, receiptMemory);
  // Persist only the capability and non-contact context needed for later application linkage.
  const { inquiry_id, continuation_token, school_id, school_name, stage, next_step, saved_at, expires_at } = receiptMemory;
  const { campus, entry_year, grade_interest, source, request_type } = intake || {};
  writeLocal(`${RECEIPT_KEY}${school_id}`, { inquiry_id, continuation_token, school_id, school_name, stage, next_step, saved_at, expires_at, intake: { campus, entry_year, grade_interest, source, request_type } });
  writeLocal(ACTIVE_SCHOOL_KEY, school_id);
  clearPendingAdmissionsInquiry();
  return receiptMemory;
}

export function clearAdmissionsInquiry(schoolId = '') {
  const school = schoolId || receiptMemory?.school_id || readLocal(ACTIVE_SCHOOL_KEY);
  if (!schoolId || receiptMemory?.school_id === schoolId) receiptMemory = null;
  writeSession(`${RECEIPT_KEY}${school}`, null);
  writeLocal(`${RECEIPT_KEY}${school}`, null);
  if (readLocal(ACTIVE_SCHOOL_KEY) === school) writeLocal(ACTIVE_SCHOOL_KEY, null);
}

export function loadPendingAdmissionsInquiry(schoolId = '') {
  const saved = pendingMemory || readSession(PENDING_KEY);
  if (!saved?.payload || !saved?.idempotencyKey) return null;
  if (schoolId && String(saved.payload.school_id || '') !== String(schoolId)) return null;
  return saved;
}

export function savePendingAdmissionsInquiry(value) {
  pendingMemory = value;
  writeSession(PENDING_KEY, value);
}

export function clearPendingAdmissionsInquiry() {
  pendingMemory = null;
  writeSession(PENDING_KEY, null);
}

export function inquiryApplicationPath(receipt) {
  const query = new URLSearchParams();
  if (receipt?.school_id) query.set('school_id', receipt.school_id);
  return `/admissions/apply${query.size ? `?${query}` : ''}`;
}

export function inquiryEntryPath(search = globalThis.location?.search || '') {
  const source = new URLSearchParams(search);
  const query = new URLSearchParams();
  for (const key of ['school_id', 'school_name', 'campus', 'grade', 'entry_year', 'request_type', 'source', 'campaign_id', 'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content']) {
    if (source.get(key)) query.set(key, source.get(key));
  }
  return `/admissions/inquire${query.size ? `?${query}` : ''}`;
}

export function inquiryWizardIntake(saved) {
  const intake = saved?.intake || {};
  return {
    inquiry: {
      campus: intake.campus || saved?.school_name || '',
      startTerm: intake.entry_year || '',
      heardAbout: intake.source || '',
      preferredTourWindow: '',
      preferredInterviewMode: '',
    },
    family: {
      parentName: intake.parent_name || '',
      email: intake.email || '',
      phone: intake.phone || '',
    },
    student: { gradeApplyingFor: intake.grade_interest || '' },
  };
}

export const INQUIRY_SOURCE_OPTIONS = [
  { value: 'website', label: 'School website' },
  { value: 'church_referral', label: 'Church referral' },
  { value: 'current_family', label: 'Current family' },
  { value: 'friend_or_colleague', label: 'Friend or colleague' },
  { value: 'social_media', label: 'Social media' },
  { value: 'search_engine', label: 'Search engine' },
  { value: 'community_event', label: 'Community event' },
  { value: 'direct_mail_qr', label: 'Mailing or QR code' },
  { value: 'other', label: 'Other' },
];

export function inquirySourceLabel(source) {
  return INQUIRY_SOURCE_OPTIONS.find((option) => option.value === source)?.label || source || 'Unspecified';
}
