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

test("Student Dashboard v2 renders KPI cards and Upcoming Assignments section", async ({
  page,
}) => {
  await seedSession(page, "student");

  // Mock the student overview API so the test is independent of any backend or demo fallback.
  await page.route("**/api/student360/me/overview/**", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        student: { name: "Test Student", grade: "10" },
        dashboard_v2: {
          gpa: 3.5,
          current_average: 91.2,
          missing_assignments: 1,
          service_hours: { approved_hours: 12.0, pending_hours: 1.5 },
          financial: { balance_cents: 25000 },
          alerts: [],
          upcoming_assignments: [],
        },
      }),
    })
  );

  await page.goto(`${BASE}/student`, { waitUntil: "domcontentloaded" });

  // Title exists
  await expect(
    page.getByRole("heading", { name: /student dashboard/i })
  ).toBeVisible();

  // KPI labels
  await expect(page.getByText(/My GPA|GPA \(est\.\)/).first()).toBeVisible();
  await expect(page.getByText(/^Current Average$/).first()).toBeVisible();
  await expect(page.getByText(/^Missing Work$/).first()).toBeVisible();
  await expect(page.getByText(/^Balance Due$/).first()).toBeVisible();

  // Assignments section header
  await expect(page.locator("text=Upcoming Assignments").first()).toBeVisible();  // card title + empty-state both contain "upcoming assignments"

  // Service Hours card
  await expect(page.locator("text=Service Hours")).toBeVisible();

  // Quick links still present
  await expect(page.getByRole("link", { name: "Gradebook", exact: true })).toBeVisible();
});
