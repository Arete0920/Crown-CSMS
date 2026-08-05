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
  it("defines only the school track", () => {
    expect(SANDBOX_TRACKS.map((track) => track.key)).toEqual(["school"]);
  });

  it("defines exactly one sandbox school: Heritage Christian Academy", () => {
    expect(SANDBOX_SCHOOL_ARCHETYPES).toHaveLength(1);
    expect(SANDBOX_SCHOOL_ARCHETYPES[0]).toMatchObject({
      key: "heritage-core",
      name: "Heritage Christian Academy",
      track: "school",
      demo_data_only: true,
    });
    expect(getTrackSchools("school")).toHaveLength(1);
    expect(getTrackSchools("daycare")).toEqual([]);
    expect(getTrackSchools("camp")).toEqual([]);
  });

  it("keeps every sandbox persona tied only to Heritage and the school track", () => {
    expect(SANDBOX_PERSONAS.length).toBeGreaterThanOrEqual(5);
    for (const persona of SANDBOX_PERSONAS) {
      expect(persona.trackKeys).toEqual(["school"]);
      expect(persona.defaultSchoolId).toBe(SANDBOX_SCHOOL_ARCHETYPES[0].id);
    }
    expect(getTrackPersonas("school").map((persona) => persona.value)).toContain("student");
  });

  it("falls back safely to Heritage for unknown keys", () => {
    expect(getSandboxTrack("unknown").key).toBe("school");
    expect(getSandboxPersona("unknown").value).toBe("school_admin");
    expect(getSandboxSchool("unknown").key).toBe("heritage-core");
  });

  it("always builds sandbox URLs with the Heritage school id", () => {
    const href = getSandboxLoginHref(
      "finance_director",
      "unknown-school-id",
      "unknown-track",
      "self-guided"
    );
    const url = new URL(href, "https://example.test");

    expect(url.pathname).toBe("/sandbox/command-center");
    expect(url.searchParams.get("mode")).toBe("sandbox");
    expect(url.searchParams.get("experience")).toBe("school");
    expect(url.searchParams.get("guidance")).toBe("self-guided");
    expect(url.searchParams.get("role")).toBe("finance_director");
    expect(url.searchParams.get("school")).toBe(SANDBOX_SCHOOL_ARCHETYPES[0].id);
    expect(url.searchParams.get("tour")).toBeTruthy();
  });
});
