import { describe, expect, it } from "vitest";
import { PATHS } from "../../src/routes/paths.js";
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
const matrixRoutes = certificationMatrix.map((surface) => surface.route);
const explicitWizardPaths = WIZARD_MANIFEST.map((wizard) => wizard.path);

function isNamedRoute(route: string): boolean {
  if (namedRoutes.includes(route)) return true;
  // A route such as /dash/admin is an instance of /dash/:role, not a
  // separate PATHS entry. Match whole segments; do not accept arbitrary URLs.
  return namedRoutes.some((pattern) => {
    if (!pattern.includes(":")) return false;
    const template = pattern.split("/");
    const actual = route.split("/");
    return template.length === actual.length
      && template.every((part, index) => part.startsWith(":")
        ? actual[index].length > 0
        : part === actual[index]);
  });
}

describe("crawler coverage inventory contract (not live certification)", () => {
  it("keeps every crawler target linked to a declared frontend path", () => {
    const notDeclared = matrixRoutes.filter((route) => !isNamedRoute(route));
    expect(notDeclared).toEqual([]);
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
      !covered.has(path) && !matrixRoutes.some((actual) =>
        actual !== path && path.includes(":") && isNamedRoute(actual)
        && path.split("/").length === actual.split("/").length));
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
