import { describe, expect, it } from "vitest";
import { collectVisibleStateBlockers } from "./assertions";

describe("production certification visible-state blockers", () => {
  it.each([
    ["Admin Dashboard\nLoading...", "persistent loading state detected"],
    ["Loading dashboard records.", "persistent loading state detected"],
    ["Loading dashboard summary service (billing)", "persistent loading state detected"],
    ["Dashboard summary service unavailable (undefined)", "dashboard summary service unavailable"],
    ["Dashboard data unavailable", "dashboard data unavailable"],
    ["Navigation Unavailable", "navigation unavailable"],
    ["Wizard Hub\n0 setup wizards available", "empty wizard registry"],
    ["Access Denied", "unexpected authorization denial"],
  ])("rejects %s", (body, expected) => {
    expect(collectVisibleStateBlockers(body)).toContain(expected);
  });

  it("accepts a settled non-error page", () => {
    expect(collectVisibleStateBlockers("Finance Dashboard\nUpdated 9:42 AM")).toEqual([]);
  });
});
