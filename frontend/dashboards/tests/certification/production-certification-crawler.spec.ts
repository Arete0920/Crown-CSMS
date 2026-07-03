import { test, expect, type Page } from "@playwright/test";
import { certificationMatrix } from "./certification-matrix";
import { certificationPersonas } from "./personas";
import { certificationTenants } from "./tenants";
import { runAccessibilityCertification } from "./accessibility";
import { collectPageBlockers } from "./assertions";
import { attachNetworkRecorder, type NetworkObservation } from "./network-recorder";
import {
  appendCertificationResult,
  loadCertificationResults,
  resetEvidenceRoot,
  screenshotPathFor,
  writeCertificationSummary,
} from "./evidence-writer";

type RoleCredential = {
  email?: string;
  password?: string;
};

const SANDBOX_ROLE_KEYS: Record<string, string> = {
  admin: "school_admin",
  teacher: "teacher",
  parent: "parent",
  student: "student",
  board: "board",
};

const SANDBOX_ROLE_CREDENTIALS: Record<string, RoleCredential> = {
  admin: { email: "admin@heritage.example.org", password: "CrownDemo!2026" },
  teacher: { email: "teacher.lower@heritage.example.org", password: "CrownDemo!2026" },
  parent: { email: "parent.reed@heritage.example.org", password: "CrownDemo!2026" },
  student: { email: "student.avery.reed11@heritage.example.org", password: "CrownDemo!2026" },
  board: { email: "board@heritage.example.org", password: "CrownDemo!2026" },
};

const SANDBOX_TENANT_SCHOOL_KEYS: Record<string, string> = {
  heritage: "heritage-core",
  harvest: "harvest-small-school",
  faith: "faith-admissions",
};

const LIVE_FRONTEND_URL = requireLiveUrl("CROWN_LIVE_FRONTEND_URL");
const LIVE_API_BASE_URL = requireLiveUrl("CROWN_LIVE_API_BASE_URL").replace(/\/+$/, "");
const USE_SANDBOX_CREDENTIAL_BUTTON = process.env.CROWN_LIVE_USE_SANDBOX_CREDENTIALS !== "0";
const LIVE_SANDBOX_INVITE_ID = resolveSandboxInviteId();

const roleValues: Record<string, string[]> = {
  admin: ["school_admin", "head_of_school", "admin"],
  teacher: ["teacher"],
  parent: ["parent"],
  student: ["student"],
  board: ["board", "head_of_school"],
};

function requireLiveUrl(name: string): string {
  const raw = process.env[name];
  if (!raw) {
    throw new Error(`${name} is required for live runtime certification.`);
  }

  const parsed = new URL(raw);
  const forbiddenHosts = new Set(["localhost", "127.0.0.1", "0.0.0.0"]);
  if (forbiddenHosts.has(parsed.hostname) || parsed.hostname.endsWith(".local")) {
    throw new Error(`${name} must target deployed runtime, not local host: ${raw}`);
  }

  return parsed.toString().replace(/\/+$/, "");
}

function credentialFor(role: string): RoleCredential {
  const key = role.toUpperCase().replace(/[^A-Z0-9]+/g, "_");
  const fallback = SANDBOX_ROLE_CREDENTIALS[role] ?? {};
  return {
    email: process.env[`CROWN_LIVE_${key}_EMAIL`] ?? process.env.CROWN_LIVE_EMAIL ?? fallback.email,
    password: process.env[`CROWN_LIVE_${key}_PASSWORD`] ?? process.env.CROWN_LIVE_PASSWORD ?? fallback.password,
  };
}

function sandboxRoleKeyFor(role: string): string {
  return SANDBOX_ROLE_KEYS[role] ?? role;
}

function sandboxSchoolKeyFor(tenant: { id: string; schoolId: string }): string {
  return SANDBOX_TENANT_SCHOOL_KEYS[tenant.id] ?? tenant.schoolId;
}

function resolveSandboxInviteId(): string {
  const envInvite = process.env.CROWN_LIVE_SANDBOX_INVITE_ID?.trim();
  if (envInvite) {
    return envInvite;
  }

  try {
    return new URL(LIVE_FRONTEND_URL).searchParams.get("invite")?.trim() ?? "";
  } catch {
    return "";
  }
}

