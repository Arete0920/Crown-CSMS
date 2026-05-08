import { expect, test } from "@playwright/test";

const DEMO_SCHOOL_ID = "19801b59-8c05-4c84-9312-5d792e4e839d";

const SANDBOX_SCHOOL_NAMES = [
  "Heritage Christian Academy",
  "Harvest Christian School",
  "Faith Christian Academy",
  "Calvary Christian School",
  "St. Anne Christian Academy",
  "Grace Covenant School",
  "Providence Christian Academy",
  "Trinity Classical School",
  "Redeemer Christian School",
  "Cornerstone Christian Academy",
  "New Hope Christian School",
  "Legacy Christian Academy",
  "Emmanuel Christian School",
  "King's Way Christian Academy",
  "Bethel Christian School",
  "Veritas Christian Academy",
  "Crossroads Christian School",
  "Shepherd's Gate Academy",
  "Lighthouse Christian School",
  "Covenant Preparatory School",
];

function normalizeSchoolId(name: string, index: number): string {
  if (index === 0) return DEMO_SCHOOL_ID;
  return `sandbox-school-${name
    .toLowerCase()
    .replaceAll(/[^a-z0-9]+/g, "-")
    .replaceAll(/^-+|-+$/g, "")}`;
}

const SANDBOX_SCHOOLS = SANDBOX_SCHOOL_NAMES.map((name, index) => ({
  id: normalizeSchoolId(name, index),
  name,
}));

const SANDBOX_EMAIL = "admin@heritage.example.org";
const SANDBOX_PASSWORD = "demo-password";
const PREFERRED_ROLE = "school_admin";

test("canonical sandbox proof across all 20 sandbox schools", async ({ page }) => {
  test.setTimeout(120_000);

  await page.route("**/demo/schools_manifest.json", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ schools: SANDBOX_SCHOOLS }),
    });
  });

  await page.route("**/demo/heritage_demo_credentials.json", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        required_personas: [
          {
            key: "school_admin",
            email: "admin@heritage.example.org",
          },
        ],
      }),
    });
  });

  await page.route("**/api/v1/auth/token/", async (route) => {
    const selectedSchool = await page.inputValue("#login-school");
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        access: "sandbox-proof-access-token",
        school_id: selectedSchool,
      }),
    });
  });

  await page.goto("/login", { waitUntil: "domcontentloaded" });

  const schoolSelect = page.locator("#login-school");
  await expect(schoolSelect).toBeVisible();
  await expect(schoolSelect.locator("option")).toHaveCount(20);

  const optionData = await schoolSelect.locator("option").evaluateAll((options) =>
    options.map((option) => ({
      value: option.getAttribute("value") ?? "",
      label: (option.textContent ?? "").trim(),
    }))
  );

  const selectableOptions = optionData.filter((option) => option.value);

  expect(selectableOptions).toHaveLength(20);
  expect(selectableOptions.map((option) => option.value)).toEqual(
    SANDBOX_SCHOOLS.map((school) => school.id)
  );

  expect(selectableOptions.map((option) => option.label)).toEqual(
    SANDBOX_SCHOOLS.map((school) => school.name)
  );

  const roleSelect = page.locator("#login-role");
  const roleOptions = await roleSelect.locator("option").evaluateAll((options) =>
    options.map((option) => option.getAttribute("value") ?? "")
  );
  const roleValue = roleOptions.includes(PREFERRED_ROLE)
    ? PREFERRED_ROLE
    : roleOptions.find(Boolean) ?? "";

  for (const school of SANDBOX_SCHOOLS) {
    await schoolSelect.selectOption(school.id);
    if (roleValue) {
      await roleSelect.selectOption(roleValue);
    }

    await page.fill("#login-email", SANDBOX_EMAIL);
    await page.fill("#login-password", SANDBOX_PASSWORD);
    const navigationAfterSignIn = page
      .waitForURL((url) => !url.pathname.endsWith("/login"), { timeout: 15_000 })
      .catch(() => null);
    await page.locator("button.btn-signin").click();
    await navigationAfterSignIn;

    await expect
      .poll(async () =>
        page
          .evaluate(() => ({
            schoolId: sessionStorage.getItem("crown.school.id"),
            role: sessionStorage.getItem("crown.role"),
            access: sessionStorage.getItem("crown.jwt.access"),
          }))
          .catch(() => ({ schoolId: null, role: null, access: null }))
      )
      .toMatchObject({
        schoolId: school.id,
        role: expect.any(String),
        access: expect.any(String),
      });

    const storage = await page.evaluate(() => ({
      schoolId: sessionStorage.getItem("crown.school.id"),
      role: sessionStorage.getItem("crown.role"),
      access: sessionStorage.getItem("crown.jwt.access"),
    }));

    expect(storage.schoolId).toBe(school.id);
    expect(storage.role).toBeTruthy();
    expect(storage.access).toBeTruthy();
    await expect(page).not.toHaveURL(/\/login$/);

    await page.goto("/login", { waitUntil: "domcontentloaded" });
  }
});
