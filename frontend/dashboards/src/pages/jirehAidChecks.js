/* Canonical aid readback checks shared by the officer screen and tests. */
export function requireAidOverview(payload) {
  if (!payload || !Array.isArray(payload.applications)
      || !Array.isArray(payload.awards) || !Array.isArray(payload.budgets)) {
    throw new Error('Financial Aid overview returned an invalid contract.');
  }
  return payload;
}

export function requireCurrentAidYear(payload, schoolId) {
  if (!payload || !Array.isArray(payload.results)) {
    throw new Error('Academic-year service returned an invalid contract.');
  }
  const active = payload.results.filter((year) =>
    year.is_current === true && String(year.school_id) === String(schoolId));
  if (active.length !== 1) {
    throw new Error('Exactly one current school academic year is required.');
  }
  return active[0];
}

export function requireLiveAidYear(payload, schoolId) {
  const meta = payload?.meta;
  const yearId = meta?.academic_year_id;
  if (payload?.dashboard_key !== 'financial-aid' || meta?.served_from !== 'live_db'
      || typeof schoolId !== 'string' || !schoolId.trim() || meta.school_id !== schoolId
      || typeof yearId !== 'string' || yearId.length !== 36
      || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(yearId)) {
    throw new Error('A live Financial Aid summary with matching school and valid academic year is required.');
  }
  return yearId;
}

export function dollarsToCents(value) {
  const input = String(value || '').trim();
  if (!/^\d+(?:\.\d{1,2})?$/.test(input)) throw new Error('Enter a valid tuition amount in dollars.');
  const parts = input.split('.');
  const cents = Number(parts[0]) * 100 + Number((parts[1] || '').padEnd(2, '0'));
  if (!Number.isSafeInteger(cents) || cents <= 0) throw new Error('Tuition must be positive.');
  return cents;
}

export function verifiedAcceptedAward(overview, awardId, applicationId, studentId) {
  const checked = requireAidOverview(overview);
  return checked.awards.find((award) =>
    String(award.id) === String(awardId)
    && String(award.aid_application_id) === String(applicationId)
    && String(award.student_id) === String(studentId)
    && award.decision_status === 'ACCEPTED'
    && Boolean(award.ledger_entry_id)
    && Number.isSafeInteger(Number(award.awarded_cents))
    && Number(award.awarded_cents) > 0);
}

export function acceptedFaceValue(overview) {
  return requireAidOverview(overview).awards.reduce((sum, award) =>
    sum + (award.decision_status === 'ACCEPTED' ? Number(award.awarded_cents) : 0), 0);
}
