// @vitest-environment jsdom
import { describe, expect, it } from "vitest";
import {
  SANDBOX_PERSONAS,
  SANDBOX_SCHOOL_ARCHETYPES,
  SANDBOX_TRACKS,
  getSandboxLoginHref,
  getSandboxPersona,
  getSandboxSchool,
  getSandboxTrack,
  getTrackPersonas,
  getTrackSchools,
} from "../sandbox/sandboxExperience";

describe("sandbox experience catalog", () => {
  it("defines school, daycare, and camp tracks", () => {
    expect(SANDBOX_TRACKS.map((track) => track.key)).toEqual(["school", "daycare", "camp"]);
  });

  it("defines at least one archetype for each track", () => {
    for (const key of ["school", "daycare", "camp"]) {
      expect(getTrackSchools(key).length).toBeGreaterThan(0);
    }
  });

  it("defines persona coverage for each track", () => {
    expect(SANDBOX_PERSONAS.length).toBeGreaterThanOrEqual(5);
    expect(getTrackPersonas("school").map((persona) => persona.value)).toContain("student");
    expect(getTrackPersonas("daycare").map((persona) => persona.value)).not.toContain("student");
    expect(getTrackPersonas("camp").map((persona) => persona.value)).toContain("student");
  });

  it("falls back safely for unknown keys", () => {
    expect(getSandboxTrack("unknown").key).toBe("school");
    expect(getSandboxPersona("unknown").value).toBe("school_admin");
    expect(getSandboxSchool("unknown").key).toBe("heritage-core");
  });

  it("builds login URLs with track, mode, persona, school, and tour context", () => {
    const href = getSandboxLoginHref(
      "finance_director",
      "sandbox-school-grace-covenant-school",
      "school",
      "self-guided"
    );
    const url = new URL(href, "https://example.test");

    expect(url.pathname).toBe("/login");
    expect(url.searchParams.get("mode")).toBe("sandbox");
    expect(url.searchParams.get("experience")).toBe("school");
    expect(url.searchParams.get("guidance")).toBe("self-guided");
    expect(url.searchParams.get("role")).toBe("finance_director");
    expect(url.searchParams.get("school")).toBe("sandbox-school-grace-covenant-school");
    expect(url.searchParams.get("tour")).toBeTruthy();
  });

  it("keeps every visible archetype tied to a known track", () => {
    const trackKeys = SANDBOX_TRACKS.map((track) => track.key);
    for (const school of SANDBOX_SCHOOL_ARCHETYPES) {
      expect(trackKeys).toContain(school.track);
      expect(school.demo_data_only).not.toBe(false);
    }
  });
});
