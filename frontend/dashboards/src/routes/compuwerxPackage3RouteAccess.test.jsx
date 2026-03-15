import { describe, expect, it } from "vitest";

const financeOnly = ["super_admin", "school_admin", "finance_admin"];
const householdRoutes = [
  "super_admin",
  "school_admin",
  "finance_admin",
  "parent",
];

function canAccess(userRoles, allowedRoles) {
  return userRoles.some((role) => allowedRoles.includes(role));
}

describe("compuwerx package 3 route access", () => {
  it("admits finance_admin to finance-only routes", () => {
    expect(canAccess(["finance_admin"], financeOnly)).toBe(true);
  });

  it("admits parent only to household-linked routes", () => {
    expect(canAccess(["parent"], householdRoutes)).toBe(true);
    expect(canAccess(["parent"], financeOnly)).toBe(false);
  });

  it("blocks student from package 3 routes", () => {
    expect(canAccess(["student"], householdRoutes)).toBe(false);
    expect(canAccess(["student"], financeOnly)).toBe(false);
  });
});