async function primeSandboxPersona(role: string, tenant: { id: string; schoolId: string }): Promise<void> {
  const payload: Record<string, string> = {
    role: sandboxRoleKeyFor(role),
    school: sandboxSchoolKeyFor(tenant),
    guidance: "guided",
    track: "school",
  };

  if (LIVE_SANDBOX_INVITE_ID) {
    payload.invite_id = LIVE_SANDBOX_INVITE_ID;
  }

  const response = await fetch(`${LIVE_API_BASE_URL}/api/v1/sandbox/session/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const body = await response.text();
    if (response.status === 403 && body.includes("sandbox_invite_required")) {
      // Live runtime may enforce invite-only sandbox priming; fall back to direct login assertions.
      return;
    }
    throw new Error(`Sandbox session priming failed for role ${role} / tenant ${tenant.id}: ${response.status} ${body}`);
  }
}

async function bootstrapSandboxSession(
  page: Page,
  role: string,
  tenant: { id: string; schoolId: string },
): Promise<boolean> {
  const payload: Record<string, string> = {
    role: sandboxRoleKeyFor(role),
    school: sandboxSchoolKeyFor(tenant),
    guidance: "guided",
    track: "school",
  };

  if (LIVE_SANDBOX_INVITE_ID) {
    payload.invite_id = LIVE_SANDBOX_INVITE_ID;
  }

  const response = await fetch(`${LIVE_API_BASE_URL}/api/v1/sandbox/session/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    return false;
  }

  const session = await response.json();
  if (!session?.access) {
    return false;
  }

  const roleValue = sandboxRoleKeyFor(role);
  const schoolId = session.school_id ?? tenant.schoolId;
  await page.evaluate(
    ({ access, roleKey, school }) => {
      sessionStorage.setItem("crown.jwt.access", access as string);
      sessionStorage.setItem("crown.role", roleKey as string);
      sessionStorage.setItem("crown.school.id", school as string);
      localStorage.setItem("crown.role", roleKey as string);
      localStorage.setItem("crown.demo.role", roleKey as string);
      localStorage.setItem("crown.school.id", school as string);
    },
    { access: session.access, roleKey: roleValue, school: schoolId },
  );

  const route = typeof session.route === "string" && session.route
    ? session.route
    : "/school-admin-dashboard";
  await page.goto(absoluteLiveUrl(route), { waitUntil: "networkidle" });
  return true;
}

function absoluteLiveUrl(path: string): string {
  const url = new URL(path, `${LIVE_FRONTEND_URL}/`);
  if (LIVE_SANDBOX_INVITE_ID) {
    url.searchParams.set("invite", LIVE_SANDBOX_INVITE_ID);
  }
  return url.toString();
}

function isAllowedExternalFailure(url: string): boolean {
  try {
    const parsed = new URL(url);
    return parsed.pathname.includes("favicon") || parsed.hostname.endsWith("visualstudio.com");
  } catch {
    return false;
  }
}

async function selectSchool(page: Page, tenant: { schoolId: string; schoolCode: string; label: string }): Promise<void> {
  const schoolSelect = page.locator("#login-school");
  if (!(await schoolSelect.isVisible({ timeout: 10_000 }).catch(() => false))) {
    return;
  }

  const selectedValue = await schoolSelect.evaluate((select, target) => {
    const options = Array.from((select as HTMLSelectElement).options);
    const match = options.find((option) => (
      option.value === target.schoolId
      || option.value === target.schoolCode
      || option.textContent?.toLowerCase().includes(target.label.toLowerCase())
      || option.textContent?.toLowerCase().includes(target.schoolCode.toLowerCase())
    ));
    return match?.value ?? null;
  }, tenant);

  if (!selectedValue) {
    throw new Error(`Live login school option not found for tenant ${tenant.label}`);
  }

  await schoolSelect.selectOption(selectedValue);
}

async function selectRole(page: Page, role: string): Promise<void> {
  const roleSelect = page.locator("#login-role");
  await expect(roleSelect).toBeVisible();

  const selectedValue = await roleSelect.evaluate((select, candidates) => {
    const options = Array.from((select as HTMLSelectElement).options);
    const values = candidates as string[];
    const match = options.find((option) => values.includes(option.value));
    return match?.value ?? null;
  }, roleValues[role] ?? [role]);

  if (!selectedValue) {
    throw new Error(`Live login role option not found for role ${role}`);
  }

  await roleSelect.selectOption(selectedValue);
}

async function performLiveLogin(page: Page, role: string, tenant: { schoolId: string; schoolCode: string; label: string }): Promise<void> {
  if (USE_SANDBOX_CREDENTIAL_BUTTON) {
    await primeSandboxPersona(role, tenant);

    // Prefer direct sandbox session bootstrap when the live runtime exposes invite/session flows.
    const sessionBootstrapped = await bootstrapSandboxSession(page, role, tenant);
    if (sessionBootstrapped) {
      return;
    }
  }

  await page.goto(absoluteLiveUrl("/login"), { waitUntil: "domcontentloaded" });
  await selectSchool(page, tenant);
  await selectRole(page, role);

  const credential = credentialFor(role);
  const sandboxButton = page.getByRole("button", { name: /use sandbox credentials/i });
  const canUseSandboxButton = USE_SANDBOX_CREDENTIAL_BUTTON
    && await sandboxButton.isVisible({ timeout: 2_000 }).catch(() => false);

  if (canUseSandboxButton) {
    await sandboxButton.click();
  }

  if (credential.email) {
    await page.locator("#login-email").fill(credential.email);
  }

  if (credential.password) {
    await page.locator("#login-password").fill(credential.password);
  }

  const emailValue = await page.locator("#login-email").inputValue().catch(() => "");
  const passwordValue = await page.locator("#login-password").inputValue().catch(() => "");

  if (!emailValue || !passwordValue) {
    throw new Error(`No live credentials available for role ${role}. Configure CROWN_LIVE_${role.toUpperCase()}_EMAIL/PASSWORD or enable the live sandbox credential button.`);
  }

  await page.getByRole("button", { name: /^sign in$/i }).click();
  await page.waitForLoadState("networkidle", { timeout: 20_000 }).catch(() => undefined);

  const alert = page.locator("[role='alert'], .error-banner").first();
  if (await alert.isVisible({ timeout: 2_000 }).catch(() => false)) {
    const loginError = await alert.innerText();
    const sessionBootstrapped = await bootstrapSandboxSession(page, role, tenant);
    if (!sessionBootstrapped) {
      throw new Error(`Live login failed for role ${role}: ${loginError}`);
    }
    return;
  }

  await expect(page.locator("body")).toBeVisible();
}

