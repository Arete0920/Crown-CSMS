import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// Browser presentation contract only: all records below are synthetic responses.
// This is NOT evidence of a working partner SGO backend, public intake or payments.
const SGO_ID = "11111111-1111-4111-8111-111111111111";
const membership = {
  organizations: [{ id: SGO_ID, name: "Fictional Partner Grantor", role: "VIEWER" }],
  funds_status: "NONCASH_ONLY",
};
const overview = {
  organization: { id: SGO_ID, name: "Fictional Partner Grantor" },
  role: "VIEWER",
  funds_status: "NONCASH_ONLY",
  status: "PILOT_SOURCE_ONLY",
  totals: { programs: 1, applications: 2, noncash_committed_cents: 5000 },
  programs: [{
    id: "22222222-2222-4222-8222-222222222222",
    name: "Fictional Grant Program",
    year: 2027,
    source: "PRIVATE",
    policy_version: "FICTIONAL_POLICY_V1",
    applications: 2,
    eligible: 1,
    unreviewed: 1,
    noncash_committed_cents: 5000,
  }],
};

for (const viewport of [{ width: 1366, height: 900 }, { width: 390, height: 844 }]) {
  test(`standalone Jireh SGO renders scoped synthetic evidence at ${viewport.width}px`, async ({ page }) => {
    const seen: { path: string; method: string; school: string | undefined; crownSchool: string | undefined }[] = [];
    const errors: string[] = [];
    page.on("pageerror", (err) => errors.push(err.message));
    await page.setViewportSize(viewport);
    await page.addInitScript(() => {
      sessionStorage.setItem("crown.jwt.access", "fictional-browser-token");
      // An unrelated school selector must NOT enter any standalone SGO request.
      sessionStorage.setItem("crown.school.id", "fictional-unrelated-school");
    });
    await page.route("**/api/v1/**", async (route) => {
      const request = route.request();
      const path = new URL(request.url()).pathname;
      const headers = request.headers();
      seen.push({
        path, method: request.method(),
        school: headers["x-school-id"], crownSchool: headers["x-crown-school-id"],
      });
      let payload: unknown;
      if (path === "/api/v1/jireh-sgo/organizations/") payload = membership;
      else if (path === `/api/v1/jireh-sgo/organizations/${SGO_ID}/overview/`) payload = overview;
      else return route.fulfill({ status: 403, contentType: "application/json", body: '{"detail":"Not permitted"}' });
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(payload) });
    });

    await page.goto("/jireh-sgo");
    await expect(page.getByRole("heading", { level: 1, name: "Jireh SGO" })).toBeVisible();
    await expect(page.getByText("Fictional Grant Program")).toBeVisible();
    await expect(page.getByText("Source-only pilot (not certified)")).toBeVisible();
    await expect(page.getByText("$50.00", { exact: true })).toHaveCount(2);
    await expect(page.locator(".crown-sidebar")).toHaveCount(0);
    await expect(page.locator(".crown-standalone-brand-mark")).toHaveCount(1);
    await expect(page.getByRole("img", { name: /CROWN.*Christian School Management Solution/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /toggle navigation/i })).toHaveCount(0);
    const programTable = page.getByRole("region", { name: "SGO programs" });
    await expect(programTable).toBeVisible();
    await expect(programTable).toHaveAttribute("tabindex", "0");

    expect(seen).toHaveLength(2);
    expect(seen.every((item) => item.method === "GET" &&
      item.path.startsWith("/api/v1/jireh-sgo/organizations/") &&
      !item.school && !item.crownSchool)).toBe(true);
    expect(errors).toEqual([]);

    // The program table may scroll inside its own named, focusable region.
    // The whole page must never develop horizontal viewport scrolling.
    const overflow = await page.evaluate(() =>
      document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(1);

    const a11y = await new AxeBuilder({ page })
      .include("main")
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(a11y.violations.filter((entry) =>
      entry.impact === "serious" || entry.impact === "critical")).toEqual([]);
  });
}

test("standalone SGO fails closed with no authenticated member session", async ({ page }) => {
  const requests: string[] = [];
  await page.route("**/api/v1/**", async (route) => {
    requests.push(new URL(route.request().url()).pathname);
    await route.fulfill({ status: 403, contentType: "application/json", body: '{"detail":"Not permitted"}' });
  });
  await page.goto("/jireh-sgo");
  await expect(page.getByRole("alert")).toContainText("Authorized SGO sign-in is required");
  await expect(page.getByText("Fictional Grant Program")).toHaveCount(0);
  expect(requests).toEqual([]);
});

test("standalone SGO does not convert denied membership into an empty success", async ({ page }) => {
  await page.addInitScript(() => {
    sessionStorage.setItem("crown.jwt.access", "fictional-browser-token");
  });
  await page.route("**/api/v1/**", async (route) => {
    await route.fulfill({ status: 403, contentType: "application/json", body: '{"detail":"Denied"}' });
  });
  await page.goto("/jireh-sgo");
  await expect(page.getByRole("alert")).toContainText("SGO membership could not be verified.");
  await expect(page.getByText("Fictional Grant Program")).toHaveCount(0);
  await expect(page.getByRole("region", { name: "SGO programs" })).toHaveCount(0);
});
