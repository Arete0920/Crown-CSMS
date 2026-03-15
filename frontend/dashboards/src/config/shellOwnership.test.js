import { describe, expect, it } from "vitest";
import {
  getDashboardRegistryPaths,
  getDuplicateOwnedPaths,
  getLikelyPlaceholderNavLinks,
  getOwnedShellPaths,
  getUnownedNavLinks,
  getWizardPaths,
  normalizePath,
} from "./shellOwnership";

describe("shellOwnership", () => {
  it("normalizes paths consistently", () => {
    expect(normalizePath("/finance/")).toBe("/finance");
    expect(normalizePath("finance")).toBe("/finance");
    expect(normalizePath("/finance?tab=1")).toBe("/finance");
    expect(normalizePath("/finance#summary")).toBe("/finance");
    expect(normalizePath("https://example.com")).toBe("https://example.com");
  });

  it("collects owned shell paths", () => {
    const owned = getOwnedShellPaths();

    expect(Array.isArray(owned)).toBe(true);
    expect(owned.length).toBeGreaterThan(0);
    expect(owned).toContain("/");
    expect(owned).toContain("/wizards");
  });

  it("collects dashboard registry paths", () => {
    const dashboardPaths = getDashboardRegistryPaths();
    expect(Array.isArray(dashboardPaths)).toBe(true);
  });

  it("collects wizard paths", () => {
    const wizardPaths = getWizardPaths();
    expect(Array.isArray(wizardPaths)).toBe(true);
    expect(wizardPaths).toContain("/onboarding");
    expect(wizardPaths).toContain("/reenrollment");
    expect(wizardPaths).toContain("/aid-setup");
    expect(wizardPaths).toContain("/enrollment-conversion");
    expect(wizardPaths).toContain("/enrollment-period-setup");
  });

  it("has no duplicate owned application paths across dashboard and wizard sources", () => {
    expect(getDuplicateOwnedPaths()).toEqual([]);
  });

  it("has no active sidebar links pointing to unowned routes", () => {
    expect(getUnownedNavLinks()).toEqual([]);
  });

  it("does not expose likely placeholder links as active nav entries", () => {
    expect(getLikelyPlaceholderNavLinks()).toEqual([]);
  });
});
