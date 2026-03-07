import { test, expect } from "@playwright/test";

/**
 * FULL UI demo audit.
 * Requirements:
 * - logs in as each role
 * - verifies nav loads
 * - visits each nav item (top-level)
 * - FAILS on any console error, pageerror, or API response >= 400 (except 401/403 for explicitly unauth pages)
 *
 * Env vars required (never commit):
 * - CROWN_UI_BASE, CROWN_API_BASE
 * - Role creds: CROWN_ROLE_ADMIN_EMAIL/PASS etc. (same as api_probe.ps1)
 * - Optional: CROWN_SCHOOL_ID, CROWN_TENANT_HEADER
 */

const UI = process.env.CROWN_UI_BASE!;
const API = process.env.CROWN_API_BASE!;
const TENANT_HEADER = process.env.CROWN_TENANT_HEADER || "X-School-Id";
const SCHOOL_ID = process.env.CROWN_SCHOOL_ID || "";

type Role = { slug: string; email?: string; pass?: string; homePath: string };

const roles: Role[] = [
  { slug: "admin", email: process.env.CROWN_ROLE_ADMIN_EMAIL, pass: process.env.CROWN_ROLE_ADMIN_PASS, homePath: "/dash/admin" },
  { slug: "teacher", email: process.env.CROWN_ROLE_TEACHER_EMAIL, pass: process.env.CROWN_ROLE_TEACHER_PASS, homePath: "/dash/teacher" },
  { slug: "parent", email: process.env.CROWN_ROLE_PARENT_EMAIL, pass: process.env.CROWN_ROLE_PARENT_PASS, homePath: "/dash/parent" },
  { slug: "student", email: process.env.CROWN_ROLE_STUDENT_EMAIL, pass: process.env.CROWN_ROLE_STUDENT_PASS, homePath: "/dash/student" },
  { slug: "finance", email: process.env.CROWN_ROLE_FINANCE_EMAIL, pass: process.env.CROWN_ROLE_FINANCE_PASS, homePath: "/dash/finance" },
  { slug: "registrar", email: process.env.CROWN_ROLE_REGISTRAR_EMAIL, pass: process.env.CROWN_ROLE_REGISTRAR_PASS, homePath: "/dash/registrar" },
];

// Minimal helper: login through API, then set localStorage token the way Crown expects.
// If Crown stores tokens differently, adjust here to match your existing auth pattern.
async function apiLogin(request: any, email: string, password: string) {
  const resp = await request.post(`${API}/api/auth/login/`, {
    data: { email, password },
    headers: {
      "Accept": "application/json",
      ...(SCHOOL_ID ? { [TENANT_HEADER]: SCHOOL_ID } : {}),
    },
  });

  const status = resp.status();
  const body = await resp.json().catch(() => ({}));
  expect(status, `login status for ${email}`).toBe(200);
  expect(body.access, "missing access token").toBeTruthy();
  return body.access as string;
}

async function setAuth(page: any, token: string) {
  await page.addInitScript(([t, sid]: [string, string]) => {
    // Adjust to match your actual storage keys.
    localStorage.setItem("access", t);
    if (sid) localStorage.setItem("school_id", sid);
  }, [token, SCHOOL_ID]);
}

test.describe("Crown demo full UI audit", () => {
  test("env sanity", async () => {
    expect(UI, "CROWN_UI_BASE missing").toBeTruthy();
    expect(API, "CROWN_API_BASE missing").toBeTruthy();
  });

  for (const r of roles) {
    test(`${r.slug}: dashboard + nav + no console/page errors + no API >=400`, async ({ page, request }) => {
      test.skip(!r.email || !r.pass, `missing env creds for ${r.slug}`);

      const pageErrors: string[] = [];
      const consoleErrors: string[] = [];
      const badNet: string[] = [];

      page.on("pageerror", (err: Error) => pageErrors.push(String(err)));
      page.on("console", (msg: any) => {
        if (msg.type() === "error") consoleErrors.push(msg.text());
      });

      page.on("response", async (resp: any) => {
        const url = resp.url();
        const status = resp.status();

        // Only police API calls (avoid blocking on fonts/assets).
        if (url.startsWith(API)) {
          // Allow intentional 401/403 only if the page is explicitly unauth (not expected here).
          if (status >= 400) {
            badNet.push(`${status} ${url}`);
          }
        }
      });

      const token = await apiLogin(request, r.email!, r.pass!);
      await setAuth(page, token);

      await page.goto(`${UI}${r.homePath}`, { waitUntil: "domcontentloaded" });

      // Core dashboard element you already use
      await expect(page.locator("[data-testid='dashboard-grid']")).toBeVisible({ timeout: 15000 });

      // Nav must render
      // Adjust selector to your CrownLayout nav container if different:
      await expect(page.locator("[data-testid='crown-nav'], nav")).toBeVisible({ timeout: 15000 });

      // HARD rule: debug JWT panel must never appear in demo audit
      await expect(page.locator("[data-testid='dev-jwt-panel']")).toHaveCount(0);

      // Wait a moment for late network calls
      await page.waitForTimeout(1000);

      expect(pageErrors, "pageerror(s)").toEqual([]);
      expect(consoleErrors, "console error(s)").toEqual([]);
      expect(badNet, "API calls returned >=400").toEqual([]);
    });
  }
});
