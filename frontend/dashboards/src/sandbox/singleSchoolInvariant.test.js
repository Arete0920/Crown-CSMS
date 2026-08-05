import { describe, expect, it } from "vitest";

import {
  SANDBOX_SCHOOL_ARCHETYPES,
  SANDBOX_TRACKS,
  getSandboxSchool,
  getTrackSchools,
} from "./sandboxExperience";

describe("single sandbox school invariant", () => {
  it("exposes only Heritage Christian Academy", () => {
    expect(SANDBOX_TRACKS).toHaveLength(1);
    expect(SANDBOX_TRACKS[0].key).toBe("school");
    expect(SANDBOX_SCHOOL_ARCHETYPES).toHaveLength(1);
    expect(SANDBOX_SCHOOL_ARCHETYPES[0]).toMatchObject({
      key: "heritage-core",
      name: "Heritage Christian Academy",
    });
    expect(getTrackSchools("school")).toEqual(SANDBOX_SCHOOL_ARCHETYPES);
  });

  it("normalizes every school request to Heritage", () => {
    const heritage = SANDBOX_SCHOOL_ARCHETYPES[0];
    for (const value of [undefined, "heritage", "trinity-k12", "grace-finance", "unknown-school"]) {
      expect(getSandboxSchool(value)).toEqual(heritage);
    }
  });
});
