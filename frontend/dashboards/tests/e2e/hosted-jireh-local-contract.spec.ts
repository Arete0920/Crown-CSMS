import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";

// Disposable PostgreSQL integration only. This cannot certify Azure or run
// against a public target; cloud-boundary checks are tested separately.
const enabled = process.env.CROWN_HOSTED_JIREH_LOCAL_CONTRACT === "1";
const frontend = "http://127.0.0.1:4175", backend = "http://127.0.0.1:8003";
const aid = "/api/v1/buyer-demo/jireh/aid/family/", sgo = "/api/v1/buyer-demo/jireh/sgo";
test.use({ trace: "off", video: "off" });
test.skip(!enabled, "Requires explicit disposable local hosted-contract harness");
test("invited family and processor perform persisted Jireh journeys with cross-buyer denial", async ({ page }) => {
  test.setTimeout(120_000);
  const fixture = JSON.parse(readFileSync(process.env.CROWN_HOSTED_JIREH_MANIFEST!, "utf8"));
  if (!fixture.synthetic_local_contract || !/^[a-f0-9]{40}$/.test(fixture.source_sha) || fixture.source_sha !== process.env.CROWN_EXPECTED_FRONTEND_SHA) throw new Error("Unverified test fixture");
  expect((await (await page.request.get(frontend + "/build.json")).json()).build_sha).toBe(fixture.source_sha);
  expect((await (await page.request.get(backend + "/api/health/")).json()).build_sha).toBe(fixture.source_sha);
  async function login(buyer: number, role: string, path: string) {
    const response = await page.request.post(backend + "/api/v1/sandbox/session/", {
      data: { invite_id: fixture.invites[buyer], role, school: "heritage-core", track: "school" },
    });
    if (response.status() !== 201) throw new Error("Synthetic invitation login refused");
    const session = await response.json();
    await page.goto(frontend + "/build.json");
    await page.evaluate((data) => {
      sessionStorage.clear(); localStorage.clear();
      sessionStorage.setItem("crown.jwt.access", data.access);
      sessionStorage.setItem("crown.school.id", data.school_id);
      sessionStorage.setItem("crown.role", data.role_code);
    }, session);
    await page.goto(frontend + path);
    return { Authorization: "Bearer " + session.access, "X-School-Id": session.school_id };
  }
  const headers = await login(0, "parent", "/parent/financial-aid");
  const submit = page.getByRole("button", { name: "Submit fictional Financial Aid application" });
  await expect(submit).toBeDisabled();
  await page.getByRole("checkbox", { name: /I confirm all application/ }).check();
  const write = page.waitForResponse((r) => r.url().endsWith(aid) && r.request().method() === "POST");
  await submit.click();
  expect((await write).status()).toBe(201);
  await expect(page.getByTestId("jireh-submit-confirmation")).toContainText("independently verified");
  await page.reload();
  await expect(page.getByText(/Duplicate submission is disabled/)).toBeVisible();
  expect((await (await page.request.get(backend + aid, { headers })).json()).applications).toHaveLength(1);
  await page.goto(frontend + "/jireh-sgo/intake");
  const partner = page.getByLabel("Partner SGO and program");
  await expect(partner.locator("option")).toHaveCount(2);
  const programs = await partner.locator("option").evaluateAll((options) => options.map((o) => (o as HTMLOptionElement).value));
  const applications: string[] = [];
  for (const program of programs) {
    await partner.selectOption(program);
    await page.getByRole("checkbox").check();
    const posted = page.waitForResponse((r) => r.url().endsWith(sgo + "/family/submit/") && r.request().method() === "POST");
    await page.getByRole("button", { name: "Submit fictional application", exact: true }).click();
    const response = await posted; expect(response.status()).toBe(201);
    applications.push((await response.json()).application.id);
    await expect(page.getByText("Saved. The submitted fictional application was read back from the server.")).toBeVisible();
    await page.reload(); await partner.selectOption(program);
    await expect(page.getByText(applications.at(-1)!, { exact: true })).toBeVisible();
  }
  await login(0, "finance_director", "/jireh-sgo/intake");
  await page.getByLabel("Assigned partner program").selectOption(programs[0]);
  await page.getByRole("button", { name: "Request correction", exact: true }).click();
  await expect(page.getByText(/Nonbinding verification correction request recorded/)).toBeVisible();
  await login(0, "parent", "/jireh-sgo/intake");
  await partner.selectOption(programs[0]);
  await page.getByLabel("Correct or confirm fictional grade").selectOption("8");
  await page.getByRole("button", { name: "Save correction and resubmit" }).click();
  await expect(page.getByText("RESUBMITTED", { exact: true })).toBeVisible();
  await page.reload(); await partner.selectOption(programs[0]);
  await expect(page.getByText("RESUBMITTED", { exact: true })).toBeVisible();
  const other = await login(1, "parent", "/parent/financial-aid");
  expect((await (await page.request.get(backend + aid, { headers: other })).json()).applications).toHaveLength(0);
  expect((await page.request.get(backend + sgo + "/family/applications/" + applications[0] + "/", { headers: other })).status()).toBe(403);
  expect((await page.request.post(backend + "/api/v1/aid/family/demo-intake/", { headers: other, data: {} })).status()).toBe(404);
  expect((await page.request.get(backend + "/api/v1/jireh-sgo/family/programs/", { headers: other })).status()).toBe(400);
  const processor = await login(1, "finance_director", "/jireh-sgo/intake");
  expect((await page.request.get(backend + sgo + "/processor/programs/" + programs[0] + "/queue/", { headers: processor })).status()).toBe(404);
  console.log(JSON.stringify({ source_sha: fixture.source_sha, local_hosted_contract: "PASS", azure_certified: false }));
});