test.describe.configure({ mode: "serial", retries: 0 });

test.beforeAll(() => {
  resetEvidenceRoot();
});

test.afterAll(() => {
  writeCertificationSummary();

  const failed = loadCertificationResults().filter((row) => row.status === "FAIL");
  const details = failed.map((row) => `${row.id} / ${row.persona} / ${row.tenant}: ${row.errors.join("; ")}`);
  expect(failed, details.join("\n")).toEqual([]);
});

for (const surface of certificationMatrix) {
  for (const personaId of surface.personas) {
    for (const tenantId of surface.tenants) {
      const persona = certificationPersonas.find((candidate) => candidate.id === personaId);
      const tenant = certificationTenants.find((candidate) => candidate.id === tenantId);

      if (!persona) {
        throw new Error(`Unknown certification persona: ${personaId}`);
      }

      if (!tenant) {
        throw new Error(`Unknown certification tenant: ${tenantId}`);
      }

      test(`${surface.id} / ${persona.id} / ${tenant.id}`, async ({ page }, testInfo) => {
        const consoleErrors: string[] = [];
        const nonApiFailedRequests: NetworkObservation[] = [];

        page.on("pageerror", (error) => {
          consoleErrors.push(`[pageerror] ${error.message}`);
        });

        page.on("console", (message) => {
          if (message.type() === "error") {
            consoleErrors.push(`[console.error] ${message.text()}`);
          }
        });

        page.on("requestfailed", (request) => {
          const url = request.url();
          if (url.includes("/api/") || isAllowedExternalFailure(url)) {
            return;
          }
          nonApiFailedRequests.push({
            url,
            method: request.method(),
            failure: request.failure()?.errorText ?? "request failed",
          });
        });

        const expectedFragments = [
          LIVE_API_BASE_URL,
          ...(surface.expectedApiFragments ?? []),
        ];
        const network = attachNetworkRecorder(page, expectedFragments);
        const errors: string[] = [];

        try {
          await performLiveLogin(page, persona.role, tenant);
          await page.goto(absoluteLiveUrl(surface.route), { waitUntil: "networkidle" });
          await expect(page.locator("body")).toBeVisible();
        } catch (error) {
          errors.push(error instanceof Error ? error.message : String(error));
        }

        const accessibility = await runAccessibilityCertification(page);
        const screenshotPath = screenshotPathFor(surface.id, persona.id, tenant.id);
        await page.screenshot({ path: screenshotPath, fullPage: true });
        await testInfo.attach("certification-screenshot", { path: screenshotPath, contentType: "image/png" });

        const pageErrors = await collectPageBlockers(
          page,
          network,
          accessibility,
          surface.expectedText ?? [],
          false,
        );
        errors.push(...pageErrors);

        if (!(surface.allowConsoleErrors ?? false) && consoleErrors.length > 0) {
          errors.push(`console errors: ${consoleErrors.length}`);
        }

        if (nonApiFailedRequests.length > 0) {
          errors.push(`failed non-API network requests: ${nonApiFailedRequests.length}`);
        }

        const missingExpectedApis = network.missingExpected();
        const failedRequests = [...network.failed, ...nonApiFailedRequests];

        appendCertificationResult({
          id: surface.id,
          label: surface.label,
          kind: surface.kind,
          route: surface.route,
          persona: persona.id,
          tenant: tenant.id,
          status: errors.length === 0 ? "PASS" : "FAIL",
          errors,
          screenshotPath,
          networkObserved: network.observed.length,
          networkFailed: failedRequests.length,
          failedRequests,
          consoleErrors,
          missingExpectedApis,
          accessibilityViolationDetails: accessibility.violations,
          accessibilityViolations: accessibility.violationCount,
          criticalAccessibilityViolations: accessibility.criticalOrSeriousCount,
        });
      });
    }
  }
}
