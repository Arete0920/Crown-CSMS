/**
 * Wizard Discovery Contract Test — Crown2026
 * =============================================
 * Validates that the backend wizard registry and the frontend manifest stay in sync.
 *
 * This test is the drift-prevention gate:
 *   - Backend adds a wizard but frontend doesn't update wizard-manifest.js → FAIL (Step 4)
 *   - Frontend adds a wizard to wizard-manifest.js but backend doesn't register it → FAIL (Step 5)
 *
 * Requires a running Django backend (CROWN_TEST_API_BASE, default: http://127.0.0.1:8000).
 * Auth: acquires a JWT via POST /api/v1/auth/token/ before calling the discovery endpoint.
 *
 * Run:
 *   npm run test:e2e -- tests/api/wizard-contract.spec.ts
 */

import { test, expect } from "@playwright/test";
import { WIZARD_SLUGS } from "../../src/routes/wizard-manifest.js";

const TEST_USER     = process.env.CROWN_TEST_USER     ?? "teacher";
const TEST_PASS     = process.env.CROWN_TEST_PASS    ;
const TEST_API_BASE = process.env.CROWN_TEST_API_BASE ?? "http://127.0.0.1:8000";

test.describe("Wizard Discovery API alignment", () => {
  let authToken: string;

  test.beforeAll(async ({ request }) => {
  if (!TEST_PASS?.trim()) throw new Error("Configure CROWN_TEST_PASS before running this proof.");
    const loginResp = await request.post(`${TEST_API_BASE}/api/v1/auth/token/`, {
      data: { username: TEST_USER, password: TEST_PASS },
    });
    expect(loginResp.status(), "Auth token request should return 200").toBe(200);
    const body = await loginResp.json();
    authToken = body?.access ?? body?.token;
    expect(authToken, "JWT token not found in login response").toBeTruthy();
  });

  test("Step 1: endpoint exists and requires auth (401 when unauthenticated)", async ({ request }) => {
    const resp = await request.get(`${TEST_API_BASE}/api/v1/wizards/`);
    expect(resp.status()).toBe(401);
  });

  test("Step 2: authenticated request returns 200", async ({ request }) => {
    const resp = await request.get(`${TEST_API_BASE}/api/v1/wizards/`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(resp.status()).toBe(200);
  });

  test("Step 3: response has correct shape", async ({ request }) => {
    const resp = await request.get(`${TEST_API_BASE}/api/v1/wizards/`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const data = await resp.json();
    expect(data).toHaveProperty("wizards");
    expect(Array.isArray(data.wizards)).toBe(true);
    expect(data.wizards.length).toBeGreaterThan(0);
    for (const w of data.wizards) {
      expect(typeof w.key).toBe("string");
      expect(typeof w.slug).toBe("string");
      expect(typeof w.title).toBe("string");
      expect(typeof w.enabled).toBe("boolean");
      expect(w.slug.length).toBeGreaterThan(0);
    }
  });

  test("Step 4: all enabled backend slugs are in the frontend manifest (backend → frontend check)", async ({ request }) => {
    const resp = await request.get(`${TEST_API_BASE}/api/v1/wizards/`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const data = await resp.json();
    const backendSlugs: string[] = data.wizards
      .filter((w: { enabled: boolean }) => w.enabled)
      .map((w: { slug: string }) => w.slug);

    const missing = backendSlugs.filter((s) => !WIZARD_SLUGS.includes(s));
    expect(missing, `Backend wizards missing from frontend wizard-manifest.js: ${missing.join(", ")}`).toHaveLength(0);
  });

  test("Step 5: all frontend manifest slugs are in the backend response (frontend → backend check)", async ({ request }) => {
    const resp = await request.get(`${TEST_API_BASE}/api/v1/wizards/`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const data = await resp.json();
    const backendSlugs: string[] = data.wizards.map((w: { slug: string }) => w.slug);

    const missing = WIZARD_SLUGS.filter((s) => !backendSlugs.includes(s));
    expect(missing, `Frontend manifest slugs missing from backend registry: ${missing.join(", ")}`).toHaveLength(0);
  });

  test("Step 6: slugs are unique (no double-registration on either side)", async ({ request }) => {
    const resp = await request.get(`${TEST_API_BASE}/api/v1/wizards/`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const data = await resp.json();
    const backendSlugs: string[] = data.wizards.map((w: { slug: string }) => w.slug);

    expect(new Set(backendSlugs).size, "Duplicate slugs in backend response").toBe(backendSlugs.length);
    expect(new Set(WIZARD_SLUGS).size, "Duplicate slugs in frontend manifest").toBe(WIZARD_SLUGS.length);
  });
});
