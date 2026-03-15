import { describe, expect, it } from "vitest";
import { WIZARD_REGISTRY } from "./wizards.js";

function getAllowedRoles(path) {
  const route = WIZARD_REGISTRY.find((item) => item.path === path);
  return route?.roles || [];
}

function canAccess(userRoles, allowedRoles) {
  return userRoles.some((role) => allowedRoles.includes(role));
}

describe("wizard route access matrix", () => {
  it("keeps unique wizard paths", () => {
    const paths = WIZARD_REGISTRY.map((item) => item.path);
    expect(new Set(paths).size).toBe(paths.length);
  });

  it("defines explicit allowed roles for every wizard route", () => {
    WIZARD_REGISTRY.forEach((route) => {
      expect(Array.isArray(route.roles)).toBe(true);
      expect(route.roles.length).toBeGreaterThan(0);
    });
  });

  it("admits expected admin routes", () => {
    const roles = ["school_admin"];
    [
      "/onboarding",
      "/reenrollment",
      "/aid-setup",
      "/enrollment-conversion",
      "/enrollment-period-setup",
    ].forEach((path) => {
      expect(canAccess(roles, getAllowedRoles(path))).toBe(true);
    });
  });

  it("admits admissions team only to appropriate routes", () => {
    const roles = ["admissions_manager"];
    expect(canAccess(roles, getAllowedRoles("/onboarding"))).toBe(true);
    expect(canAccess(roles, getAllowedRoles("/reenrollment"))).toBe(false);
    expect(canAccess(roles, getAllowedRoles("/aid-setup"))).toBe(false);
    expect(canAccess(roles, getAllowedRoles("/enrollment-conversion"))).toBe(true);
    expect(canAccess(roles, getAllowedRoles("/enrollment-period-setup"))).toBe(false);
  });

  it("admits finance team only to aid setup", () => {
    const roles = ["finance_admin"];
    expect(canAccess(roles, getAllowedRoles("/onboarding"))).toBe(false);
    expect(canAccess(roles, getAllowedRoles("/reenrollment"))).toBe(false);
    expect(canAccess(roles, getAllowedRoles("/aid-setup"))).toBe(true);
    expect(canAccess(roles, getAllowedRoles("/enrollment-conversion"))).toBe(false);
    expect(canAccess(roles, getAllowedRoles("/enrollment-period-setup"))).toBe(false);
  });

  it("admits registrar only to reenrollment and enrollment setup routes", () => {
    const roles = ["registrar"];
    expect(canAccess(roles, getAllowedRoles("/onboarding"))).toBe(false);
    expect(canAccess(roles, getAllowedRoles("/reenrollment"))).toBe(true);
    expect(canAccess(roles, getAllowedRoles("/aid-setup"))).toBe(false);
    expect(canAccess(roles, getAllowedRoles("/enrollment-conversion"))).toBe(true);
    expect(canAccess(roles, getAllowedRoles("/enrollment-period-setup"))).toBe(true);
  });
});
