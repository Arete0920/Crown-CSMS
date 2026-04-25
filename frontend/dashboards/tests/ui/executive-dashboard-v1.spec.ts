import { test, expect } from "@playwright/test";

const BASE = process.env.VITE_DEV_BASE_URL || "http://localhost:4173";
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

test("School Administrator dashboard renders key workflow and metrics sections", async ({
  page,
}) => {
  await seedSession(page, "admin");

  // Mock the admin metrics API consumed by the Executive dashboard page.
  await page.route("**/api/v1/admin/metrics/**", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        enrolled: 412,
        attendance_rate: 96,
        operational_alerts: [{ label: "Grade 10 attendance dip", count: 2 }],
      }),
    })
  );

  await page.route("**/api/v1/nav/**", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        groups: [
          {
            title: "Leadership",
            items: [
              { label: "Home", href: "/" },
              { label: "Dashboard", href: "/dashboard" },
            ],
          },
        ],
      }),
    })
  );

  await page.goto(`${BASE}/admin`, { waitUntil: "domcontentloaded" });

  // Executive dashboard uses static page headings plus API-fed KPI cards.
  await expect(
    page.getByRole("heading", { name: /executive dashboard/i })
  ).toBeVisible();
  await expect(page.getByRole("heading", { name: /administration/i })).toBeVisible();

  // Stable section anchors in the current admin layout.
  await expect(page.locator("text=Leadership Action").first()).toBeVisible();
  await expect(page.locator("text=Executive Insights").first()).toBeVisible();

  // Deterministic KPI labels from the current admin metric cards.
  await expect(page.locator("text=Enrolled").first()).toBeVisible();
  await expect(page.locator("text=Attendance Flags").first()).toBeVisible();
  await expect(page.locator("text=Discipline").first()).toBeVisible();
  await expect(page.locator("text=Messages Pending").first()).toBeVisible();

  // Core cards in the current executive layout.
  await expect(page.locator("text=Academic Risk").first()).toBeVisible();
  await expect(page.locator("text=Enrollment Trend").first()).toBeVisible();
});
