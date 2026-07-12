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

  it.each(["snapshot", "sample", "fallback", "unknown"])(
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

  it("designated API with explicit live provenance passes", () => {
    const result = evaluateProvenanceRequirement({
      url: "/api/dashboards/summary/",
      status: 200,
      body: { meta: { served_from: "live_db" } },
      provenanceRequiredApiFragments: designatedDataApi,
    });

    expect(result.enforced).toBe(true);
    expect(result.missing).toBe(false);
    expect(result.nonLiveValues).toEqual([]);
  });
});
