import { describe, expect, it } from "vitest";
import { evaluateProvenanceRequirement } from "./network-recorder";

describe("evaluateProvenanceRequirement", () => {
  const designatedDataApi = ["/api/dashboards/"];

  it("auth JSON without provenance does not fail", () => {
    const result = evaluateProvenanceRequirement({
      url: "/api/v1/auth/me",
      status: 200,
      body: { user: { id: "u1" } },
      provenanceRequiredApiFragments: designatedDataApi,
    });

    expect(result.enforced).toBe(false);
    expect(result.missing).toBe(false);
    expect(result.nonLiveValues).toEqual([]);
  });

  it("navigation JSON without provenance does not fail", () => {
    const result = evaluateProvenanceRequirement({
      url: "/api/v1/nav",
      status: 200,
      body: { links: [] },
      provenanceRequiredApiFragments: designatedDataApi,
    });

    expect(result.enforced).toBe(false);
    expect(result.missing).toBe(false);
    expect(result.nonLiveValues).toEqual([]);
  });

  it("designated dashboard API JSON without provenance fails", () => {
    const result = evaluateProvenanceRequirement({
      url: "/api/dashboards/summary/",
      status: 200,
      body: { metrics: [] },
      provenanceRequiredApiFragments: designatedDataApi,
    });

    expect(result.enforced).toBe(true);
    expect(result.missing).toBe(true);
    expect(result.nonLiveValues).toEqual([]);
  });

  it.each([
    { meta: { served_from: null } },
    { meta: { served_from: "" } },
    { meta: { served_from: "   " } },
    { meta: { provenance: null } },
    { provenance: "" },
  ])("blank provenance value is treated as missing: %o", (body) => {
    const result = evaluateProvenanceRequirement({
      url: "/api/dashboards/summary/",
      status: 200,
      body,
      provenanceRequiredApiFragments: designatedDataApi,
    });

    expect(result.enforced).toBe(true);
    expect(result.missing).toBe(true);
    expect(result.nonLiveValues).toEqual([]);
  });

  it.each(["snapshot", "sample", "fallback", "unknown", "seed-command", "scaffold", "cached"])(
    "designated API with %s provenance fails",
    (value) => {
      const result = evaluateProvenanceRequirement({
        url: "/api/dashboards/summary/",
        status: 200,
        body: { meta: { served_from: value } },
        provenanceRequiredApiFragments: designatedDataApi,
      });

      expect(result.enforced).toBe(true);
      expect(result.missing).toBe(false);
      expect(result.nonLiveValues.length).toBeGreaterThan(0);
      expect(result.nonLiveValues[0]?.value).toBe(value);
    },
  );

  it.each(["live", "live_db"])(
    "designated API with explicit %s provenance passes",
    (value) => {
      const result = evaluateProvenanceRequirement({
        url: "/api/dashboards/summary/",
        status: 200,
        body: { meta: { served_from: value } },
        provenanceRequiredApiFragments: designatedDataApi,
      });

      expect(result.enforced).toBe(true);
      expect(result.missing).toBe(false);
      expect(result.nonLiveValues).toEqual([]);
    },
  );

  it("error responses do not create missing-provenance noise", () => {
    const result = evaluateProvenanceRequirement({
      url: "/api/dashboards/summary/",
      status: 503,
      body: { code: "dashboard_live_data_required" },
      provenanceRequiredApiFragments: designatedDataApi,
    });

    expect(result.enforced).toBe(true);
    expect(result.missing).toBe(false);
    expect(result.nonLiveValues).toEqual([]);
  });
});
