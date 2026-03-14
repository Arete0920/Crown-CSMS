import { describe, expect, it } from "vitest";

const wizardRoutes = [
  {
    path: "/onboarding",
    allowedRoles: ["super_admin", "school_admin", "admissions_manager"],
  },
  {
    path: "/reenrollment",
    allowedRoles: ["super_admin", "school_admin", "registrar"],
  },
  {
    path: "/aid-setup",
    allowedRoles: ["super_admin", "school_admin", "finance_admin"],
  },
  {
    path: "/enrollment-conversion",
    allowedRoles: [
      "super_admin",
      "school_admin",
      "admissions_manager",
      "registrar",
    ],
  },
  {
    path: "/enrollment-period-setup",
    allowedRoles: ["super_admin", "school_admin", "registrar"],
  },
];

function canAccess(userRoles, allowedRoles) {
  return userRoles.some((role) => allowedRoles.includes(role));
}

describe("wizard route access matrix", () => {
  it("admits expected admin routes", () => {
    const roles = ["school_admin"];
    wizardRoutes.forEach((route) => {
      expect(canAccess(roles, route.allowedRoles)).toBe(true);
    });
  });

  it("admits admissions team only to appropriate routes", () => {
    const roles = ["admissions_manager"];
    expect(canAccess(roles, wizardRoutes[0].allowedRoles)).toBe(true);
    expect(canAccess(roles, wizardRoutes[1].allowedRoles)).toBe(false);
    expect(canAccess(roles, wizardRoutes[2].allowedRoles)).toBe(false);
    expect(canAccess(roles, wizardRoutes[3].allowedRoles)).toBe(true);
    expect(canAccess(roles, wizardRoutes[4].allowedRoles)).toBe(false);
  });

  it("admits finance team only to aid setup", () => {
    const roles = ["finance_admin"];
    expect(canAccess(roles, wizardRoutes[0].allowedRoles)).toBe(false);
    expect(canAccess(roles, wizardRoutes[1].allowedRoles)).toBe(false);
    expect(canAccess(roles, wizardRoutes[2].allowedRoles)).toBe(true);
    expect(canAccess(roles, wizardRoutes[3].allowedRoles)).toBe(false);
    expect(canAccess(roles, wizardRoutes[4].allowedRoles)).toBe(false);
  });

  it("admits registrar only to reenrollment and enrollment setup routes", () => {
    const roles = ["registrar"];
    expect(canAccess(roles, wizardRoutes[0].allowedRoles)).toBe(false);
    expect(canAccess(roles, wizardRoutes[1].allowedRoles)).toBe(true);
    expect(canAccess(roles, wizardRoutes[2].allowedRoles)).toBe(false);
    expect(canAccess(roles, wizardRoutes[3].allowedRoles)).toBe(true);
    expect(canAccess(roles, wizardRoutes[4].allowedRoles)).toBe(true);
  });
});
