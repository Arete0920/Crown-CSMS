import { expect, test } from "@playwright/test";

// No fixtures are changed: this is a real operator click-path proof in a
// prepared, disposable local Heritage stack, never a hosted buyer run.
const FRONTEND = "http://127.0.0.1:4173";
const BACKEND = "http://127.0.0.1:8000";
const enabled = process.env.CROWN_LOCAL_PRESENTER_E2E === "1";

if (process.env.CROWN_REQUIRE_LOCAL_PRESENTER_PROOF === "1" && !enabled) {
  throw new Error("Local presenter evidence is required, not skipped.");
}

test.describe("Heritage physical-presenter browser navigation contract", () => {
  test.skip(!enabled, "Only the guarded local Heritage five-module rehearsal may run this suite.");
  test.use({ baseURL: FRONTEND });

  test("starts at real /sandbox; authenticates school admin and parent; opens actual live workflows", async ({ page, request }) => {
    test.setTimeout(180_000);
    expect(process.env.CROWN_EXPECTED_FRONTEND_SHA).toMatch(/^[0-9a-f]{40}$/);

    const source = await request.get(FRONTEND + "/build.json");
    expect(source.status()).toBe(200);
    expect((await source.json()).build_sha).toBe(process.env.CROWN_EXPECTED_FRONTEND_SHA);

    const catalog = await request.get(BACKEND + "/api/v1/sandbox/catalog/");
    expect(catalog.status()).toBe(200);
    expect((await catalog.json()).schools.map((school: { key: string }) => school.key)).toEqual(["heritage-core"]);

    await page.goto(FRONTEND + "/sandbox", { waitUntil: "domcontentloaded" });
    const adminCard = page.locator(".sandbox-persona-card").filter({ hasText: "School Administrator" }).first();
    await expect(adminCard).toBeVisible();
    await adminCard.getByRole("button", { name: "Start guided" }).click();
    await expect(page).toHaveURL(/\/sandbox\/command-center\?/);
    expect(await page.evaluate(() => sessionStorage.getItem("crown.role"))).toBe("school_admin");

    // The previous /sandbox route opened only an illustrative admin dashboard.
    await expect(page.getByRole("link", { name: /Open live Summer Camp setup/i })).toBeVisible();
    await expect(page.getByText(/Diadem Daycare staff release requires the separate signed/i)).toBeVisible();
    await expect(page.getByText(/Standalone Jireh SGO uses independently authenticated/i)).toBeVisible();

    const camp = page.waitForResponse((r) =>
      new URL(r.url()).pathname === "/api/v1/summer-camp/wizard/setup/" && r.request().method() === "GET"
    );
    await page.getByRole("link", { name: /Open live Summer Camp setup/i }).click();
    expect((await camp).status()).toBe(200);
    await expect(page).toHaveURL(/\/summer-camp-dashboard\/setup$/);

    await page.goBack();
    await expect(page).toHaveURL(/\/sandbox\/command-center\?/);
    const am = page.waitForResponse((r) => {
      const url = new URL(r.url());
      return url.pathname === "/api/v1/aftercare/roster/today/"
        && url.searchParams.get("care_session") === "AM"
        && r.request().method() === "GET";
    });
    await page.getByRole("link", { name: /Open Before Care \(AM\) roster/i }).click();
    expect((await am).status()).toBe(200);
    await expect(page).toHaveURL(/\/before-care\/roster$/);

    await page.goBack();
    await expect(page).toHaveURL(/\/sandbox\/command-center\?/);
    const pm = page.waitForResponse((r) => {
      const url = new URL(r.url());
      return url.pathname === "/api/v1/aftercare/roster/today/"
        && url.searchParams.get("care_session") === "PM"
        && r.request().method() === "GET";
    });
    await page.getByRole("link", { name: /Open Aftercare \(PM\) roster/i }).click();
    expect((await pm).status()).toBe(200);
    await expect(page).toHaveURL(/\/aftercare\/roster$/);

    await page.goBack();
    await expect(page).toHaveURL(/\/sandbox\/command-center\?/);
    await page.getByRole("link", { name: /Choose another authorized role/i }).click();
    await expect(page).toHaveURL(/\/sandbox$/);
    // Returning to the launcher has not manufactured a Parent token.
    expect(await page.evaluate(() => sessionStorage.getItem("crown.role"))).toBe("school_admin");

    const parentCard = page.locator(".sandbox-persona-card").filter({ hasText: "Parent / Guardian" });
    await parentCard.getByRole("button", { name: "Start guided" }).click();
    await expect(page).toHaveURL(/\/sandbox\/command-center\?/);
    expect(await page.evaluate(() => sessionStorage.getItem("crown.role"))).toBe("parent");
    const aidLink = page.getByRole("link", { name: /Prepare and save a fictional Jireh financial aid application/i });
    await expect(aidLink).toBeVisible();
    await aidLink.click();
    await expect(page).toHaveURL(/\/parent\/financial-aid$/);
    await expect(page.getByRole("heading", { name: "Family Financial Aid demonstration" })).toBeVisible();

    const readback = page.waitForResponse((r) =>
      new URL(r.url()).pathname === "/api/v1/aid/family/demo-intake/" && r.request().method() === "GET"
    );
    await page.getByRole("button", { name: "Refresh saved status" }).click();
    expect((await readback).status()).toBe(200);
  });
});
