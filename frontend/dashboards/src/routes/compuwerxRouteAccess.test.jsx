import { describe, expect, it } from "vitest";

const route = {
  path: "/finance/compuwerx-test",
  allowedRoles: ["super_admin", "school_admin", "finance_admin"],
};

function canAccess(userRoles, allowedRoles) {
  return userRoles.some((role) => allowedRoles.includes(role));
}

describe("compuwerx route access", () => {
  it("admits finance admin", () => {
    expect(canAccess(["finance_admin"], route.allowedRoles)).toBe(true);
  });

  it("blocks parent", () => {
    expect(canAccess(["parent"], route.allowedRoles)).toBe(false);
  });

  it("blocks student", () => {
    expect(canAccess(["student"], route.allowedRoles)).toBe(false);
  });
});
