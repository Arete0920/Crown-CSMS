import { describe, expect, it } from "vitest";
import {
  evaluateProvenanceRequirement,
  isProvenanceDesignatedEndpoint,
  shouldRecordMissingProvenanceForNonJson,
} from "./network-recorder";

const designatedDataApi = ["/api/v1/dashboards/", "/api/dashboards/"];

describe("isProvenanceDesignatedEndpoint", () => {
  it.each([
    "/api/v1/dashboards/school-administrator/summary",
    "/api/dashboards/school-administrator/summary",
    "https://crown.example/api/v1/dashboards/school-administrator/summary?tenant=heritage",
  ])("matches a designated dashboard pathname: %s", (url) => {
    expect(isProvenanceDesignatedEndpoint(url, designatedDataApi)).toBe(true);
  });

  it.each([
    "https://crown.example/api/v1/auth/me?next=/api/v1/dashboards/summary",
    "https://api-v1-dashboards.example/api/v1/auth/me",
    "/api/v1/nav?returnTo=/api/dashboards/summary",
  ])("does not match dashboard text outside the pathname: %s", (url) => {
    expect(isProvenanceDesignatedEndpoint(url, designatedDataApi)).toBe(false);
  });

  it("ignores empty endpoint fragments", () => {
    expect(isProvenanceDesignatedEndpoint("/api/v1/auth/me", [""])).toBe(false);
  });
});

describe("shouldRecordMissingProvenanceForNonJson", () => {
  it.each(["text/html", "text/plain", ""])(
    "fails closed for designated successful non-JSON responses: %s",
    (contentType) => {
      expect(shouldRecordMissingProvenanceForNonJson({
        url: "/api/v1/dashboards/school-administrator/summary",
        status: 200,
        contentType,
        provenanceRequiredApiFragments: designatedDataApi,
      })).toBe(true);
    },
  );

  it("does not add provenance noise for designated error responses", () => {
    expect(shouldRecordMissingProvenanceForNonJson({
      url: "/api/v1/dashboards/school-administrator/summary",
      status: 502,
      contentType: "text/html",
      provenanceRequiredApiFragments: designatedDataApi,
    })).toBe(false);
  });

  it("does not enforce provenance on non-designated non-JSON responses", () => {
    expect(shouldRecordMissingProvenanceForNonJson({
      url: "/api/v1/auth/me",
      status: 200,
      contentType: "text/html",
      provenanceRequiredApiFragments: designatedDataApi,
    })).toBe(false);
  });
});

describe("evaluateProvenanceRequirement", () => {
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

  it("designated canonical dashboard API JSON without provenance fails", () => {
    const result = evaluateProvenanceRequirement({
      url: "/api/v1/dashboards/school-administrator/summary",
      status: 200,
      body: { metrics: [] },
      provenanceRequiredApiFragments: designatedDataApi,
    });

    expect(result.enforced).toBe(true);
    expect(result.missing).toBe(true);
    expect(result.nonLiveValues).toEqual([]);
  });

  it("designated compatibility dashboard API JSON without provenance fails", () => {
    const result = evaluateProvenanceRequirement({
      url: "/api/dashboards/school-administrator/summary",
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
      url: "/api/v1/dashboards/school-administrator/summary",
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
        url: "/api/v1/dashboards/school-administrator/summary",
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
        url: "/api/v1/dashboards/school-administrator/summary",
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
      url: "/api/v1/dashboards/school-administrator/summary",
      status: 503,
      body: { code: "dashboard_live_data_required" },
      provenanceRequiredApiFragments: designatedDataApi,
    });

    expect(result.enforced).toBe(true);
    expect(result.missing).toBe(false);
    expect(result.nonLiveValues).toEqual([]);
  });
});
