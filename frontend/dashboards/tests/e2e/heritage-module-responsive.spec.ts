import { expect, test, type Page, type TestInfo } from "@playwright/test";
import { readFileSync, writeFileSync } from "node:fs";
const required = process.env.CROWN_REQUIRE_SGO_BROWSER_PROOF === "1";
let capture = 0;
async function login(page: Page, role: string) {
  await page.goto("/login");
  await page.locator("#login-role").selectOption(role);
  await page.getByRole("button", { name: /continue to heritage preview/i }).click();
  await page.waitForURL(url => !url.pathname.endsWith("/login"));
}
async function inspect(page: Page, path: string, info: TestInfo) {
  const output = info.outputPath(`${++capture}-${path.replaceAll("/", "_")}`);
  await page.goto(path, { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  await expect(page.locator("main")).toHaveCount(1);
  await expect(page.locator("main h1, main h2").first()).toBeVisible();
  writeFileSync(output + ".json", JSON.stringify({ source_sha: process.env.CROWN_EXPECTED_FRONTEND_SHA, ...(await page.evaluate(() => ({ path: location.pathname, width: innerWidth, sidebars: document.querySelectorAll("aside").length, font: getComputedStyle(document.body).fontFamily, main: getComputedStyle(document.querySelector("main")!).padding }))) }));
  expect(await page.evaluate(() => Math.max(document.body.scrollWidth, document.documentElement.scrollWidth) - innerWidth)).toBeLessThanOrEqual(1);
  await page.screenshot({ path: output + ".png", fullPage: true });
}
for (const [width, height] of [[1440, 900], [1024, 768], [390, 844]]) {
  test(`real-role module layouts ${width}x${height}`, async ({ page, context, request }, info) => {
    test.skip(!required, "Only the guarded five-module local rehearsal.");
    test.setTimeout(180_000);
    await page.setViewportSize({ width, height });
    expect((await (await request.get("/build.json")).json()).build_sha).toBe(process.env.CROWN_EXPECTED_FRONTEND_SHA);
    const errors: string[] = []; page.on("pageerror", error => errors.push(error.message));
    await login(page, "school_admin"); const dashboard = new URL(page.url()).pathname;
    for (const path of [dashboard, "/summer-camp-dashboard/roster", "/summer-camp-dashboard/setup", "/before-care/roster", "/aftercare/roster", dashboard]) {
      await inspect(page, path, info);
      if (width <= 1100 && await page.locator(".crown-sidebar-toggle").count()) {
        await page.locator(".crown-sidebar-toggle").focus(); await page.keyboard.press("Enter");
        await expect(page.locator(".crown-sidebar")).toBeVisible();
        await page.locator(".crown-sidebar-close").click(); await expect(page.locator(".crown-sidebar")).toBeHidden();
      }
    }
    await context.clearCookies(); await page.evaluate(() => sessionStorage.clear());
    await login(page, "parent"); const parent = new URL(page.url()).pathname;
    for (const path of [parent, "/parent/financial-aid", parent]) await inspect(page, path, info);
    const scenario = JSON.parse(readFileSync(process.env.CROWN_DIADEM_PICKUP_MANIFEST!, "utf8"));
    expect(scenario.fictional_only).toBe(true); expect(scenario.source_sha).toBe(process.env.CROWN_EXPECTED_FRONTEND_SHA);
    await page.evaluate(s => { sessionStorage.clear(); sessionStorage.setItem("crown.jwt.access", s.staff_access); sessionStorage.setItem("crown.school.id", s.school_id); sessionStorage.setItem("crown.role", "daycare_staff"); sessionStorage.setItem("crown.active.role", "daycare_staff"); }, scenario);
    await inspect(page, "/diadem/daycare", info);
    const credentials = readFileSync(process.env.CROWN_SGO_LOCAL_CREDENTIALS!, "utf8");
    expect(credentials.startsWith("# CROWN fictional SGO local demo accounts.")).toBe(true);
    const block = credentials.split("[Fictional Delaware SGO (demo)]")[1].split("\n[")[0];
    for (const [role, label] of [["family", "Family login"], ["processor", "Processor login"]]) {
      await page.evaluate(() => sessionStorage.clear()); await page.goto("/jireh-sgo/sign-in");
      const [username, password] = block.split(label + ": ")[1].split(/\r?\n/)[0].split(" / ");
      expect(username).toBe("sgo_demo_de_" + role);
      await page.getByLabel("Synthetic account username").fill(username); await page.getByLabel("Synthetic account password").fill(password);
      await page.getByRole("button", { name: "Sign in to fictional SGO" }).click(); await page.waitForURL("**/jireh-sgo/intake");
      await expect(page.getByLabel(role === "family" ? "Partner SGO and program" : "Assigned partner program")).toBeVisible();
      await inspect(page, "/jireh-sgo/intake", info); await expect(page.locator("aside")).toHaveCount(0);
    }
    expect(errors).toEqual([]);
  });
}
