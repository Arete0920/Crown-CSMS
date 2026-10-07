import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

function memoryStorage(initial = {}) {
  const values = new Map(Object.entries(initial));
  return {
    getItem: vi.fn((key) => values.get(key) ?? null),
    setItem: vi.fn((key, value) => values.set(key, String(value))),
    removeItem: vi.fn((key) => values.delete(key)),
    clear: vi.fn(() => values.clear()),
  };
}

describe("roleAdapter security boundary", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.stubGlobal("sessionStorage", memoryStorage());
    vi.stubGlobal("localStorage", memoryStorage({
      "crown.role": "head_of_school",
      "crown.active.role": "head_of_school",
      "crown_user_roles": JSON.stringify(["head_of_school"]),
    }));
    globalThis.__CROWN_USER_ROLES__ = ["head_of_school"];
  });

  afterEach(() => {
    delete globalThis.__CROWN_USER_ROLES__;
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("ignores persistent and injected role claims in production", async () => {
    vi.stubEnv("VITE_DEMO_MODE", "production");
    vi.stubEnv("VITE_SANDBOX_MODE", "0");
    vi.stubEnv("VITE_WIZARD_CERTIFICATION", "0");

    const { getCurrentUserRoles } = await import("./roleAdapter.js");
    expect(getCurrentUserRoles()).toEqual([]);
  });

  it("allows deterministic injected role claims only in explicit sandbox mode", async () => {
    vi.stubEnv("VITE_DEMO_MODE", "sandbox");

    const { getCurrentUserRoles } = await import("./roleAdapter.js");
    expect(getCurrentUserRoles()).toContain("head_of_school");
  });
});
