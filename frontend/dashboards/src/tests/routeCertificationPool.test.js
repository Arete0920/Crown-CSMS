import { describe, expect, it } from "vitest";
import { certifyWithConcurrency } from "../../scripts/route-certification-pool.mjs";

describe("route certification worker pool", () => {
  it("visits every route once, preserves order, and bounds concurrency", async () => {
    let active = 0;
    let maximum = 0;
    const visits = [];
    const result = await certifyWithConcurrency([0, 1, 2, 3, 4], 2, async (route) => {
      visits.push(route);
      maximum = Math.max(maximum, ++active);
      await new Promise((resolve) => setTimeout(resolve, route === 0 ? 20 : 1));
      active--;
      return `route-${route}`;
    });
    expect(maximum).toBe(2);
    expect(visits.sort()).toEqual([0, 1, 2, 3, 4]);
    expect(result).toEqual(["route-0", "route-1", "route-2", "route-3", "route-4"]);
  });

  it("propagates a fatal failure after other active work settles", async () => {
    let cleanedUp = false;
    await expect(certifyWithConcurrency([0, 1], 2, async (route) => {
      if (route === 0) throw new Error("Browser failed");
      await new Promise((resolve) => setTimeout(resolve, 10));
      cleanedUp = true;
      return route;
    })).rejects.toThrow("Browser failed");
    expect(cleanedUp).toBe(true);
  });

  it("rejects invalid limits and handles an empty inventory", async () => {
    await expect(certifyWithConcurrency([1], 0, () => 1)).rejects.toThrow("Invalid certification concurrency");
    expect(await certifyWithConcurrency([], 2, () => 1)).toEqual([]);
  });
});
