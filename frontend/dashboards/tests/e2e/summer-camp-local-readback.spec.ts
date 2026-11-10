import { expect, test, request as isolatedRequest, type Page } from "@playwright/test";

// This suite is deliberately opt-in and pinned to the local Heritage launcher.
// It must never change hosted, production, or real-school configurations.
const FRONTEND = "http://127.0.0.1:4173";
const BACKEND = "http://127.0.0.1:8000";
const WIZARD = "/api/v1/summer-camp/wizard/setup/";
const CONFIG_KEYS = [
  "camp_name", "default_capacity", "default_staff_ratio",
  "public_registration_enabled", "billing_policy",
] as const;

function isWizardResponse(response: { url(): string; request(): { method(): string } }, method: string) {
  const url = new URL(response.url());
  // The Heritage preview proxies browser /api requests to :8000, so their
  // browser-observed origin is :4173. Some developer builds use the direct
  // backend origin. Both paths must still perform the real HTTP transaction.
  return [new URL(FRONTEND).origin, new URL(BACKEND).origin].includes(url.origin) &&
    url.pathname === WIZARD && response.request().method() === method;
}

async function openHeadOfSchool(page: Page) {
  await page.goto(`${FRONTEND}/login`, { waitUntil: "domcontentloaded" });
  const roles = page.locator("#login-role");
  await expect(roles).toBeVisible();
  await roles.selectOption("school_admin");
  await page.getByRole("button", { name: /continue to heritage preview/i }).click();
  await expect(page).not.toHaveURL(/\/login(?:\?.*)?$/, { timeout: 30_000 });
}

