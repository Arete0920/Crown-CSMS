import { describe, expect, it } from "vitest";
import { deriveSessionTotals } from "./CareSessionDirectorDashboard.jsx";

describe("AM/PM care roster aggregates", () => {
  const rows = [
    { student_id: "a", attendance: { checkin_time: "start", checkout_time: "end", handoff_time: "end", handoff_verified: true } },
    { student_id: "b", attendance: { checkin_time: "start", checkout_time: null } },
    { student_id: "c", attendance: null },
  ];
  it("separates morning school handoff and ongoing supervision", () => {
    expect(deriveSessionTotals(rows, "AM")).toEqual({
      expected: 3, checkedIn: 2, present: 1, completed: 1, unverifiedClosures: 0,
      awaitingArrival: 1, latePickups: 0, lateFeeCents: 0,
    });
  });
  it("never treats an AM handoff as PM pickup", () => {
    expect(deriveSessionTotals(rows, "PM").completed).toBe(0);
  });
  it("counts late fees assessed without claiming cash receipts", () => {
    expect(deriveSessionTotals([{ student_id: "d", attendance: {
      checkin_time: "start", checkout_time: "end", pickup_verified: true,
      late_minutes: 11, late_fee_cents: 2000,
    } }], "PM")).toEqual({
      expected: 1, checkedIn: 1, present: 0, completed: 1, unverifiedClosures: 0,
      awaitingArrival: 0, latePickups: 1, lateFeeCents: 2000,
    });
  });  it("flags closed morning custody without a verified school handoff", () => {
    expect(deriveSessionTotals([{ student_id: "a", attendance: {
      checkin_time: "start", checkout_time: "end", handoff_time: null, handoff_verified: false,
    } }], "AM")).toMatchObject({
      checkedIn: 1, present: 0, completed: 0, unverifiedClosures: 1,
    });
  });
  it("flags a recorded afternoon checkout without verified authorized pickup", () => {
    expect(deriveSessionTotals([{ student_id: "b", attendance: {
      checkin_time: "start", checkout_time: "end", pickup_verified: false,
    } }], "PM")).toMatchObject({
      checkedIn: 1, present: 0, completed: 0, unverifiedClosures: 1,
    });
  });
});
