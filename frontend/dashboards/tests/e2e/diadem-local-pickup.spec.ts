import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";
import { enterPresenter, verifyPresenter } from "../../scripts/heritage-daycare-presenter.mjs";

const manifestPath = process.env.CROWN_DIADEM_PICKUP_MANIFEST || "";
const required = process.env.CROWN_REQUIRE_DIADEM_PICKUP_PROOF === "1";
// Exercise the presenter entry in visible Chromium on the Windows rehearsal.
test.use({ headless: process.platform !== "win32" });
if (required && !manifestPath) {
  throw new Error("Diadem live-browser proof requires a local fictional scenario manifest.");
}

type Case = { attendance_id: string; authority_id: string; child_name: string };
type Scenario = {
  fictional_only: true;
  source_sha: string;
  school_id: string;
  site_id: string;
  room_id: string;
  guardian_name: string;
  staff_access: string;
  unprivileged_access: string;
  cases: { approved: Case; revoked: Case; expired: Case };
};

function loadScenario(): Scenario {
  const scenario = JSON.parse(readFileSync(manifestPath, "utf8")) as Scenario;
  expect(scenario.fictional_only).toBe(true);
  expect(scenario.source_sha).toBe(process.env.CROWN_EXPECTED_FRONTEND_SHA);
  expect(scenario.staff_access).toBeTruthy();
  expect(scenario.unprivileged_access).toBeTruthy();
  return scenario;
}

async function staffSession(page: import("@playwright/test").Page, scenario: Scenario) {
  await page.addInitScript(({ token, school }) => {
    sessionStorage.setItem("crown.jwt.access", token);
    sessionStorage.setItem("crown.school.id", school);
    sessionStorage.setItem("crown.role", "daycare_staff");
    sessionStorage.setItem("crown.active.role", "daycare_staff");
  }, { token: scenario.staff_access, school: scenario.school_id });
  const response = await page.goto("/diadem/daycare", { waitUntil: "networkidle" });
  expect(response?.status() ?? 500).toBeLessThan(400);
  await expect(page).toHaveURL(/\/diadem\/daycare$/);
  await expect(page.getByRole("region", { name: "Children in care roster" })).toBeVisible();
}

function headers(scenario: Scenario, token = scenario.staff_access, school = scenario.school_id) {
  return { Authorization: "Bearer " + token, "X-School-Id": school };
}

function candidateUrl(scenario: Scenario, row: Case) {
  return "/api/v1/aftercare/daycare/sites/" + scenario.site_id +
    "/attendance/" + row.attendance_id + "/release-authorities/";
}

const releaseUrl = "/api/v1/aftercare/daycare/attendance/release/";

