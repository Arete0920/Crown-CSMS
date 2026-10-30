import { describe, expect, it } from "vitest";
import { canExposeDevAidWizard, DEV_AID_PREVIEW_ORIGIN } from "./devAidPreviewAccess.js";

const route = { path: "/aid-setup", moduleType: "wizard", releaseState: "draft" };
const config = { flag: "1", sandboxMode: "1", demoMode: "sandbox", origin: DEV_AID_PREVIEW_ORIGIN };

describe("isolated DEV financial aid preview release gate", () => {
  it("allows only the explicit draft financial aid wizard in the pinned DEV preview", () => {
    expect(canExposeDevAidWizard(route, config)).toBe(true);
  });

  it("fails closed when opt-in is absent or any context differs", () => {
    for (const override of [
      { flag: undefined }, { flag: "0" }, { sandboxMode: "0" },
      { demoMode: "production" }, { origin: "https://yellow-forest-0eecc8b0f.7.azurestaticapps.net" },
      { origin: "https://untrusted.invalid" }, { origin: DEV_AID_PREVIEW_ORIGIN + ".invalid" },
    ]) {
      expect(canExposeDevAidWizard(route, { ...config, ...override })).toBe(false);
    }
  });

  it("does not expose unrelated draft wizards or change readiness classification", () => {
    for (const candidate of [
      { ...route, path: "/billing-setup" },
      { ...route, moduleType: "dashboard" },
      { ...route, releaseState: "ready" },
      { ...route, releaseState: "placeholder" },
      { ...route, releaseState: undefined },
    ]) {
      expect(canExposeDevAidWizard(candidate, config)).toBe(false);
    }
  });
});
