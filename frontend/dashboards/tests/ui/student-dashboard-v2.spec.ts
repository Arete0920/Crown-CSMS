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

test("Student Dashboard v2 renders KPI cards and Upcoming Assignments section", async ({
  page,
}) => {
  await seedSession(page, "student");
  await page.goto(`${BASE}/student`, { waitUntil: "domcontentloaded" });

  // Title exists
  await expect(
    page.getByRole("heading", { name: /student dashboard/i })
  ).toBeVisible();

  // KPI labels
  await expect(page.locator("text=GPA")).toBeVisible();
  await expect(page.locator("text=Current Average")).toBeVisible();
  await expect(page.locator("text=Missing Work")).toBeVisible();
  await expect(page.locator("text=Balance Due")).toBeVisible();

  // Assignments section header
  await expect(page.locator("text=Upcoming Assignments").first()).toBeVisible();  // card title + empty-state both contain "upcoming assignments"

  // Service Hours card
  await expect(page.locator("text=Service Hours")).toBeVisible();

  // Quick links still present
  await expect(page.locator("a[href='/gradebook']")).toBeVisible();
});