test.describe.serial("Diadem authenticated local fictional pickup", () => {
  test.skip(!manifestPath && !required, "This is executed only by the isolated Heritage live-browser runner.");

  test("positive: roster -> current guardian -> identity attestation -> POST -> refreshed roster", async ({ page, request }) => {
    const scenario = loadScenario();
    await enterPresenter(page, scenario, process.env.CROWN_EXPECTED_FRONTEND_SHA);
    const row = page.getByRole("row").filter({
      has: page.getByRole("cell", { name: scenario.cases.approved.child_name, exact: true }),
    });
    await expect(row).toBeVisible();
    const candidates = page.waitForResponse((response) =>
      response.url().includes("/release-authorities/") && response.request().method() === "GET"
    );
    await row.getByRole("button", { name: "Review pickup" }).click();
    const candidateResponse = await candidates;
    expect(candidateResponse.status()).toBe(200);
    const candidateData = await candidateResponse.json();
    expect(candidateData.site_id).toBe(scenario.site_id);
    expect(candidateData.attendance_id).toBe(scenario.cases.approved.attendance_id);
    expect(candidateData.options).toEqual([{
      authority_id: scenario.cases.approved.authority_id,
      guardian_name: scenario.guardian_name,
    }]);

    await page.getByLabel("Verified pickup recipient").selectOption(scenario.cases.approved.authority_id);
    await page.getByLabel("Identity verification method").selectOption("GOVERNMENT_PHOTO_ID");
    await page.getByRole("checkbox").check();
    const posted = page.waitForResponse((response) =>
      response.url().endsWith("/daycare/attendance/release/") &&
      response.request().method() === "POST"
    );
    await page.getByRole("button", { name: "Confirm verified handoff" }).click();
    const response = await posted;
    expect(response.status()).toBe(201);
    const result = await response.json();
    expect(result.status).toBe("released");
    expect(result.attendance_id).toBe(scenario.cases.approved.attendance_id);
    expect(result.release_id).toMatch(/^[0-9a-f-]{36}$/i);
    await expect(page.getByText(/Server-confirmed handoff/)).toBeVisible();
    await expect(page.getByText(scenario.cases.approved.child_name, { exact: true })).toHaveCount(0);
    await expect(verifyPresenter(scenario, process.env.CROWN_EXPECTED_FRONTEND_SHA)).rejects.toThrow(/already released/);

    const roster = await request.get(
      "/api/v1/aftercare/daycare/sites/" + scenario.site_id + "/roster/",
      { headers: headers(scenario) },
    );
    expect(roster.status()).toBe(200);
    const verified = await roster.json();
    expect(verified.rows.some((item: { attendance_id: string }) =>
      item.attendance_id === scenario.cases.approved.attendance_id)).toBe(false);
    await page.reload({ waitUntil: "networkidle" });
    await expect(page.getByText(scenario.cases.approved.child_name, { exact: true })).toHaveCount(0);
  });

  test("negative: revoked and expired pickup recipients are not presented or released", async ({ page, request }) => {
    const scenario = loadScenario();
    await staffSession(page, scenario);
    for (const kind of ["revoked", "expired"] as const) {
      const denied = scenario.cases[kind];
      const row = page.getByRole("row").filter({
        has: page.getByRole("cell", { name: denied.child_name, exact: true }),
      });
      await expect(row).toBeVisible();
      await row.getByRole("button", { name: "Review pickup" }).click();
      await expect(page.getByText(/No verified recipient available/)).toBeVisible();
      expect(await page.getByRole("button", { name: "Confirm verified handoff" }).count()).toBe(0);
      const candidates = await request.get(candidateUrl(scenario, denied), {
        headers: headers(scenario),
      });
      expect(candidates.status()).toBe(200);
      expect((await candidates.json()).options).toEqual([]);
      const forged = await request.post(releaseUrl, {
        headers: headers(scenario),
        data: {
          site_id: scenario.site_id, room_id: scenario.room_id,
          attendance_id: denied.attendance_id,
          guardian_authority_id: denied.authority_id,
          request_key: crypto.randomUUID(),
          identity_method: "GOVERNMENT_PHOTO_ID",
          identity_verified: true,
        },
      });
      expect(forged.status()).toBeGreaterThanOrEqual(400);
      expect(forged.status()).toBeLessThan(500);
      await page.getByRole("button", { name: "Cancel review" }).click();
    }
  });

  test("negative: anonymous, unauthorized staff and cross-school headers deny custody reads", async ({ request }) => {
    const scenario = loadScenario();
    const url = candidateUrl(scenario, scenario.cases.revoked);
    const anonymous = await request.get(url, { headers: { "X-School-Id": scenario.school_id } });
    expect(anonymous.status()).toBeGreaterThanOrEqual(400);
    const noRole = await request.get(url, {
      headers: headers(scenario, scenario.unprivileged_access),
    });
    expect(noRole.status()).toBeGreaterThanOrEqual(400);
    const foreign = await request.get(url, {
      headers: headers(scenario, scenario.staff_access, "11111111-1111-4111-8111-111111111111"),
    });
    expect(foreign.status()).toBeGreaterThanOrEqual(400);
    for (const response of [anonymous, noRole, foreign]) {
      expect(response.status()).toBeLessThan(500);
      expect(await response.text()).not.toContain(scenario.cases.revoked.child_name);
    }
  });
});
