import { test, expect } from "@playwright/test";

const BASE = process.env.VITE_DEV_BASE_URL || "http://localhost:3000";
const DEMO_SCHOOL_ID = process.env.CROWN_DEMO_SCHOOL_ID || "19801b59-8c05-4c84-9312-5d792e4e839d";
const DEMO_TOKEN = process.env.CROWN_DEMO_TOKEN || "playwright-demo-token";

async function seedDemoSession(page, role: string) {
  await page.addInitScript(({ role, token, schoolId }) => {
    sessionStorage.setItem("crown.jwt.access", token);
    sessionStorage.setItem("crown.role", role);
    sessionStorage.setItem("crown.school.id", schoolId);
    localStorage.setItem("crown.jwt.access", token);
    localStorage.setItem("crown.role", role);
    localStorage.setItem("crown.school.id", schoolId);
    localStorage.setItem("crown.demo.role", role);
  }, { role, token: DEMO_TOKEN, schoolId: DEMO_SCHOOL_ID });
}

const CASES = [
  { role: "parent", expectPath: "/parent" },
  { role: "student", expectPath: "/student" },
  { role: "teacher", expectPath: "/teacher" },
];

test.describe("Home route role redirect", () => {
  for (const c of CASES) {
    test(`"/" redirects for role=${c.role}`, async ({ page }) => {
      await seedDemoSession(page, c.role);
      await page.goto(BASE + "/", { waitUntil: "networkidle" });
      await page.waitForTimeout(250);
      await expect(page).toHaveURL(new RegExp(`${c.expectPath.replace("/", "\\/")}$`));
    });
  }
});
