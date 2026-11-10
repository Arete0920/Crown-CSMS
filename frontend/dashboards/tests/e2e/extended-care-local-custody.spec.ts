import { expect, test, request as isolatedRequest, type APIRequestContext, type Page } from "@playwright/test";

// Destructive acceptance on a fresh isolated Heritage SQLite instance only.
// #618 owns this fictional learner; daily QA schedule enables weekday/weekend browser proof.
// No intercepted APIs, arbitrary children, live families or payment operations.
const FRONTEND = "http://127.0.0.1:4173";
const BACKEND = "http://127.0.0.1:8000";
const SCHOOL = "19801b59-8c05-4c84-9312-5d792e4e839d";
const CHILD = "43848698-9317-5444-9acd-6a08b2d01678";
const API = "/api/v1/aftercare";
const enabled = process.env.CROWN_CARE_LOCAL_E2E === "1";
if (process.env.CROWN_REQUIRE_CARE_BROWSER_PROOF === "1" && !enabled) {
  throw new Error("Required real Extended Care browser proof cannot be skipped.");
}

async function session(role = "school_admin") {
  const anonymous = await isolatedRequest.newContext();
  try {
    const response = await anonymous.post(BACKEND + "/api/v1/sandbox/session/", {
      data: { role, school: "heritage-core" },
    });
    expect(response.status()).toBe(201);
    const body = await response.json();
    expect(body.school_id).toBe(SCHOOL);
    expect(body.access).toBeTruthy();
    return { Authorization: `Bearer ${body.access}`, "X-School-Id": SCHOOL };
  } finally {
    await anonymous.dispose();
  }
}

async function row(request: APIRequestContext, headers: Record<string, string>, care: string) {
  const response = await request.get(BACKEND + API + "/roster/today/?care_session=" + care, { headers });
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body.care_session).toBe(care);
  const rows = body.rows.filter((item: { student_id: string }) => item.student_id === CHILD);
  expect(rows, "Run #618 canonical daily samples on a fresh isolated Heritage database").toHaveLength(1);
  expect(rows[0].student_name).toBe("Sample Learner");
  return rows[0];
}

async function browserWrite(page: Page, path: string, action: () => Promise<void>, status: number) {
  const pending = page.waitForResponse((response) =>
    new URL(response.url()).pathname === API + path && response.request().method() === "POST",
  );
  await action();
  const response = await pending;
  expect(response.status()).toBe(status);
  expect(await response.request().headerValue("authorization")).toMatch(/^Bearer /);
  expect(await response.request().headerValue("x-school-id")).toBe(SCHOOL);
  const body = await response.json();
  // A response alone is not confirmed custody: let the UI finish fresh GET
  // verification before reloading, rather than interrupting its safety barrier.
  await expect.poll(() => page.evaluate(() =>
    sessionStorage.getItem("crown.extended-care.unconfirmed-custody"),
  )).toBeNull();
  return body;
}

