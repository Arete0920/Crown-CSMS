import { expect, test } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

// Read-only presenter navigation, using the ACTUAL local session endpoint and
// real browser links. Transactional POST/readback is certified by separate
// Camp, Jireh, Daycare and Extended Care browser specs in the same rehearsal.
const FRONTEND = "http://127.0.0.1:4173";
const enabled = process.env.CROWN_LOCAL_PRESENTER_E2E === "1";
if (process.env.CROWN_REQUIRE_LOCAL_PRESENTER_PROOF === "1" && !enabled) {
  throw new Error("Six-persona presenter link audit must not be skipped.");
}

const personas = [
  { role: "school_admin", label: "School Administrator", paths: [
    "/summer-camp-dashboard/setup", "/summer-camp-dashboard/roster",
    "/before-care/roster", "/aftercare/roster", "/school-admin-dashboard",
    "/registrar-dashboard", "/attendance-dashboard", "/gradebook-dashboard",
    "/finance", "/communications-dashboard",
  ] },
  { role: "admissions_director", label: "Admissions Director", paths: [
    "/admissions-dashboard", "/admissions/pipeline", "/admissions/apply",
    "/admissions/checklist", "/enrollment-conversion",
  ] },
  { role: "finance_director", label: "Finance Director", paths: [
    "/finance", "/finance/invoices", "/finance",
    "/finance/exceptions", "/finance/bank-reconciliation",
  ] },
  { role: "teacher", label: "Teacher / Staff", paths: [
    "/teacher/classes", "/teacher/attendance", "/teacher/lesson-plans/today",
    "/teacher/lesson-plans/today", "/teacher/daily-cockpit",
    "/academics/teacher-grading", "/gradebook",
  ] },
  { role: "parent", label: "Parent / Guardian", paths: [
    "/parent/admissions/start", "/admissions/apply", "/parent/financial-aid",
    "/parent/admissions/status", "/parent/admissions/status", "/parent",
    "/parent/learning-status", "/parent/billing",
  ] },
  { role: "student", label: "Student", paths: [
    "/student", "/student/today", "/student/assignments",
    "/academics/student-work", "/student", "/student",
  ] },
] as const;

const knownRedirects: Record<string, string[]> = {
  "/enrollment-conversion": ["/wizards"],
};

test.describe("Heritage six-persona guided presenter links, click by click", () => {
  test.skip(!enabled, "Only the prepared fictional local Windows five-module rehearsal.");
  test.use({ baseURL: FRONTEND, viewport: { width: 1366, height: 768 } });

  for (const persona of personas) {
    test(persona.role + " follows every linked proof step from /sandbox", async ({ page, request }, info) => {
      test.setTimeout(240_000);
      const expectedSource = process.env.CROWN_EXPECTED_FRONTEND_SHA;
      const evidenceDir = process.env.CROWN_PRESENTER_LINK_AUDIT_DIR;
      expect(expectedSource).toMatch(/^[0-9a-f]{40}$/);
      expect(evidenceDir).toBeTruthy();

      const report: {
        source_sha: string | undefined; role: string; result: string;
        expected_links: number; clicked_links: number;
        pages: { requested: string; observed: string; heading: string }[];
        browser_errors: string[]; server_errors: string[]; error?: string;
      } = {
        source_sha: expectedSource, role: persona.role, result: "FAIL",
        expected_links: persona.paths.length, clicked_links: 0, pages: [],
        browser_errors: [], server_errors: [],
      };
      page.on("pageerror", error => report.browser_errors.push(error.message));
      page.on("response", response => {
        try {
          const url = new URL(response.url());
          if ((url.hostname === "localhost" || url.hostname === "127.0.0.1")
              && url.pathname.startsWith("/api/") && response.status() >= 500) {
            report.server_errors.push(url.pathname + ": HTTP " + response.status());
          }
        } catch { /* Non-URL browser resources are irrelevant. */ }
      });
      try {
        const build = await request.get(FRONTEND + "/build.json");
        expect(build.status()).toBe(200);
        expect((await build.json()).build_sha).toBe(expectedSource);
        await page.goto("/sandbox", { waitUntil: "domcontentloaded" });

        const roleCard = page.locator(".sandbox-persona-card")
          .filter({ has: page.getByText(persona.label, { exact: true }) }).first();
        await expect(roleCard).toBeVisible();
        await roleCard.getByRole("button", { name: "Start guided" }).click();
        await expect(page).toHaveURL(/\/sandbox\/command-center\?/);
        expect(await page.evaluate(() => sessionStorage.getItem("crown.role"))).toBe(persona.role);
        await expect(page.getByRole("heading", { name: /Guided proof path/i })).toBeVisible();

        const items = page.locator(".sandbox-workspace-preview ol li a");
        const routes = await items.evaluateAll(anchors => anchors.map(a => a.getAttribute("href")));
        expect(routes).toEqual([...persona.paths]);
        for (const [index, href] of routes.entries()) {
          expect(href).toMatch(/^\/(?!\/)/);
          const link = page.locator(".sandbox-workspace-preview ol li a").nth(index);
          await expect(link).toBeVisible();
          await link.click();
          await expect(page).not.toHaveURL(/\/(login|sandbox\/command-center)(?:\?|$)/);
          // Some legitimate operational pages use MUI Box instead of a semantic main.
          // Require a visible document heading and actual page content, not one tag name.
          const headingNode = page.locator("h1, h2, h3, h4, [role='heading']").filter({ hasText: /\S.{2,}/ }).first();
          await expect(headingNode).toBeVisible();
          const observed = new URL(page.url()).pathname;
          const accepted = [href!, ...(knownRedirects[href!] || [])];
          expect(accepted).toContain(observed);
          const heading = String(await headingNode.textContent() || "").trim();
          expect(heading.length).toBeGreaterThan(2);
          expect(heading).not.toMatch(/^(404|not found|unauthorized|access denied)$/i);
          const contentRoot = page.locator("main, [role='main']").first();
          const mainText = String(await (await contentRoot.count()
            ? contentRoot.innerText() : page.locator("body").innerText()) || "").trim();
          expect(mainText.length).toBeGreaterThan(35);
          expect(mainText).not.toMatch(/missing household_id in query string|not authorized|access denied/i);
          if (persona.role === "finance_director" && index === 2) {
            // The prior URL-only family detail link failed without a household ID.
            // This live existing panel already displays the fictional household ledger.
            await expect(page.getByTestId("sandbox-finance-transaction")).toBeVisible();
            await expect(page.getByTestId("finance-family-account")).toContainText("Reed Family");
          }
          await page.screenshot({ path: info.outputPath(
            persona.role + "-" + String(index + 1).padStart(2, "0") + ".png"
          ), fullPage: false });
          report.pages.push({ requested: href!, observed, heading });
          report.clicked_links = report.pages.length;
          await page.goBack({ waitUntil: "domcontentloaded" });
          await expect(page).toHaveURL(/\/sandbox\/command-center\?/);
          expect(await page.evaluate(() => sessionStorage.getItem("crown.role"))).toBe(persona.role);
        }
        expect(report.server_errors).toEqual([]);
        expect(report.browser_errors).toEqual([]);
        expect(report.clicked_links).toBe(persona.paths.length);
        report.result = "PASS";
      } catch (error) {
        report.error = String(error);
        throw error;
      } finally {
        if (evidenceDir) {
          mkdirSync(evidenceDir, { recursive: true });
          writeFileSync(join(evidenceDir, "presenter-links-" + persona.role + ".json"),
            JSON.stringify(report, null, 2) + "\n", "utf8");
        }
      }
    });
  }
});
