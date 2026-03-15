import { describe, expect, it } from "vitest";

const protectedRoutes = [
  {
    path: "/finance/family-account",
    allowedRoles: ["super_admin", "school_admin", "finance_admin"],
  },
  {
    path: "/finance/disputes",
    allowedRoles: ["super_admin", "school_admin", "finance_admin"],
  },
  {
    path: "/finance/payout-reconciliation",
    allowedRoles: ["super_admin", "school_admin", "finance_admin"],
  },
];

function canAccess(userRoles, allowedRoles) {
  return userRoles.some((role) => allowedRoles.includes(role));
}

describe("compuwerx ops route access", () => {
  it("admits finance admin for every route", () => {
    for (const route of protectedRoutes) {
      expect(canAccess(["finance_admin"], route.allowedRoles)).toBe(true);
    }
  });

  it("blocks parent for every route", () => {
    for (const route of protectedRoutes) {
      expect(canAccess(["parent"], route.allowedRoles)).toBe(false);
    }
  });

  it("blocks student for every route", () => {
    for (const route of protectedRoutes) {
      expect(canAccess(["student"], route.allowedRoles)).toBe(false);
    }
  });
});
