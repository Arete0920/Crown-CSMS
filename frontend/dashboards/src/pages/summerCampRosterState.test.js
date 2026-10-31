import { describe, expect, it } from "vitest";
import { campSessions, campRoster, campToday, currentCampCustody,
  campCanCheckIn, campCanVerifyPickup, campCustodyLabel, campPickupContacts,
  duplicateCampRegistration } from "./summerCampRosterState.js";

const child = { enrollment_id: "11", session_id: "4", student_id: "student-1",
  status: "REGISTERED", readiness_status: "READY" };
const session = { id: 4, status: "PUBLISHED", start_date: "2026-07-01", end_date: "2026-07-10" };
const today = { date: "2026-07-03", rows: [{
  ...child, checkin_time: null, checkout_time: null, pickup_verified: false,
}] };

describe("Summer Camp live roster and custody", () => {
  it("requires actual API shapes, session identity and local custody date", () => {
    expect(campSessions([session])).toHaveLength(1);
    expect(() => campSessions({ results: [session] })).toThrow();
    expect(campRoster({ session_id: "4", rows: [child] }, 4)).toHaveLength(1);
    expect(() => campRoster({ session_id: "5", rows: [child] }, 4)).toThrow();
    expect(campToday(today)).toEqual(today);
    expect(() => campToday({ rows: [] })).toThrow();
  });

  it("never matches another child, session or enrollment for custody", () => {
    expect(currentCampCustody(child, today, 4)).toEqual(today.rows[0]);
    expect(currentCampCustody(child, { ...today, rows: [{ ...today.rows[0], student_id: "other" }] }, 4)).toBeNull();
    expect(currentCampCustody(child, { ...today, rows: [{ ...today.rows[0], enrollment_id: "other" }] }, 4)).toBeNull();
    expect(currentCampCustody(child, today, 5)).toBeNull();
  });

  it("fails closed for missing evidence, duplicate registration, and stale dates", () => {
    expect(campCanCheckIn(child, today.rows[0], session, today.date)).toBe(true);
    expect(campCanCheckIn(child, null, session, today.date)).toBe(false);
    expect(campCanCheckIn(child, today.rows[0], session, "2026-08-01")).toBe(false);
    expect(campCanCheckIn({ ...child, readiness_status: "BLOCKED" }, today.rows[0], session, today.date)).toBe(false);
    expect(duplicateCampRegistration(child, [child, { ...child, enrollment_id: "12" }])).toBe(true);
    expect(campCanCheckIn(child, today.rows[0], session, today.date, true)).toBe(false);
  });

  it("requires an open attendance record for release and verified pickup for success label", () => {
    expect(campCanVerifyPickup(child, today.rows[0])).toBe(false);
    const checked = { ...today.rows[0], checkin_time: "08:00" };
    expect(campCanVerifyPickup(child, checked)).toBe(true);
    expect(campCanVerifyPickup(child, { ...checked, checkout_time: "16:00" })).toBe(false);
    expect(campCustodyLabel({ ...checked, checkout_time: "16:00", pickup_verified: false })).toContain("review");
    expect(campCustodyLabel({ ...checked, checkout_time: "16:00", pickup_verified: true })).toContain("verified");
  });

  it("blocks manual-review and ambiguous open custody without hiding custody", () => {
    const checked = { ...today.rows[0], checkin_time: "2026-07-02T23:55:00-04:00" };
    expect(campCanVerifyPickup(child, { ...checked, requires_supervisor_reconciliation: true })).toBe(false);
    expect(campCanVerifyPickup(child, { ...checked, open_custody_count: 2 })).toBe(false);
    expect(campCanVerifyPickup(child, { ...checked, open_custody_count: 1 })).toBe(true);
    expect(campCustodyLabel({ ...checked, requires_supervisor_reconciliation: true })).toContain("supervisor");
  });

  it("rejects mismatched and malformed pickup choices", () => {
    expect(campPickupContacts({ enrollment_id: 11, contacts: [{ id: 7, name: "Guardian" }] }, 11)).toHaveLength(1);
    expect(() => campPickupContacts({ enrollment_id: 12, contacts: [] }, 11)).toThrow();
    expect(() => campPickupContacts({ enrollment_id: 11, contacts: [{ id: "not-number" }] }, 11)).toThrow();
  });
});
