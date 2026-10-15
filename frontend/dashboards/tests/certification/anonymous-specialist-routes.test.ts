import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";

const router = readFileSync(new URL("../../src/routes/router.jsx", import.meta.url), "utf8");
const guard = readFileSync(new URL("../../src/components/routing/AuthenticatedSchoolRouteGuard.jsx", import.meta.url), "utf8");

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
