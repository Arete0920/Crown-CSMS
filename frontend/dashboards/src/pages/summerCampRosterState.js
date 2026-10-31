// Keep roster displays tied to actual school-scoped API data; never synthesize custody.
export function campSessions(payload) {
  if (!Array.isArray(payload)) throw new Error("Invalid Camp sessions response.");
  return payload;
}

export function campRoster(payload, sessionId) {
  if (!payload || !Array.isArray(payload.rows) ||
      String(payload.session_id) !== String(sessionId)) {
    throw new Error("Camp session roster does not match the selected session.");
  }
  return payload.rows;
}

export function campToday(payload) {
  if (!payload || !Array.isArray(payload.rows) ||
      typeof payload.date !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(payload.date)) {
    throw new Error("Camp custody day could not be verified.");
  }
  return payload;
}

export function currentCampCustody(enrollment, today, sessionId) {
  if (!today || !Array.isArray(today.rows) || !enrollment?.student_id) return null;
  return today.rows.find((row) =>
    String(row.session_id) === String(sessionId) &&
    String(row.student_id) === String(enrollment.student_id) &&
    String(row.enrollment_id) === String(enrollment.enrollment_id)) || null;
}

// Open custody is school-wide. A child may have an unresolved attendance
// from a different Camp session or a cancelled/expired enrollment.
export function campOpenCustodyRows(today) {
  if (!today || !Array.isArray(today.rows)) return [];
  return today.rows.filter((row) => row && !row.checkout_time &&
    (Boolean(row.checkin_time) || row.unresolved_custody === true ||
      row.requires_supervisor_reconciliation === true));
}

export function campStudentHasOpenCustody(today, studentId) {
  // Invalid or missing custody evidence cannot authorize a new admission.
  if (!today || !Array.isArray(today.rows) || !studentId) return true;
  return campOpenCustodyRows(today).some((row) =>
    row.student_id != null && String(row.student_id) === String(studentId));
}

export function duplicateCampRegistration(row, roster) {
  return roster.filter((item) =>
    item.status === "REGISTERED" &&
    String(item.student_id) === String(row.student_id)).length !== 1;
}

export function campCanCheckIn(row, custody, session, day, duplicate = false) {
  return Boolean(!duplicate && row?.student_id && row.status === "REGISTERED" &&
    row.readiness_status === "READY" && custody && !custody.checkin_time &&
    session?.status === "PUBLISHED" && typeof day === "string" &&
    session.start_date <= day && day <= session.end_date);
}

export function campCanVerifyPickup(row, custody, duplicate = false) {
  return Boolean(!duplicate && row?.student_id && row.status === "REGISTERED" &&
    custody?.checkin_time && !custody.checkout_time &&
    !custody.requires_supervisor_reconciliation &&
    (custody.open_custody_count == null || custody.open_custody_count === 1));
}

export function campCustodyLabel(custody) {
  if (!custody) return "Custody status unavailable";
  if (!custody.checkin_time) return "Not checked in today";
  if (custody.requires_supervisor_reconciliation || custody.open_custody_count > 1) return "Unresolved custody; supervisor reconciliation required";
  if (!custody.checkout_time) return "Checked in; awaiting authorized release";
  return custody.pickup_verified ? "Released to verified pickup" : "Release needs review";
}

export function campPickupContacts(payload, enrollmentId) {
  if (!payload || String(payload.enrollment_id) !== String(enrollmentId) ||
      !Array.isArray(payload.contacts) ||
      !payload.contacts.every((contact) => Number.isSafeInteger(contact.id) &&
        contact.id > 0 && typeof contact.name === "string")) {
    throw new Error("Current enrollment pickup contacts are unavailable.");
  }
  return payload.contacts;
}
