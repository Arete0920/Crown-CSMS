import { expect, test } from "@playwright/test";

const PERSONA_ROUTES = [
  { role: "school_admin", label: "Program Director", route: "/school-admin-dashboard" },
  { role: "teacher", label: "Teacher / Staff", route: "/teacher" },
  { role: "parent", label: "Parent / Guardian", route: "/parent" },
  { role: "student", label: "Student / Camper", route: "/student" },
];
const SANDBOX_SCHOOL_ID = "19801b59-8c05-4c84-9312-5d792e4e839d";

test("open sandbox launches roles without credential fields", async ({ page }, testInfo) => {
  test.setTimeout(90_000);

  const consoleErrors: string[] = [];
  const requestFailures: string[] = [];
  const launchedRoutes: string[] = [];

  page.on("console", (message) => {
    if (message.type() === "error") {
      consoleErrors.push(message.text());
    }
  });

  page.on("requestfailed", (request) => {
    const failure = request.failure()?.errorText || "failed";
    requestFailures.push(`${request.method()} ${request.url()} ${failure}`);
  });

  await page.addInitScript(() => {
    try {
      Object.defineProperty(navigator, "sendBeacon", {
        configurable: true,
        value: () => true,
      });
    } catch {
      // ignore
    }
  });

  await page.route("**/api/v1/sandbox/session/", async (route) => {
    const payload = route.request().postDataJSON() as { role?: string; school?: string; guidance?: string; tour?: string };
    const role = payload.role || "school_admin";
    const mapping = PERSONA_ROUTES.find((persona) => persona.role === role) || PERSONA_ROUTES[0];
    launchedRoutes.push(mapping.route);

    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({
        access: `sandbox-${role}-access-token`,
        refresh: "",
        school_id: SANDBOX_SCHOOL_ID,
        school_name: "Heritage Christian Academy",
        role,
        guidance: payload.guidance || "guided",
        tour: payload.tour || "",
        route: mapping.route,
        command_center: { route: "/sandbox/command-center" },
      }),
    });
  });

  await page.route("**/api/v1/sandbox/events/", async (route) => {
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({ ok: true, event_id: "sandbox-event-1" }),
    });
  });

  await page.route("**/api/v1/nav/", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        groups: [
          {
            title: "Navigation",
            items: [
              { label: "Administration", href: "/admin" },
              { label: "School Board", href: "/board" },
              { label: "Finance", href: "/finance" },
              { label: "Parent", href: "/parent" },
              { label: "Student", href: "/student" },
            ],
          },
        ],
      }),
    });
  });

  await page.route("**/api/v1/**", async (route) => {
    const url = route.request().url();
    if (
      url.includes("/api/v1/sandbox/session/") ||
      url.includes("/api/v1/sandbox/events/") ||
      url.includes("/api/v1/nav/")
    ) {
      await route.fallback();
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ ok: true }),
    });
  });

  await page.route("**fonts.googleapis.com/**", async (route) => {
    await route.fulfill({ status: 200, contentType: "text/css", body: "" });
  });

  await page.route("**fonts.gstatic.com/**", async (route) => {
    await route.fulfill({ status: 200, contentType: "font/woff2", body: "" });
  });

  await page.goto("/sandbox", { waitUntil: "domcontentloaded" });

  await expect(page.getByLabel("CROWN sandbox overview").getByRole("heading", { name: "Guided Proof Sandbox" })).toBeVisible();
  await expect(page.getByText("One-click role launch")).toBeVisible();
  await expect(page.getByText("No buyer passwords")).toBeVisible();
  await expect(page.getByText("Demo data only", { exact: true })).toBeVisible();
  await expect(page.locator("input, select, textarea")).toHaveCount(0);

  for (const persona of PERSONA_ROUTES) {
    await expect(page.getByText(persona.label, { exact: true })).toBeVisible();
  }

  for (const persona of PERSONA_ROUTES) {
    await page.goto("/sandbox", { waitUntil: "domcontentloaded" });

    await expect(page.getByLabel("CROWN sandbox overview").getByRole("heading", { name: "Guided Proof Sandbox" })).toBeVisible();
    await page.locator(".persona-card", { hasText: persona.label }).getByRole("button").click();

    await expect(page).toHaveURL(new RegExp(`${persona.route.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}$`));
    await expect
      .poll(async () =>
        page.evaluate(() => ({
          access: sessionStorage.getItem("crown.jwt.access"),
          schoolId: sessionStorage.getItem("crown.school.id"),
          role: sessionStorage.getItem("crown.role"),
        }))
      )
      .toMatchObject({
        access: expect.stringContaining(`sandbox-${persona.role}-access-token`),
        schoolId: SANDBOX_SCHOOL_ID,
        role: persona.role,
      });

    await page.waitForLoadState("networkidle");

    await page.screenshot({ path: testInfo.outputPath(`sandbox-${persona.role}.png`), fullPage: true });
  }

  expect(launchedRoutes).toEqual(PERSONA_ROUTES.map((persona) => persona.route).flatMap((route) => [route]));
  const unexpectedRequestFailures = requestFailures.filter(
    (failure) => !failure.includes("/api/v1/sandbox/events/")
  );
  const unexpectedConsoleErrors = consoleErrors.filter(
    (error) => !/Encountered two children with the same key/i.test(error)
  );

  expect(unexpectedRequestFailures, "browser request failures").toEqual([]);
  expect(unexpectedConsoleErrors, "browser console errors").toEqual([]);
});
