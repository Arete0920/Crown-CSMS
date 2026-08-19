import { describe, expect, it } from "vitest";
import {
  filterVisibleNav,
  getUserRoles,
  hasAnyRole,
  hasAllRoles,
  normalizeRoles,
} from "./roleAccess";

describe("roleAccess", () => {
  it("normalizes equivalent role labels", () => {
    expect(normalizeRoles(["head_of_school"])).toContain("school_admin");
    expect(normalizeRoles(["finance"])).toContain("finance_admin");
    expect(normalizeRoles(["admissions"])).toContain("admissions_manager");
    expect(normalizeRoles(["admissions_director"])).toContain("admissions_manager");
    expect(normalizeRoles(["facilities"])).toContain("facilities_manager");
    expect(normalizeRoles(["it"])).toContain("it_support");
    expect(normalizeRoles(["safety"])).toContain("safety_manager");
    expect(normalizeRoles(["security"])).toContain("security_officer");
  });

  it("extracts roles from common auth payload shapes", () => {
    expect(getUserRoles({ role: "head_of_school" })).toContain("school_admin");
    expect(getUserRoles({ roles: ["finance"] })).toContain("finance_admin");
    expect(getUserRoles({ user: { role: "admissions" } })).toContain("admissions_manager");
    expect(getUserRoles({ user: { role: "admissions_director" } })).toContain("admissions_manager");
    expect(getUserRoles({ profile: { roles: [{ code: "it" }] } })).toContain("it_support");
  });

  it("passes any-role checks through alias normalization", () => {
    expect(hasAnyRole({ role: "head_of_school" }, ["school_admin"])).toBe(true);
    expect(hasAnyRole({ roles: ["finance"] }, ["finance_admin"])).toBe(true);
    expect(hasAnyRole({ roles: ["admissions"] }, ["admissions_manager", "registrar"])).toBe(true);
    expect(hasAnyRole({ roles: ["admissions_director"] }, ["admissions_manager"])).toBe(true);
    expect(hasAnyRole({ roles: ["teacher"] }, ["finance_admin"])).toBe(false);
  });

  it("passes all-role checks through alias normalization", () => {
    expect(
      hasAllRoles(
        { roles: ["head_of_school", "finance"] },
        ["school_admin", "finance_admin"],
      ),
    ).toBe(true);

    expect(
      hasAllRoles(
        { roles: ["head_of_school"] },
        ["school_admin", "finance_admin"],
      ),
    ).toBe(false);
  });

  it("filters visible nav items by runtime role access", () => {
    const nav = [
      { label: "Home", href: "/" },
      { label: "Finance", href: "/finance", roles: ["finance_admin"] },
      { label: "Admissions", href: "/admissions", roles: ["admissions_manager"] },
      {
        label: "Admin",
        children: [
          { label: "Settings", href: "/settings", roles: ["school_admin"] },
          { label: "IT", href: "/it", roles: ["it_support"] },
        ],
      },
    ];

    const financeUserNav = filterVisibleNav(nav, { roles: ["finance"] });
    const labels = financeUserNav.map((item) => item.label);

    expect(labels).toContain("Home");
    expect(labels).toContain("Finance");
    expect(labels).not.toContain("Admissions");

    const adminSection = financeUserNav.find((item) => item.label === "Admin");
    expect(adminSection).toBeDefined();
    expect(adminSection.children).toEqual([]);
  });

  it("retains admin children for equivalent admin role labels", () => {
    const nav = [
      {
        label: "Admin",
        children: [{ label: "Settings", href: "/settings", roles: ["school_admin"] }],
      },
    ];

    const result = filterVisibleNav(nav, { role: "head_of_school" });
    expect(result[0].children).toHaveLength(1);
    expect(result[0].children[0].label).toBe("Settings");
  });
});
