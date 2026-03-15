import { describe, expect, it } from "vitest";

const financeOnly = ["super_admin", "school_admin", "finance_admin"];

function canAccess(userRoles, allowedRoles) {
  return userRoles.some((role) => allowedRoles.includes(role));
}

describe("compuwerx package 4 route access", () => {
  it("admits finance_admin", () => {
    expect(canAccess(["finance_admin"], financeOnly)).toBe(true);
  });

  it("blocks parent", () => {
    expect(canAccess(["parent"], financeOnly)).toBe(false);
  });

  it("blocks student", () => {
    expect(canAccess(["student"], financeOnly)).toBe(false);
  });
});
