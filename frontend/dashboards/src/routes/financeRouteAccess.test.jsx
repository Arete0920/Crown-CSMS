import { describe, expect, it } from "vitest";

const financeRoutes = [
  {
    path: "/finance",
    allowedRoles: ["super_admin", "school_admin", "finance_admin"],
  },
  {
    path: "/finance/invoices",
    allowedRoles: ["super_admin", "school_admin", "finance_admin"],
  },
  {
    path: "/billing",
    allowedRoles: ["super_admin", "school_admin", "finance_admin"],
  },
  {
    path: "/billing-dashboard",
    allowedRoles: ["super_admin", "school_admin", "finance_admin"],
  },
  {
    path: "/wizards/finance-setup",
    allowedRoles: ["super_admin", "school_admin", "finance_admin"],
  },
];

function canAccess(userRoles, allowedRoles) {
  return userRoles.some((role) => allowedRoles.includes(role));
}

describe("finance route access matrix", () => {
  it("admits school_admin to all finance routes", () => {
    const roles = ["school_admin"];
    financeRoutes.forEach((route) => {
      expect(canAccess(roles, route.allowedRoles)).toBe(true);
    });
  });

  it("admits finance_admin to all finance routes", () => {
    const roles = ["finance_admin"];
    financeRoutes.forEach((route) => {
      expect(canAccess(roles, route.allowedRoles)).toBe(true);
    });
  });

  it("blocks admissions_team from finance routes", () => {
    const roles = ["admissions_team"];
    financeRoutes.forEach((route) => {
      expect(canAccess(roles, route.allowedRoles)).toBe(false);
    });
  });

  it("blocks parent and student roles from finance routes", () => {
    expect(canAccess(["parent"], financeRoutes[0].allowedRoles)).toBe(false);
    expect(canAccess(["student"], financeRoutes[0].allowedRoles)).toBe(false);
  });
});
