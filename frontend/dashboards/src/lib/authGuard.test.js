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

describe("auth guard security boundary", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.stubGlobal("sessionStorage", memoryStorage({
      "crown.jwt.access": "browser-controlled-token",
      "crown.role": "school_admin",
      "crown.school.id": "school-123",
    }));
    vi.stubGlobal("localStorage", memoryStorage());
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("does not trust browser storage as authentication in a production build", async () => {
    vi.stubEnv("VITE_DEMO_MODE", "");
    vi.stubEnv("VITE_SANDBOX_MODE", "");
    vi.stubEnv("VITE_WIZARD_CERTIFICATION", "");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Unauthorized" }), {
        status: 401,
        headers: { "content-type": "application/json" },
      }),
    );
    const navigate = vi.fn();

    const { requireAuth } = await import("./authGuard.js");
    await expect(requireAuth(navigate)).resolves.toBeNull();

    expect(fetchMock).toHaveBeenCalledWith("/auth/me/", expect.objectContaining({
      credentials: "include",
    }));
    expect(navigate).toHaveBeenCalledWith("/login");
  });

  it("permits the synthetic browser session only in explicit sandbox mode", async () => {
    vi.stubEnv("VITE_DEMO_MODE", "sandbox");
    const fetchMock = vi.spyOn(globalThis, "fetch");

    const { requireAuth } = await import("./authGuard.js");
    await expect(requireAuth(vi.fn())).resolves.toMatchObject({
      role: "school_admin",
      school_id: "school-123",
    });

    expect(fetchMock).not.toHaveBeenCalled();
  });
});
