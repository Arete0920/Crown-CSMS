import { describe, expect, it } from "vitest";
import { certificationMatrix } from "./certification-matrix";

const REQUIRED_AUTHENTICATED_DASHBOARD_ROUTES = [
  {
    route: "/school-admin-dashboard",
    persona: "sandbox-admin",
    expectedApi: "/api/v1/dashboards/school-administrator/summary",
  },
  {
    route: "/admin",
    persona: "sandbox-admin",
    expectedApi: "/api/v1/dashboards/school-administrator/summary",
  },
  {
    route: "/dash/admin",
    persona: "sandbox-admin",
    expectedApi: "/api/dashboards/summary/",
  },
  {
    route: "/teacher",
    persona: "sandbox-teacher",
    expectedApi: "/api/v1/dashboards/teacher/summary",
  },
  {
    route: "/dash/teacher",
    persona: "sandbox-teacher",
    expectedApi: "/api/dashboards/summary/",
  },
  {
    route: "/parent",
    persona: "sandbox-parent",
    expectedApi: "/api/v1/dashboards/parent/summary",
  },
  {
    route: "/dash/parent",
    persona: "sandbox-parent",
    expectedApi: "/api/dashboards/summary/",
  },
];

describe("authenticated dashboard proof matrix", () => {
  it.each(REQUIRED_AUTHENTICATED_DASHBOARD_ROUTES)(
    "retains $route for $persona with its owning API contract",
    ({ route, persona, expectedApi }) => {
      const surface = certificationMatrix.find((candidate) => candidate.route === route);

      expect(surface).toBeDefined();
      expect(surface?.kind).toBe("dashboard");
      expect(surface?.personas).toEqual([persona]);
      expect(surface?.requireLiveProvenance).toBe(true);
      expect(surface?.provenanceRequiredApiFragments).toEqual([expectedApi]);
      expect(surface?.expectedApiFragments).toContain(expectedApi);
    },
  );

  it("keeps every required route unique", () => {
    const routes = REQUIRED_AUTHENTICATED_DASHBOARD_ROUTES.map(({ route }) => route);
    const matchingRows = certificationMatrix.filter((surface) => routes.includes(surface.route));

    expect(matchingRows).toHaveLength(routes.length);
    expect(new Set(matchingRows.map((surface) => surface.route)).size).toBe(routes.length);
  });
});
