import { expect, test, type Page } from "@playwright/test";

const frontendUrl = process.env.CERT_FRONTEND_URL || "http://127.0.0.1:4173";

// Never run this fictional state-changing acceptance outside local Heritage.
async function launch(page: Page, role: string) {
  await page.goto(frontendUrl + "/login", { waitUntil: "networkidle" });
  const roleSelect = page.locator("#login-role").first();
  await expect(roleSelect).toBeVisible();
  await roleSelect.selectOption(role);
  await page.getByRole("button", { name: /continue to heritage preview/i }).first().click();
  await expect(page).not.toHaveURL(/\/login(?:\?.*)?$/i, { timeout: 30000 });
}

function isParentState(url: string) {
  return url.includes("/api/v1/sandbox/parent/enrollment/");
}

test("the exact parent application remains enrolled for registrar and Parent360", async ({ browser }) => {
  test.setTimeout(180000);
  expect(["localhost", "127.0.0.1"]).toContain(new URL(frontendUrl).hostname);
  expect(process.env.CROWN_ENV).toBe("local");
  expect(process.env.VITE_LOCAL_DEMO).toBe("1");

  const parentContext = await browser.newContext();
  const registrarContext = await browser.newContext();
  try {
    const parent = await parentContext.newPage();
    await launch(parent, "parent");
    const beforePromise = parent.waitForResponse(
      (r) => isParentState(r.url()) && r.request().method() === "GET", { timeout: 60000 },
    );
    await parent.goto(frontendUrl + "/parent/admissions/status", { waitUntil: "networkidle" });
    const beforeResponse = await beforePromise;
    expect(beforeResponse.status()).toBe(200);
    const before = await beforeResponse.json();
    expect(["accepted", "enrolled"]).toContain(before.lifecycle_stage);
    expect(before.application_id).toBeTruthy();
    expect(before.demo_payment_processed).toBe(false);
    let completed = before;
    if (before.lifecycle_stage === "accepted") {
      await parent.getByLabel("Accept sandbox enrollment agreement").check();
      const postPromise = parent.waitForResponse(
        (r) => isParentState(r.url()) && r.request().method() === "POST", { timeout: 60000 },
      );
      await parent.getByRole("button", { name: /accept enrollment and complete demo handoff/i }).click();
      const post = await postPromise;
      expect(post.status()).toBe(200);
      completed = await post.json();
    }
    expect(completed.application_id).toBe(before.application_id);
    expect(completed.lifecycle_stage).toBe("enrolled");
    expect(completed.contract_status).toBe("countersigned");
    expect(completed.deposit_status).toBe("paid");
    expect(completed.applicant_to_student_status).toBe("completed");
    expect(completed.child_id).toBeTruthy();
    expect(completed.demo_payment_processed).toBe(false);

    const registrar = await registrarContext.newPage();
    await launch(registrar, "admissions_director");
    const listPromise = registrar.waitForResponse(
      (r) => r.url().includes("/api/admissions/applications/") && r.request().method() === "GET",
      { timeout: 60000 },
    );
    await registrar.goto(frontendUrl + "/admissions/pipeline", { waitUntil: "networkidle" });
    const list = await listPromise;
    expect(list.status()).toBe(200);
    await expect(registrar.getByText("Live / Role Scoped", { exact: true })).toBeVisible();

    const sourceHeaders = await list.request().allHeaders();
    // Never print bearer values. This header is taken from the actual registrar request.
    expect(Boolean(sourceHeaders.authorization)).toBe(true);
    const staffHeaders: Record<string, string> = {
      Authorization: sourceHeaders.authorization, Accept: "application/json",
    };
    if (sourceHeaders["x-school-id"]) staffHeaders["X-School-Id"] = sourceHeaders["x-school-id"];
    if (sourceHeaders["x-crown-school-id"]) staffHeaders["X-Crown-School-Id"] = sourceHeaders["x-crown-school-id"];
    const origin = new URL(list.url()).origin;
    const exactApp = origin + "/api/v1/admissions/applications/"
      + encodeURIComponent(String(completed.application_id));
    const staffStateResponse = await registrarContext.request.get(
      exactApp + "/enrollment-state/", { headers: staffHeaders },
    );
    expect(staffStateResponse.status()).toBe(200);
    const staffState = await staffStateResponse.json();
    expect(staffState.application_id).toBe(completed.application_id);
    expect(staffState.contract_status).toBe("countersigned");
    expect(staffState.deposit_status).toBe("paid");

    const eventsResponse = await registrarContext.request.get(
      exactApp + "/event-replay/", { headers: staffHeaders },
    );
    expect(eventsResponse.status()).toBe(200);
    const events = await eventsResponse.json();
    expect(events.application_id).toBe(completed.application_id);
    expect((events.events || []).filter(
      (event: { event_type: string }) => event.event_type === "enrollment_confirmed",
    )).toHaveLength(1);

    // Negative proof: a parent bearer cannot use the registrar-only read.
    const parentSource = await beforeResponse.request().allHeaders();
    expect(Boolean(parentSource.authorization)).toBe(true);
    const parentHeaders: Record<string, string> = {
      Authorization: parentSource.authorization, Accept: "application/json",
    };
    if (parentSource["x-school-id"]) parentHeaders["X-School-Id"] = parentSource["x-school-id"];
    if (parentSource["x-crown-school-id"]) parentHeaders["X-Crown-School-Id"] = parentSource["x-crown-school-id"];
    const denied = await parentContext.request.get(
      exactApp + "/enrollment-state/", { headers: parentHeaders },
    );
    expect(denied.status()).toBe(403);

    const statePromise = parent.waitForResponse(
      (r) => isParentState(r.url()) && r.request().method() === "GET", { timeout: 60000 },
    );
    const overviewPromise = parent.waitForResponse(
      (r) => r.url().includes("/api/v1/parent360/me/overview/") && r.request().method() === "GET",
      { timeout: 60000 },
    );
    await parent.reload({ waitUntil: "networkidle" });
    const [stateResponse, overviewResponse] = await Promise.all([statePromise, overviewPromise]);
    expect(stateResponse.status()).toBe(200);
    expect(overviewResponse.status()).toBe(200);
    // Read-only replay avoids evicted Chromium response bodies; no POST replay.
    const stateRead = await parentContext.request.fetch(stateResponse.request());
    const overviewRead = await parentContext.request.fetch(overviewResponse.request());
    expect(stateRead.status()).toBe(200);
    expect(overviewRead.status()).toBe(200);
    const after = await stateRead.json();
    const overview = await overviewRead.json();
    expect(after.application_id).toBe(completed.application_id);
    expect(after.child_id).toBe(completed.child_id);
    expect(after.lifecycle_stage).toBe("enrolled");
    const exactRow = (overview?.admissions_continuity?.applications || []).find(
      (row: { application_id: string }) => row.application_id === completed.application_id,
    );
    expect(exactRow?.lifecycle_stage).toBe("enrolled");
    await expect(parent.getByTestId("sandbox-parent-enrollment-complete")).toContainText("Jordan Reed");
  } finally {
    await registrarContext.close();
    await parentContext.close();
  }
});
