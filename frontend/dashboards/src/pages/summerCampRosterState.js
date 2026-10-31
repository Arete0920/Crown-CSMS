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
    custody?.checkin_time && !custody.checkout_time);
}

export function campCustodyLabel(custody) {
  if (!custody) return "Custody status unavailable";
  if (!custody.checkin_time) return "Not checked in today";
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
