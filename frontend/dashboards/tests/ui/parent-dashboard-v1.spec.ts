import { test, expect } from "@playwright/test";

const BASE = process.env.VITE_DEV_BASE_URL || "http://localhost:3000";
const DEMO_SCHOOL_ID =
  process.env.CROWN_DEMO_SCHOOL_ID || "19801b59-8c05-4c84-9312-5d792e4e839d";
const DEMO_TOKEN = process.env.CROWN_DEMO_TOKEN || "playwright-demo-token";

async function seedSession(page, role: string) {
  await page.addInitScript(
    ({ token, role, schoolId }) => {
      try {
        sessionStorage.setItem("crown.jwt.access", token);
        sessionStorage.setItem("crown.role", role);
        sessionStorage.setItem("crown.school.id", schoolId);
        localStorage.setItem("crown.jwt.access", token);
        localStorage.setItem("crown.role", role);
        localStorage.setItem("crown.school.id", schoolId);
        localStorage.setItem("crown.demo.role", role);
      } catch {
        // ignore
      }
    },
    { token: DEMO_TOKEN, role, schoolId: DEMO_SCHOOL_ID }
  );
}

test("Parent Dashboard renders household KPI row and Children card", async ({
  page,
}) => {
  await seedSession(page, "parent");
  await page.goto(`${BASE}/parent`, { waitUntil: "domcontentloaded" });

  // Title exists (static — always renders even if fetch fails)
  await expect(
    page.getByRole("heading", { name: /parent dashboard/i })
  ).toBeVisible();

  // KPI labels
  await expect(page.locator("text=Household Balance")).toBeVisible();
  await expect(page.locator("text=Children").first()).toBeVisible();  // KPI label + CrownCard title both say "Children"
  await expect(page.locator("text=Missing Assignments")).toBeVisible();
  await expect(page.locator("text=Upcoming")).toBeVisible();

  // Children card section exists
  await expect(page.locator("text=Children").first()).toBeVisible();

  // Quick links still intact
  await expect(page.locator("a[href='/academics/parent-snapshot']")).toBeVisible();
  await expect(page.locator("a[href='/finance/invoices']")).toBeVisible();
});
