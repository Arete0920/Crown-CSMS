import { describe, expect, it } from "vitest";
import { classifyProvenance } from "./network-recorder";

describe("classifyProvenance", () => {
  it("fails closed when provenance metadata is missing", () => {
    const result = classifyProvenance({
      data: { value: 1 },
    });

    expect(result.hasProvenance).toBe(false);
    expect(result.nonLiveValues).toEqual([]);
  });

  it("detects explicit non-live provenance", () => {
    const result = classifyProvenance({
      meta: { served_from: "snapshot" },
    });

    expect(result.hasProvenance).toBe(true);
    expect(result.nonLiveValues).toEqual([
      {
        url: "",
        method: undefined,
        status: undefined,
        value: "snapshot",
        source: "meta.served_from",
      },
    ]);
  });

  it("accepts live provenance markers", () => {
    const result = classifyProvenance({
      meta: { served_from: "live_db" },
      provenance: "api",
    });

    expect(result.hasProvenance).toBe(true);
    expect(result.nonLiveValues).toEqual([]);
  });
});
