import fs from "node:fs";
import path from "node:path";
import AxeBuilder from "@axe-core/playwright";
import { test, expect } from "@playwright/test";
import { attachNetworkRecorder } from "./network-recorder";

type LiveRuntimeResult = {
  status: "PASS" | "FAIL";
  frontendUrl: string;
  currentUrl: string;
  failedRequests: Array<{ url: string; status?: number; failure?: string | null; method?: string }>;
  missingExpectedApis: string[];
  consoleErrors: string[];
  criticalAccessibilityViolations: number;
  errors: string[];
};

const evidenceRoot = path.resolve(process.cwd(), "../../audit-artifacts/live-runtime-certification/current");
const summaryPath = path.join(evidenceRoot, "certification-summary.md");
const resultPath = path.join(evidenceRoot, "live-runtime-result.json");
const screenshotPath = path.join(evidenceRoot, "live-runtime-login.png");

function requireEnv(name: string): string {
  const value = process.env[name]?.trim();
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

function writeEvidence(result: LiveRuntimeResult): void {
  fs.mkdirSync(evidenceRoot, { recursive: true });
  fs.writeFileSync(resultPath, `${JSON.stringify(result, null, 2)}\n`);

  const lines = [
    "# Live Runtime Certification Summary",
    "",
    `Status: **${result.status}**`,
    "",
    `Frontend URL: ${result.frontendUrl}`,
    `Current URL after login: ${result.currentUrl}`,
    `Failed requests: ${result.failedRequests.length}`,
    `Missing expected APIs: ${result.missingExpectedApis.length}`,
    `Console errors: ${result.consoleErrors.length}`,
    `Critical/serious accessibility violations: ${result.criticalAccessibilityViolations}`,
    "",
    "## Errors",
    ...(result.errors.length ? result.errors.map((error) => `- ${error}`) : ["- None"]),
  ];
  fs.writeFileSync(summaryPath, `${lines.join("\n")}\n`);
}

test.describe.configure({ mode: "serial", retries: 0 });

test("live runtime login and auth-path certification", async ({ page }, testInfo) => {
  const frontendBase = requireEnv("CROWN_LIVE_FRONTEND_URL").replace(/\/+$/, "");
  const email = requireEnv("CROWN_LIVE_LOGIN_EMAIL");
  const password = requireEnv("CROWN_LIVE_LOGIN_PASSWORD");
  const roleLabel = process.env.CROWN_LIVE_ROLE_LABEL || "School Admin";
  const schoolLabel = process.env.CROWN_LIVE_SCHOOL_LABEL || "";

  const consoleErrors: string[] = [];
  page.on("pageerror", (error) => {
    consoleErrors.push(`[pageerror] ${error.message}`);
  });
  page.on("console", (message) => {
    if (message.type() === "error") {
      consoleErrors.push(`[console.error] ${message.text()}`);
    }
  });

  const network = attachNetworkRecorder(page, ["/api/v1/auth/token/", "/api/v1/auth/me/"]);
  await page.goto(`${frontendBase}/login`, { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: /Sign In/i })).toBeVisible();

  if (schoolLabel) {
    const schoolCombo = page.getByLabel("School");
    if (await schoolCombo.count()) {
      await schoolCombo.selectOption({ label: schoolLabel });
    }
  }

  const roleCombo = page.getByLabel("Role");
  if (await roleCombo.count()) {
    await roleCombo.selectOption({ label: roleLabel });
  }

  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: /^Sign In$/ }).click();

  await page.waitForTimeout(5000);
  const currentUrl = page.url();
  const bodyText = await page.locator("body").innerText().catch(() => "");

  const a11y = await new AxeBuilder({ page }).analyze();
  const criticalOrSeriousCount = a11y.violations.filter(
    (violation) => violation.impact === "critical" || violation.impact === "serious",
  ).length;

  await page.screenshot({ path: screenshotPath, fullPage: true });
  await testInfo.attach("live-runtime-login", { path: screenshotPath, contentType: "image/png" });

  const errors: string[] = [];
  const loginErrorPattern = /Failed to fetch|Access Restricted|You do not have permission|fix the assigned role set|Auth failed/i;
  if (loginErrorPattern.test(bodyText)) {
    errors.push("login page displayed an auth/network failure message");
  }

  if (/\/login(?:$|[?#])/.test(currentUrl)) {
    errors.push("still on /login after sign-in attempt");
  }

  if (network.failed.length > 0) {
    errors.push(`failed API/network requests: ${network.failed.length}`);
  }

  const missingExpectedApis = network.missingExpected();
  if (missingExpectedApis.length > 0) {
    errors.push(`missing expected API calls: ${missingExpectedApis.join(", ")}`);
  }

  if (consoleErrors.length > 0) {
    errors.push(`console errors: ${consoleErrors.length}`);
  }

  if (criticalOrSeriousCount > 0) {
    errors.push(`critical/serious accessibility violations: ${criticalOrSeriousCount}`);
  }

  const result: LiveRuntimeResult = {
    status: errors.length === 0 ? "PASS" : "FAIL",
    frontendUrl: frontendBase,
    currentUrl,
    failedRequests: network.failed,
    missingExpectedApis,
    consoleErrors,
    criticalAccessibilityViolations: criticalOrSeriousCount,
    errors,
  };

  writeEvidence(result);
  expect(errors, errors.join("\n")).toEqual([]);
});
