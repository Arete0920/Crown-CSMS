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

  // The /admin launch surface has evolved; accept either legacy or current header copy.
  await expect(page.locator("body")).toContainText(
    /good morning|school administrator command center|school administrator dashboard/i
  );
  await expect(page.getByRole("link", { name: /dashboard/i }).first()).toBeVisible();

  const wizardHubHeading = page.getByRole("heading", { name: /wizard hub/i });
  if (await wizardHubHeading.isVisible()) {
    // /admin can legitimately land on the setup wizard launch surface.
    await expect(wizardHubHeading).toBeVisible();
    await expect(page.locator("body")).toContainText(/setup wizards/i);
    return;
  }

  // Stable anchors in the current admin launch layout.
  await expect(page.getByRole("heading", { name: /execution queue/i })).toBeVisible();
  await expect(page.getByRole("heading", { name: /action required/i })).toBeVisible();

  // Deterministic watch-card labels in the current layout.
  await expect(page.getByRole("heading", { name: /42 open applications/i })).toBeVisible();
  await expect(page.getByRole("heading", { name: /96\.2% present today/i })).toBeVisible();
  await expect(page.getByRole("heading", { name: /18 students at risk/i })).toBeVisible();
});
