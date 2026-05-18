import { describe, expect, it } from "vitest";
import { KPI_REGISTRY, buildKpiRoute } from "../kpiRegistry";

const KNOWN_ROUTE_PREFIXES = [
  "/",
  "/dashboard",
  "/executive-360",
  "/students",
  "/student360",
  "/attendance",
  "/finance",
  "/billing",
  "/enrollment",
  "/admissions",
  "/gradebook",
  "/discipline",
  "/service-hours",
  "/spiritual-life",
  "/messages",
  "/board",
  "/compliance",
  "/compliance-audit-dashboard",
  "/staff",
  "/hr",
];

describe("dashboard KPI registry route integrity", () => {
  it("every KPI has a stable id, title, route, and source endpoint", () => {
    for (const kpi of KPI_REGISTRY) {
      expect(kpi.id).toMatch(/^[a-z0-9_:-]+$/);
      expect(kpi.title).toBeTruthy();
      expect(kpi.sourceEndpoint || kpi.source || kpi.endpoint).toBeTruthy();
      expect(kpi.route || kpi.path).toBeTruthy();
    }
  });

  it("every KPI drilldown route is absolute and maps to a known Crown route family", () => {
    for (const kpi of KPI_REGISTRY) {
      const route = buildKpiRoute(kpi);
      expect(route).toMatch(/^\//);

      const pathOnly = route.split("?")[0];
      const matched = KNOWN_ROUTE_PREFIXES.some(
        (prefix) => pathOnly === prefix || pathOnly.startsWith(`${prefix}/`)
      );

      expect(matched, `${kpi.id} has unknown route ${route}`).toBe(true);
    }
  });

  it("every KPI action has a usable label and href", () => {
    for (const kpi of KPI_REGISTRY) {
      const actions = kpi.actions || [];
      for (const action of actions) {
        expect(action.label).toBeTruthy();
        expect(action.href || action.to || action.route).toMatch(/^\//);
      }
    }
  });
});