test.describe("Camp setup — isolated local Heritage acceptance", () => {
  test.skip(
    process.env.CROWN_LOCAL_CAMP_E2E !== "1",
    "Opt in only after starting the guarded local Heritage launcher; never run against customer data.",
  );
  test.use({ baseURL: FRONTEND });

  test.beforeEach(async ({ page, request }) => {
    const catalog = await request.get(`${BACKEND}/api/v1/sandbox/catalog/`);
    expect(catalog.ok(), "Local Heritage sandbox backend is required").toBe(true);
    const payload = await catalog.json();
    expect(payload.schools?.map((school: { key: string }) => school.key)).toEqual(["heritage-core"]);
    await openHeadOfSchool(page);
  });

  test("real fictional registration persists after reload while clearance and unauthorized admission stay denied", async ({ page, request }, testInfo) => {
    expect(process.env.CROWN_EXPECTED_FRONTEND_SHA).toMatch(/^[0-9a-f]{40}$/);
    const build = await request.get(FRONTEND + "/build.json");
    const identity = await build.json();
    expect(identity.build_sha).toBe(process.env.CROWN_EXPECTED_FRONTEND_SHA);
    expect(identity.deploy_tag).toBe("heritage-local");
    await page.goto(FRONTEND + "/summer-camp-dashboard/roster");
    const panel = page.getByRole("region", { name: "Fictional Camp registration" });
    await expect(panel).toBeVisible();
    const option = panel.getByRole("option", { name: "Avery Reed (Grade 7)", exact: true });
    await expect(option).toHaveCount(1);
    const student = await option.getAttribute("value");
    expect(student).toMatch(/^[0-9a-f-]{36}$/);
    await panel.getByLabel("Camper").selectOption(student!);
    const post = page.waitForResponse((response) => new URL(response.url()).pathname === "/api/v1/summer-camp/enrollments/" && response.request().method() === "POST");
    const get = page.waitForResponse((response) => new URL(response.url()).pathname === "/api/v1/summer-camp/enrollments/" && response.request().method() === "GET");
    await panel.getByRole("button", { name: "Save fictional registration" }).click();
    const posted = await post;
    expect(posted.status()).toBe(201);
    const saved = await posted.json();
    expect(saved).toMatchObject({ student, status: "REGISTERED", readiness_status: "BLOCKED", health_status: "NEEDS_REVIEW", pickup_status: "MISSING", payment_status: "NOT_BILLED", balance_due_cents: 0 });
    expect((await get).status()).toBe(200);
    await expect(panel.getByRole("status")).toContainText("Registration saved and verified");
    const headers = { Authorization: (await posted.request().headerValue("authorization"))!, "X-School-Id": (await posted.request().headerValue("x-school-id"))! };
    expect(headers.Authorization).toMatch(/^Bearer /);
    const readback = await request.get(BACKEND + `/api/v1/summer-camp/enrollments/?session_id=${saved.session}`, { headers });
    expect(readback.status()).toBe(200);
    const canonical = (await readback.json()).filter((item: { id: number }) => item.id === saved.id);
    expect(canonical).toHaveLength(1);
    expect(canonical[0]).toMatchObject({ ...saved, readiness_blockers: expect.arrayContaining([
      "HEALTH_REVIEW_REQUIRED", "PICKUP_CONTACT_MISSING", "STAFF_REVIEW_REQUIRED",
    ]) });
    await page.reload();
    const row = page.locator("tbody tr").filter({ has: page.getByRole("cell", { name: "Avery Reed", exact: true }) });
    await expect(row).toHaveCount(1);
    await expect(row).toContainText("BLOCKED");
    const payload = { session_id: saved.session, student_id: student };
    expect((await request.post(BACKEND + "/api/v1/summer-camp/attendance/checkin/", { headers, data: payload })).status()).toBe(400);
    expect((await request.post(BACKEND + "/api/v1/summer-camp/enrollments/", { headers, data: payload })).status()).toBe(400);
    const forged = await request.post(BACKEND + "/api/v1/summer-camp/enrollments/", { headers, data: { ...payload, health_status: "APPROVED" } });
    expect(forged.status()).toBe(400);
    expect(JSON.stringify(await forged.json())).toContain("cannot be set during registration");
    const foreign = await request.post(BACKEND + "/api/v1/summer-camp/enrollments/", {
      headers: { ...headers, "X-School-Id": "22222222-2222-4222-8222-222222222222" }, data: payload,
    });
    expect([400, 403, 404]).toContain(foreign.status());
    const parent = await isolatedRequest.newContext();
    try {
      const login = await parent.post(BACKEND + "/api/v1/sandbox/session/", { data: { role: "parent", school: "heritage-core" } });
      expect(login.status()).toBe(201);
      const denied = await parent.post(BACKEND + "/api/v1/summer-camp/enrollments/", {
        headers: { Authorization: `Bearer ${(await login.json()).access}`, "X-School-Id": headers["X-School-Id"] }, data: payload,
      });
      expect(denied.status()).toBe(403);
    } finally { await parent.dispose(); }
    const final = await request.get(BACKEND + `/api/v1/summer-camp/enrollments/?session_id=${saved.session}`, { headers });
    expect(final.status()).toBe(200);
    expect((await final.json()).filter((item: { id: number }) => item.id === saved.id)).toEqual(canonical);
    await testInfo.attach("real-camp-registration-readback", {
      contentType: "application/json", body: Buffer.from(JSON.stringify({ source_sha: identity.build_sha,
        enrollment_id: saved.id, session_id: saved.session, student_id: student,
        registration_reload_verified: true, readiness: "BLOCKED", denied_clearance: true,
        denied_checkin: true, denied_parent: true, denied_foreign_school: true, balance_due_cents: 0 })),
    });
  });

  test("real authorized POST and independent GET persist across a reload", async ({ page, request }) => {
    const initialWait = page.waitForResponse((response) => isWizardResponse(response, "GET"));
    await page.goto(`${FRONTEND}/summer-camp-dashboard/setup`);
    const initial = await initialWait;
    expect(initial.status(), "Camp setup GET requires an active fictional entitlement and view grant").toBe(200);
    const prior = await initial.json();
    expect(prior?.wizard?.completed_steps).toBeInstanceOf(Array);
    const headers = await initial.request().allHeaders();
    expect(headers.authorization, "Use a genuine sandbox-issued bearer, never a seeded fake token").toMatch(/^Bearer\s+\S+/i);
    expect(headers["x-school-id"], "Require the sandbox-selected school context").toBeTruthy();

    const initialConfig = Object.fromEntries(CONFIG_KEYS.map((key) => [key, prior.config[key]]));
    const original = {
      config: initialConfig,
      completed_steps: prior.wizard.completed_steps,
      is_completed: prior.wizard.is_completed,
    };
    const authHeaders = {
      Authorization: headers.authorization,
      "X-School-Id": headers["x-school-id"],
    };
    const uniqueName = `Fictional Camp Readback ${Date.now()}`;
    let possiblyWritten = false;

    try {
      await expect(page.getByRole("button", { name: "Save Setup" })).toBeVisible();
      for (let i = 0; i < 3 && !(await page.getByLabel("Camp Name").isVisible()); i += 1) {
        await page.getByRole("button", { name: "Back" }).click();
      }
      await expect(page.getByLabel("Camp Name")).toBeVisible();
      await page.getByLabel("Camp Name").fill(uniqueName);

      const posted = page.waitForResponse((response) => isWizardResponse(response, "POST"));
      const readback = page.waitForResponse((response) => isWizardResponse(response, "GET"));
      possiblyWritten = true;
      await page.getByRole("button", { name: "Save Setup" }).click();
      const postResponse = await posted;
      expect(postResponse.status(), "The real POST must be accepted").toBe(200);
      const getResponse = await readback;
      expect(getResponse.status(), "Require a distinct post-save GET").toBe(200);
      const persisted = await getResponse.json();
      expect(persisted.config.camp_name).toBe(uniqueName);
      expect(persisted.wizard.completed_steps).toEqual(["Program"]);
      expect(persisted.wizard.is_completed).toBe(false);
      await expect(page.getByText(/Saved and verified against server records/)).toBeVisible();

      await page.getByLabel("Camp Name").fill(uniqueName + " unsaved");
      await expect(page.getByText(/Saved and verified against server records/)).toHaveCount(0);

      const reloadWait = page.waitForResponse((response) => isWizardResponse(response, "GET"));
      await page.reload();
      const reloaded = await reloadWait;
      expect((await reloaded.json()).config.camp_name).toBe(uniqueName);
      await expect(page.getByLabel("Camp Name")).toHaveValue(uniqueName);
    } finally {
      // The original school-scoped configuration and completion state must
      // survive the test. Run only against the launcher-isolated SQLite demo.
      if (possiblyWritten) {
        const restored = await request.post(`${BACKEND}${WIZARD}`, {
          headers: authHeaders,
          data: original,
        });
        expect(restored.status(), "Failed to restore fictional Camp setup after browser test").toBe(200);
        const confirmed = await request.get(`${BACKEND}${WIZARD}`, { headers: authHeaders });
        expect(confirmed.status()).toBe(200);
        const after = await confirmed.json();
        for (const key of CONFIG_KEYS) expect(after.config[key]).toEqual(initialConfig[key]);
        expect(after.wizard.completed_steps).toEqual(original.completed_steps);
        expect(after.wizard.is_completed).toBe(original.is_completed);
      }
    }
  });

  test("failed initial GET blocks edits (injected network failure)", async ({ page }) => {
    await page.route(`**${WIZARD}`, async (route) => {
      await route.fulfill({ status: 503, contentType: "application/json", body: '{"detail":"simulated unavailable"}' });
    });
    await page.goto(`${FRONTEND}/summer-camp-dashboard/setup`);
    await expect(page.getByRole("alert")).toContainText("HTTP 503");
    await expect(page.getByRole("button", { name: "Save Setup" })).toHaveCount(0);
  });

  for (const failure of ["failed POST", "mismatched GET"] as const) {
    test(`${failure} cannot claim saved configuration (injected response)`, async ({ page }) => {
      const config = {
        camp_name: "Synthetic Camp",
        default_capacity: 20,
        default_staff_ratio: 8,
        public_registration_enabled: false,
        billing_policy: "PER_SESSION",
      };
      let readCount = 0;
      let postCount = 0;
      await page.route(`**${WIZARD}`, async (route) => {
        if (route.request().method() === "POST") {
          postCount += 1;
          await route.fulfill({
            status: failure === "failed POST" ? 503 : 200,
            contentType: "application/json",
            body: JSON.stringify(failure === "failed POST" ? { detail: "simulated" } : { status: "ok" }),
          });
          return;
        }
        readCount += 1;
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            config: {
              ...config,
              camp_name: readCount === 2 && failure === "mismatched GET" ? "Different server record" : config.camp_name,
            },
            wizard: { completed_steps: ["Program"], is_completed: false },
          }),
        });
      });
      await page.goto(`${FRONTEND}/summer-camp-dashboard/setup`);
      await page.getByLabel("Camp Name").fill("Synthetic Changed Camp");
      await page.getByRole("button", { name: "Save Setup" }).click();
      await expect(page.getByRole("alert")).toBeVisible();
      expect(postCount).toBe(1);
      expect(readCount).toBe(failure === "failed POST" ? 1 : 2);
      await expect(page.getByText(/Saved and verified against server records/)).toHaveCount(0);
      await expect(page.getByRole("button", { name: "Save Setup" })).toHaveCount(0);
    });
  }

  test("summary failure preserves access to operations routes (injected failure)", async ({ page }) => {
    await page.route("**/api/v1/summer-camp/board/summary/", async (route) => {
      await route.fulfill({ status: 503, contentType: "application/json", body: '{"detail":"simulated unavailable"}' });
    });
    await page.goto(`${FRONTEND}/summer-camp-dashboard`);
    await expect(page.getByRole("alert")).toBeVisible();
    const setup = page.getByRole("link", { name: "Configure camp" });
    const roster = page.getByRole("link", { name: "Open attendance and authorized pickup" });
    await expect(setup).toHaveAttribute("href", "/summer-camp-dashboard/setup");
    await expect(roster).toHaveAttribute("href", "/summer-camp-dashboard/roster");
    await setup.click();
    await expect(page).toHaveURL(/\/summer-camp-dashboard\/setup$/);
  });
});
