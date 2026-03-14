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

test("Executive Dashboard renders admin KPI cards and Executive Insights section", async ({
  page,
}) => {
  await seedSession(page, "admin");

  // Mock the admin metrics API so the test is independent of any backend or demo fallback.
  await page.route("**/api/v1/admin/metrics/**", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        enrolled: 320,
        attendance_flags_today: 5,
        discipline_incidents_week: 2,
        messages_pending: 8,
        billing_delinquencies: 3,
        enrollment_funnel: { inquiries: 50, applicants: 30, admitted: 25, enrolled: 20 },
        operational_alerts: [],
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

  // Page title from CrownLayout
  await expect(
    page.getByRole("heading", { name: /administration/i })
  ).toBeVisible();

  // Operational KPI cards (rendered from API mock — deterministic)
  // .first() required: each label also appears in the "Today at a Glance" table row (case-insensitive substring match)
  await expect(page.locator("text=Enrolled").first()).toBeVisible();  // KPI card + FunnelStep both render "Enrolled"
  await expect(page.locator("text=Attendance Flags").first()).toBeVisible();
  await expect(page.locator("text=Discipline").first()).toBeVisible();
  await expect(page.locator("text=Messages Pending").first()).toBeVisible();

  // Enrollment funnel section
  await expect(page.locator("text=Enrollment Funnel")).toBeVisible();

  // Executive Insights card title (added in this slice)
  // .first() required: ErrorBanner title also contains "Executive insights" as a substring (case-insensitive match)
  await expect(page.locator("text=Executive Insights").first()).toBeVisible();

  // ExecMetric labels (always rendered regardless of API availability)
  await expect(page.locator("text=Receivables")).toBeVisible();
  await expect(page.locator("text=Aid Allocated")).toBeVisible();
  await expect(page.locator("text=Academic Risk")).toBeVisible();
  await expect(page.locator("text=Overdue Work")).toBeVisible();
});