test.describe("Extended Care real local custody acceptance", () => {
  test.skip(!enabled, "Explicitly opt in on fresh local Heritage with #618 samples.");

  test("signed AM handoff and PM authorized pickup persist across fresh GETs and reload", async ({ page, request }, testInfo) => {
    test.setTimeout(180_000);
    page.setDefaultTimeout(15_000);
    expect(process.env.CROWN_EXPECTED_FRONTEND_SHA).toMatch(/^[0-9a-f]{40}$/);
    const build = await request.get(FRONTEND + "/build.json");
    expect(build.status()).toBe(200);
    const identity = await build.json();
    expect(identity.build_sha).toBe(process.env.CROWN_EXPECTED_FRONTEND_SHA);
    expect(identity.deploy_tag).toBe("heritage-local");
    const catalog = await request.get(BACKEND + "/api/v1/sandbox/catalog/");
    expect(catalog.status()).toBe(200);
    expect((await catalog.json()).schools.map((school: { key: string }) => school.key)).toEqual(["heritage-core"]);
    const reader = await session();
    expect((await row(request, reader, "AM")).attendance).toBeNull();
    expect((await row(request, reader, "PM")).attendance).toBeNull();

    // Real authorized configuration write keeps this synthetic exercise noncash
    // even if the operator runs after the school's normal pickup cutoff.
    const config = await request.put(BACKEND + API + "/config/", {
      headers: reader, data: { late_fee_per_10_min: "0.00" },
    });
    expect(config.status()).toBe(200);
    expect(Number((await config.json()).late_fee_per_10_min)).toBe(0);
    const contacts = await request.get(BACKEND + API + `/students/${CHILD}/pickup-contacts/`, { headers: reader });
    expect(contacts.status()).toBe(200);
    expect(await contacts.json(), "Do not reuse a previously exercised custody fixture").toHaveLength(0);
    const createdContact = await request.post(BACKEND + API + `/students/${CHILD}/pickup-contacts/`, {
      headers: reader, data: { name: "Fictional Care Guardian", relationship: "Synthetic guardian", is_active: true },
    });
    expect(createdContact.status()).toBe(201);
    const contact = await createdContact.json();
    const parent = await session("parent");
    expect((await request.post(BACKEND + API + "/attendance/checkin/", {
      headers: parent, data: { student_id: CHILD, care_session: "AM" },
    })).status()).toBe(403);
    expect([400, 403, 404]).toContain((await request.get(BACKEND + API + "/roster/today/?care_session=AM", {
      headers: { ...reader, "X-School-Id": "22222222-2222-4222-8222-222222222222" },
    })).status());

    await page.goto(FRONTEND + "/login", { waitUntil: "domcontentloaded" });
    await page.locator("#login-role").first().selectOption("school_admin");
    await page.getByRole("button", { name: /continue to heritage preview/i }).first().click();
    await expect(page).not.toHaveURL(/\/login(?:\?.*)?$/);
    await page.goto(FRONTEND + "/before-care/roster");
    const child = page.locator("tbody tr").filter({ has: page.getByRole("cell", { name: "Sample Learner", exact: true }) });
    await expect(child).toHaveCount(1);
    const admittedAM = await browserWrite(page, "/attendance/checkin/", () => child.getByRole("button", { name: "Check In", exact: true }).click(), 201);
    expect((await row(request, reader, "AM")).attendance.id).toBe(admittedAM.id);
    await page.reload();
    await expect(child.getByText("Checked in", { exact: true })).toBeVisible();
    expect((await request.post(BACKEND + API + "/attendance/checkin/", {
      headers: reader, data: { student_id: CHILD, care_session: "PM" },
    })).status()).toBe(400);
    expect((await row(request, reader, "PM")).attendance).toBeNull();
    await child.getByRole("button", { name: "Acknowledge School Handoff" }).click();
    await expect(page.getByRole("button", { name: "Record School Handoff" })).toBeDisabled();
    await page.getByRole("checkbox", { name: /I am the receiving staff member/ }).check();
    const handoff = await browserWrite(page, "/attendance/school-handoff/", () => page.getByRole("button", { name: "Record School Handoff" }).click(), 200);
    expect(handoff.handoff_verified).toBe(true);
    expect(handoff.handoff_recipient).toBeTruthy();
    await page.reload();
    await expect(child.getByText("Handed off", { exact: true })).toBeVisible();
    const freshReader = await session();
    expect((await row(request, freshReader, "AM")).attendance).toMatchObject({
      id: admittedAM.id, handoff_verified: true, handoff_recipient: handoff.handoff_recipient,
    });

    await page.goto(FRONTEND + "/aftercare/roster");
    const admittedPM = await browserWrite(page, "/attendance/checkin/", () => child.getByRole("button", { name: "Check In", exact: true }).click(), 201);
    expect(admittedPM.id).not.toBe(admittedAM.id);
    await page.reload();
    await expect(child.getByText("Checked in", { exact: true })).toBeVisible();
    const pickup = { student_id: CHILD, care_session: "PM", pickup_contact_id: contact.id, pickup_verified: true };
    expect((await request.post(BACKEND + API + "/attendance/checkout/", { headers: parent, data: pickup })).status()).toBe(403);
    expect((await request.post(BACKEND + API + "/attendance/checkout/", {
      headers: reader, data: { ...pickup, pickup_verified: false },
    })).status()).toBe(400);
    expect((await request.post(BACKEND + API + "/attendance/checkout/", {
      headers: reader, data: { ...pickup, pickup_contact_id: 2147483647 },
    })).status()).toBe(400);
    expect((await row(request, freshReader, "PM")).attendance.checkout_time).toBeNull();
    await child.getByRole("button", { name: "Verify Pickup" }).click();
    await expect(page.getByRole("button", { name: "Confirm Checkout" })).toBeDisabled();
    await page.getByLabel("Authorized pickup contact").click();
    await page.getByRole("option", { name: /Fictional Care Guardian/ }).click();
    await page.getByRole("checkbox", { name: /I have checked this person's identity/ }).check();
    const released = await browserWrite(page, "/attendance/checkout/", () => page.getByRole("button", { name: "Confirm Checkout" }).click(), 200);
    expect(released).toMatchObject({ id: admittedPM.id, pickup_contact_id: contact.id, pickup_verified: true, late_fee_cents: 0 });
    expect(released.late_fee_charge_id).toBeFalsy();
    expect(released.checkout_time).toBeTruthy();
    await page.reload();
    await expect(child.getByText("Checked out", { exact: true })).toBeVisible();
    const persisted = (await row(request, await session(), "PM")).attendance;
    expect(persisted).toMatchObject({ id: admittedPM.id, pickup_contact_id: contact.id, pickup_verified: true, checkout_time: released.checkout_time });
    expect((await request.post(BACKEND + API + "/attendance/checkout/", { headers: reader, data: pickup })).status()).toBe(400);
    expect((await request.post(BACKEND + API + "/attendance/checkin/", {
      headers: reader, data: { student_id: CHILD, care_session: "AM" },
    })).status()).toBe(400);
    expect((await row(request, reader, "AM")).attendance.id).toBe(admittedAM.id);
    expect((await row(request, reader, "PM")).attendance).toEqual(persisted);
    await testInfo.attach("real-care-custody-readback", {
      contentType: "application/json", body: Buffer.from(JSON.stringify({
        source_sha: process.env.CROWN_EXPECTED_FRONTEND_SHA, school_id: SCHOOL,
        student_id: CHILD, am_id: admittedAM.id, pm_id: admittedPM.id,
        am_handoff_verified: true, pm_pickup_verified: true, reload_verified: true,
        real_api: true, denied_parent: true, denied_foreign_school: true,
        denied_open_am_to_pm: true, denied_unverified_pickup: true, denied_replay: true,
      })),
    });
  });
});
