// Private local operator handoff, never a public login or a permission grant.
import { chromium } from "@playwright/test";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";

const school = "19801b59-8c05-4c84-9312-5d792e4e839d";
const frontend = "http://127.0.0.1:4173";
const backend = "http://127.0.0.1:8000";
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

export async function verifyPresenter(scenario, sha, fetcher = fetch) {
  if (!/^[0-9a-f]{40}$/.test(sha) || scenario.source_sha !== sha ||
      scenario.fictional_only !== true || scenario.school_id !== school ||
      !/^[0-9a-f]{10}$/.test(scenario.scenario) ||
      !uuid.test(scenario.site_id) || !uuid.test(scenario.cases?.approved?.attendance_id) ||
      !scenario.staff_access) throw new Error("Invalid fictional presenter source or scope.");
  async function get(url, authenticated = false) {
    const response = await fetcher(url, { redirect: "error", headers: authenticated ? {
      Authorization: "Bearer " + scenario.staff_access, "X-School-Id": school,
    } : {} });
    if (response.status !== 200) throw new Error("Presenter readback denied.");
    return response.json();
  }
  if ((await get(frontend + "/build.json")).build_sha !== sha)
    throw new Error("Presenter frontend source mismatch.");
  const health = await get(backend + "/api/health/");
  if (health.build_sha !== sha || health.env !== "local" || health.db !== "ok")
    throw new Error("Presenter backend source or environment mismatch.");
  const roster = await get(backend + "/api/v1/aftercare/daycare/sites/" + scenario.site_id + "/roster/", true);
  if (roster.site_id !== scenario.site_id || !roster.rows?.some(row =>
    row.attendance_id === scenario.cases.approved.attendance_id))
    throw new Error("Presenter custody scenario is unavailable or already released.");
  const authorities = await get(backend + "/api/v1/aftercare/daycare/sites/" + scenario.site_id +
    "/attendance/" + scenario.cases.approved.attendance_id + "/release-authorities/", true);
  if (authorities.attendance_id !== scenario.cases.approved.attendance_id ||
      authorities.options?.length !== 1 || authorities.options[0].authority_id !== scenario.cases.approved.authority_id)
    throw new Error("Presenter guardian authority is unavailable.");
}

export async function enterPresenter(page, scenario, sha) {
  await verifyPresenter(scenario, sha);
  const response = await page.goto(frontend + "/build.json");
  if (response?.status() !== 200 || (await response.json()).build_sha !== sha)
    throw new Error("Presenter frontend changed before entry.");
  await page.evaluate(({ token, tenant }) => {
    if (location.origin !== "http://127.0.0.1:4173") return;
    sessionStorage.clear();
    sessionStorage.setItem("crown.jwt.access", token);
    sessionStorage.setItem("crown.school.id", tenant);
    sessionStorage.setItem("crown.role", "daycare_staff");
    sessionStorage.setItem("crown.active.role", "daycare_staff");
  }, { token: scenario.staff_access, tenant: school });
  // One installation; reload cannot reinstall an old identity or clear custody warnings.
  await page.goto(frontend + "/diadem/daycare");
  await page.getByRole("region", { name: "Children in care roster" }).waitFor();
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  let browser;
  try {
    let input = "";
    for await (const chunk of process.stdin) input += chunk;
    const scenario = JSON.parse(input);
    await verifyPresenter(scenario, process.env.BUILD_SHA);
    const check = process.argv.includes("--check");
    // Windows acceptance must exercise a visible window, just like the presenter.
    const headless = check && process.platform !== "win32";
    browser = await chromium.launch({ headless });
    const page = await browser.newPage();
    await enterPresenter(page, scenario, process.env.BUILD_SHA);
    page.once("close", () => browser.close().catch(() => {}));
    console.log(`Verified fictional DAYCARE_STAFF; source ${scenario.source_sha}; scenario ${scenario.scenario}. Close the browser to end this session.`);
    console.log(JSON.stringify({ presenter_entry: "PASS", source_sha: scenario.source_sha,
      scenario: scenario.scenario, visible_browser: !headless, custody_write_performed: false }));
    if (check) {
      await page.screenshot({ path: fileURLToPath(new URL("../../../.local-backups/heritage-demo/presenter-entry.png", import.meta.url)), fullPage: true });
      await browser.close();
    }
    else await new Promise(done => browser.on("disconnected", done));
  } catch {
    console.error("Presenter entry refused. Check local source, staff authorization, expiry and unconsumed scenario; no credentials were printed.");
    await browser?.close();
    process.exitCode = 1;
  }
}
