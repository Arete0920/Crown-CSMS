import { test, expect } from "@playwright/test";

/**
 * Demo-seeded persona route audit.
 * No manual credentials are required for this sandbox proof path.
 */

const UI = process.env.CROWN_UI_BASE || "http://127.0.0.1:4173";
const API = process.env.CROWN_API_BASE || "http://127.0.0.1:8000";
const SCHOOL_ID = process.env.CROWN_SCHOOL_ID || "19801b59-8c05-4c84-9312-5d792e4e839d";
const DEMO_SEED_USER = process.env.CROWN_DEMO_USER || "admin";
const DEMO_SEED_PASS = process.env.CROWN_DEMO_PASS || "Crown2026!";

type Persona = { seedRole: string; label: string; homePath: string; allowedFinalPaths: string[]; headingPattern: RegExp };

const personas: Persona[] = [
  { seedRole: "school_admin", label: "admin_school_admin", homePath: "/school-admin-dashboard", allowedFinalPaths: ["/school-admin-dashboard", "/wizards"], headingPattern: /School Admin|School Administrator|Administration|Overview|Wizards|Wizard Hub/i },
  { seedRole: "teacher", label: "teacher", homePath: "/dash/teacher", allowedFinalPaths: ["/dash/teacher"], headingPattern: /Teacher/i },
  { seedRole: "parent", label: "parent", homePath: "/dash/parent", allowedFinalPaths: ["/dash/parent"], headingPattern: /Parent/i },
  { seedRole: "student", label: "student", homePath: "/dash/student", allowedFinalPaths: ["/dash/student"], headingPattern: /Student/i },
  { seedRole: "finance", label: "finance", homePath: "/dash/finance", allowedFinalPaths: ["/dash/finance"], headingPattern: /Finance|Financial/i },
  { seedRole: "registrar", label: "registrar", homePath: "/dash/registrar", allowedFinalPaths: ["/dash/registrar"], headingPattern: /Registrar|Enrollment/i },
];

const blockedTextPattern = /\b401\b|\b403\b|\b404\b|unauthorized|not\s+found|restricted\s+access|not\s+authorized|application\s+error/i;
const blockedConsolePattern = /\b401\b|\b403\b|\b404\b|unauthorized|restricted\s+access|not\s+authorized|application\s+error/i;

async function acquireDemoToken(request: any): Promise<string> {
  const resp = await request.post(`${API}/api/v1/auth/token/`, {
    data: { username: DEMO_SEED_USER, password: DEMO_SEED_PASS },
  });
  expect(resp.status(), "demo token endpoint status").toBe(200);
  const data = await resp.json();
  expect(data?.access, "demo token missing access").toBeTruthy();
  return data.access as string;
}

async function seedDemoSession(page: any, role: string, token: string) {
  await page.addInitScript(([seedRole, sid, token]: [string, string, string]) => {
    sessionStorage.setItem("crown.jwt.access", token);
    sessionStorage.setItem("crown.role", seedRole);
    sessionStorage.setItem("crown.school.id", sid);

    localStorage.setItem("crown.jwt.access", token);
    localStorage.setItem("crown.role", seedRole);
    localStorage.setItem("crown.school.id", sid);
    localStorage.setItem("crown.demo.role", seedRole);
  }, [role, SCHOOL_ID, token]);
}

test.describe("Crown demo-seeded persona audit", () => {
  test("env sanity", async () => {
    expect(UI, "CROWN_UI_BASE missing").toBeTruthy();
  });

  for (const persona of personas) {
    test(`${persona.label}: demo-seeded route loads with no restricted/error text`, async ({ page, request }) => {
      const pageErrors: string[] = [];
      const consoleErrors: string[] = [];
      const blockedResponses: string[] = [];

      page.on("pageerror", (err: Error) => pageErrors.push(String(err)));
      page.on("console", (msg: any) => {
        if (msg.type() === "error") {
          consoleErrors.push(msg.text());
        }
      });

      page.on("response", (resp: any) => {
        const status = resp.status();
        const url = resp.url();
        if (status === 403 || status === 404) {
          blockedResponses.push(`${status} ${url}`);
        }
      });

      const token = await acquireDemoToken(request);
      await seedDemoSession(page, persona.seedRole, token);
      await page.goto(`${UI}${persona.homePath}`, { waitUntil: "networkidle" });

      const url = new URL(page.url());
      expect(persona.allowedFinalPaths.includes(url.pathname), `final route for ${persona.label}: ${url.pathname}`).toBe(true);

      await expect(page.locator("main")).toBeVisible({ timeout: 15000 });
      await expect(page.locator("[data-testid='dashboard-grid'], [data-testid='crown-nav'], nav").first()).toBeVisible({ timeout: 15000 });

      const bodyText = (await page.locator("body").innerText()).toLowerCase();
      expect(bodyText, `blocked error text found for ${persona.label}`).not.toMatch(blockedTextPattern);

      const headings = page.getByRole("heading");
      await expect(headings.filter({ hasText: persona.headingPattern }).first()).toBeVisible({ timeout: 15000 });

      const severeConsoleErrors = consoleErrors.filter((msg) => blockedConsolePattern.test(msg.toLowerCase()));

      expect(pageErrors, `pageerror(s) for ${persona.label}`).toEqual([]);
      expect(severeConsoleErrors, `blocked console errors for ${persona.label}`).toEqual([]);
      expect(blockedResponses, `403/404 responses for ${persona.label}`).toEqual([]);
    });
  }
});
