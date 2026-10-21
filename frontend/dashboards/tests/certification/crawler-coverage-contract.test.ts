import { describe, expect, it } from "vitest";
import { PATHS } from "../../src/routes/paths.js";
import { router as assembledRouter } from "../../src/routes/router.jsx";
import { WIZARD_MANIFEST } from "../../src/routes/wizard-manifest.js";
import { certificationMatrix } from "./certification-matrix";

/**
 * Source-level inventory contract only. These assertions cannot certify that a
 * browser visited a route, an API returned live data, or a write persisted.
 * See #273 for deployed exact-SHA runtime acceptance.
 */
const namedRoutes = [...new Set(Object.values(PATHS).filter(
  (route): route is string => typeof route === "string" && route.startsWith("/"),
))];
const declaredRoutes = [...new Set([...namedRoutes, ...assembledRouter.routes.map((route) => route.path)].filter(
  (route): route is string => typeof route === "string" && route.startsWith("/"),
))];
const matrixRoutes = certificationMatrix.map((surface) => surface.route);
const explicitWizardPaths = WIZARD_MANIFEST.map((wizard) => wizard.path);

function routeMatchesDeclaredPattern(pattern: string, actualRoute: string): boolean {
  const template = pattern.split("/");
  const actual = actualRoute.split("/");
  return template.length === actual.length
    && template.every((part, index) => part.startsWith(":")
      ? actual[index].length > 0
      : part === actual[index]);
}

function isNamedRoute(route: string): boolean {
  // Dynamic /dash/:role can cover /dash/admin, but it cannot cover an
  // unrelated two-segment path such as /students/:id.
  // Literal aliases in the assembled router are executable routes even when
  // they have no PATHS constant. The catch-all must never count as coverage.
  return declaredRoutes.some((pattern) => routeMatchesDeclaredPattern(pattern, route));
}

describe("crawler coverage inventory contract (not live certification)", () => {
  it("keeps every crawler target linked to a declared frontend path", () => {
    const notDeclared = matrixRoutes.filter((route) => !isNamedRoute(route));
    expect(notDeclared).toEqual([]);
  });

  it("does not count unrelated routes as covered by dynamic path patterns", () => {
    expect(routeMatchesDeclaredPattern("/dash/:role", "/dash/admin")).toBe(true);
    expect(routeMatchesDeclaredPattern("/students/:id", "/students/synthetic-id")).toBe(true);
    expect(routeMatchesDeclaredPattern("/students/:id", "/dash/admin")).toBe(false);
    expect(routeMatchesDeclaredPattern("/dash/:role", "/other/admin")).toBe(false);
    expect(routeMatchesDeclaredPattern("/dash/:role", "/dash/admin/extra")).toBe(false);
  });

  it("keeps unique surface identifiers and route/persona/tenant combinations", () => {
    expect(new Set(certificationMatrix.map((surface) => surface.id)).size)
      .toBe(certificationMatrix.length);
    const keys = certificationMatrix.flatMap((surface) =>
      surface.personas.flatMap((persona) =>
        surface.tenants.map((tenant) => `${surface.route}|${persona}|${tenant}`)));
    expect(new Set(keys).size).toBe(keys.length);
    expect(certificationMatrix.every((surface) =>
      surface.personas.length > 0 && surface.tenants.length > 0)).toBe(true);
  });

  it("requires a provenance-backed API contract for certified dashboards", () => {
    for (const surface of certificationMatrix.filter((row) => row.kind === "dashboard")) {
      expect(surface.requireLiveProvenance, surface.id).toBe(true);
      expect(surface.provenanceRequiredApiFragments?.length ?? 0, surface.id)
        .toBeGreaterThan(0);
      for (const api of surface.provenanceRequiredApiFragments ?? []) {
        expect(surface.expectedApiFragments, surface.id).toContain(api);
      }
    }
  });

  it("reports explicitly uncovered paths and wizard journeys without claiming a PASS", () => {
    const covered = new Set(matrixRoutes);
    const uncoveredNamedPaths = namedRoutes.filter((path) =>
      !matrixRoutes.some((actual) => routeMatchesDeclaredPattern(path, actual)));
    const uncoveredWizards = explicitWizardPaths.filter((path) => !covered.has(path));

    const snapshot = {
      evidence_class: "SOURCE_INVENTORY_ONLY",
      named_paths: namedRoutes.length,
      matrix_routes: covered.size,
      untested_named_path_count: uncoveredNamedPaths.length,
      wizard_manifest_entries: WIZARD_MANIFEST.length,
      wizard_paths_not_explicitly_crawled: uncoveredWizards.length,
      untested_named_paths: uncoveredNamedPaths,
      wizard_paths_not_in_matrix: uncoveredWizards,
      live_runtime_certified: false,
    };
    console.info("CROWN_CRAWLER_COVERAGE_AUDIT " + JSON.stringify(snapshot));
    expect(covered.size).toBeGreaterThan(0);
    expect(WIZARD_MANIFEST.length).toBeGreaterThan(0);
    expect(snapshot.live_runtime_certified).toBe(false);
  });
});

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
