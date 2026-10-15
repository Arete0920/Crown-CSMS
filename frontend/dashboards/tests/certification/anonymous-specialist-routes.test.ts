import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";

// Vitest may transform import.meta.url to a non-file virtual URL. CI runs
// with frontend/dashboards as cwd; explicit repo-relative paths are stable.
const router = readFileSync("src/routes/router.jsx", "utf8");
const guard = readFileSync("src/components/routing/AuthenticatedSchoolRouteGuard.jsx", "utf8");

const specialistRoutes = [
  "BOARD", "IT", "MARKETING", "SPIRITUAL_LIFE", "MASTER_CONTROL",
  "OFFICE", "HEALTH", "COUNSELING", "FOOD", "ATHLETICS",
  "ADVANCEMENT", "TRANSPORTATION", "FACILITIES", "SECURITY",
  "ACADEMIC_SUPPORT", "FINE_ARTS", "LIBRARY", "EXTENDED_CARE",
  "REGISTRAR", "COMMUNICATIONS_DIRECTOR", "PD", "STUDENT_SERVICES",
  "SAFETY", "BOARD_EXECUTIVE",
];

describe("anonymous specialist route denial contract", () => {
  it.each(specialistRoutes)("protects %s with session and tenant prerequisites", (name) => {
    const path = `path: PATHS.${name},`;
    const start = router.indexOf(path);
    expect(start, name).toBeGreaterThanOrEqual(0);
    const block = router.slice(start, router.indexOf("},", start) + 2);
    expect(block, name).toContain("<AuthenticatedSchoolRouteGuard>");
    expect(block, name).toContain("</AuthenticatedSchoolRouteGuard>");
  });

  it.each([
    "PATHS.ROLE_DASHBOARD", "PATHS.WIZARDS", "PATHS.HR",
    "PATHS.AFTERCARE_ROSTER", "PATHS.WIZARD_AFTERCARE_SETUP",
    "PATHS.ADMISSIONS_PIPELINE", "PATHS.STUDENT_LIFE", "PATHS.SETTINGS",
    "'/students/:id'",
  ])("guards sensitive route %s", (name) => {
    const start = router.indexOf(`path: ${name},`);
    expect(start, name).toBeGreaterThanOrEqual(0);
    const next = router.indexOf("\n  },", start);
    const block = router.slice(start, next);
    expect(block, name).toContain("<AuthenticatedSchoolRouteGuard>");
    expect(block, name).toContain("</AuthenticatedSchoolRouteGuard>");
  });

  it("restricts HR, settings, admissions pipeline and aftercare to assigned roles", () => {
    for (const name of ["PATHS.HR", "PATHS.SETTINGS", "PATHS.ADMISSIONS_PIPELINE", "PATHS.AFTERCARE_ROSTER"]) {
      const start = router.indexOf(`path: ${name},`);
      const block = router.slice(start, router.indexOf("\n  },", start));
      expect(block, name).toContain("<RoleRouteGuard allowedRoles=");
    }
  });

  it("protects the board route with an explicit role policy", () => {
    const start = router.indexOf("path: PATHS.BOARD,");
    const block = router.slice(start, router.indexOf("},", start) + 2);
    expect(block).toContain("<RoleRouteGuard allowedRoles=");
    expect(block).toContain('"board_member"');
  });

  it("denies routes with missing bearer or school rather than showing data", () => {
    expect(guard).toContain("!getAccessToken() || !getSelectedSchoolId()");
    expect(guard).toContain('to="/not-authorized"');
    expect(guard).not.toContain("localStorage");
  });
});
