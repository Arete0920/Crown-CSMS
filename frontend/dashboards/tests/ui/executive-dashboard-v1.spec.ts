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

  // Mock the school-admin summary API so this gate is deterministic and decoupled from backend state.
  await page.route("**/api/v1/dashboards/school-administrator/summary**", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        dashboard_key: "school-administrator",
        metrics: [
          { label: "Enrollment", value: "412" },
          { label: "Attendance Today", value: "96.4%" },
          { label: "Tuition Collected MTD", value: "$287,400" },
          { label: "Students At Risk", value: "18" },
        ],
        alerts: [
          { title: "Grade 10 attendance dip for second straight week", level: "High" },
        ],
        queue: ["Review board packet readiness by Friday"],
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

  // /admin redirects to the school-admin dashboard route.
  await expect(
    page.getByRole("heading", { name: /school administrator dashboard/i })
  ).toBeVisible();

  // Workflow panel is always present for the school-admin view.
  await expect(page.locator("text=Administrator Workflow Actions")).toBeVisible();

  // Deterministic metric labels from mocked summary payload.
  await expect(page.locator("text=Enrollment").first()).toBeVisible();
  await expect(page.locator("text=Attendance Today").first()).toBeVisible();
  await expect(page.locator("text=Tuition Collected MTD").first()).toBeVisible();
  await expect(page.locator("text=Students At Risk").first()).toBeVisible();

  // Card section titles in the new school-admin layout.
  await expect(page.locator("text=Administrator Priorities").first()).toBeVisible();
  await expect(page.locator("text=Operational Queue").first()).toBeVisible();
});
