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

type CertificationTenant = {
  id: string;
  schoolKey: string;
  schoolId: string;
  label: string;
};

type AuthMode = "credentials" | "sandbox-session" | "sandbox-no-login";

type BrowserAuthState = {
  hasToken: boolean;
  hasSchoolId: boolean;
  token: string;
  schoolId: string;
  tokenSources: string[];
  schoolIdSources: string[];
};

type ApiProbeResult = {
  ok: boolean;
  status: number;
  url: string;
  code: string;
  hasAuthorizationHeader: boolean;
  hasSchoolIdHeader: boolean;
};

const SANDBOX_ROLE_KEYS: Record<string, string> = {
  admin: "school_admin",
  teacher: "teacher",
  parent: "parent",
  student: "student",
  board: "board",
};

const SANDBOX_NO_LOGIN_ROUTES: Record<string, string> = {
  admin: "/school-admin-dashboard",
  teacher: "/teacher",
  parent: "/parent",
  student: "/student",
  board: "/board",
};

const DASHBOARD_SUMMARY_SLUGS: Record<string, string> = {
  admin: "school-administrator",
  teacher: "teacher",
  parent: "parent",
  student: "student",
  board: "school-board",
};

const CERTIFICATION_TENANT_MODE = (process.env.CROWN_CERTIFICATION_TENANT_MODE || "sandbox").trim().toLowerCase();
const USES_SANDBOX_TENANT = CERTIFICATION_TENANT_MODE !== "live";
const HERITAGE_SCHOOL_UUID = (
  USES_SANDBOX_TENANT
    ? process.env.CROWN_DEMO_SCHOOL_ID
    : process.env.CROWN_LIVE_SCHOOL_ID)
  || process.env.CROWN_DEMO_SCHOOL_ID
  || "19801b59-8c05-4c84-9312-5d792e4e839d";

const AUTH_API = ["/api/v1/auth/token", "/api/v1/auth/me"];

const LIVE_FRONTEND_URL = requireLiveUrl("CROWN_LIVE_FRONTEND_URL");
const LIVE_API_BASE_URL = requireLiveUrl("CROWN_LIVE_API_BASE_URL").replace(/\/+$/, "");
const IS_PRODUCTION_API = isProductionApiHost(LIVE_API_BASE_URL);
const USE_SANDBOX_CREDENTIAL_BUTTON = process.env.CROWN_LIVE_USE_SANDBOX_CREDENTIALS !== "0";
const LIVE_SANDBOX_INVITE_ID = resolveSandboxInviteId();

assertLiveSchoolIdConfiguration();

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

function assertLiveSchoolIdConfiguration(): void {
  if (!IS_PRODUCTION_API) {
    return;
  }

  if (USES_SANDBOX_TENANT) {
    const demoSchoolId = process.env.CROWN_DEMO_SCHOOL_ID?.trim() || HERITAGE_SCHOOL_UUID;
    if (demoSchoolId) {
      return;
    }
  }

  const liveSchoolId = process.env.CROWN_LIVE_SCHOOL_ID?.trim();
  if (liveSchoolId) {
    return;
  }

  throw new Error(
    "CROWN_LIVE_SCHOOL_ID is required for live production tenant certification. "
    + "For investor/demo certification use CROWN_CERTIFICATION_TENANT_MODE=sandbox and CROWN_DEMO_SCHOOL_ID.",
  );
}

function isProductionApiHost(url: string): boolean {
  const host = new URL(url).hostname.toLowerCase();
  return host.includes("crown-api-prod") || host.includes("prod");
}

function credentialFor(role: string): RoleCredential {
  const key = role.toUpperCase().replace(/[^A-Z0-9]+/g, "_");
  return {
    email: process.env[`CROWN_LIVE_${key}_EMAIL`] ?? process.env.CROWN_LIVE_EMAIL,
    password: process.env[`CROWN_LIVE_${key}_PASSWORD`] ?? process.env.CROWN_LIVE_PASSWORD,
  };
}

function sandboxRoleKeyFor(role: string): string {
  return SANDBOX_ROLE_KEYS[role] ?? role;
}

function sandboxSchoolKeyFor(tenant: CertificationTenant): string {
  return tenant.schoolKey;
}

function dashboardSummarySlugFor(role: string): string {
  return DASHBOARD_SUMMARY_SLUGS[role] ?? role;
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

async function primeSandboxPersona(role: string, tenant: CertificationTenant): Promise<void> {
  const payload: Record<string, string> = {
    role: sandboxRoleKeyFor(role),
    school: sandboxSchoolKeyFor(tenant),
    guidance: "guided",
    track: "school",
  };

  if (LIVE_SANDBOX_INVITE_ID) {
    payload.invite_id = LIVE_SANDBOX_INVITE_ID;
  }

  const response = await globalThis.fetch(`${LIVE_API_BASE_URL}/api/v1/sandbox/session/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const body = await response.text();
    if (response.status === 403 && body.includes("sandbox_invite_required")) {
      if (IS_PRODUCTION_API && USES_SANDBOX_TENANT) {
        throw new Error(
          "Live sandbox session requires CROWN_LIVE_SANDBOX_INVITE_ID. "
          + "Investor demo must use an invite-backed Heritage sandbox session, not GP School or password login.",
        );
      }
      return;
    }
    throw new Error(`Sandbox session priming failed for role ${role} / tenant ${tenant.id}: ${response.status} ${body}`);
  }
}

async function bootstrapSandboxSession(
  page: Page,
  role: string,
  tenant: CertificationTenant,
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

  const response = await globalThis.fetch(`${LIVE_API_BASE_URL}/api/v1/sandbox/session/`, {
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
  const schoolId = typeof session.school_id === "string" && session.school_id ? session.school_id : tenant.schoolId;
  await seedClientAuthStorage(page, roleValue, schoolId, session.access);

  const route = typeof session.route === "string" && session.route
    ? session.route
    : "/school-admin-dashboard";
  await page.goto(absoluteLiveUrl(route), { waitUntil: "networkidle" });
  return true;
}

async function bootstrapSandboxNoLogin(
  page: Page,
  role: string,
  tenant: CertificationTenant,
): Promise<boolean> {
  const route = SANDBOX_NO_LOGIN_ROUTES[role];
  if (!route) {
    return false;
  }

  await page.goto(absoluteLiveUrl("/login"), { waitUntil: "domcontentloaded" });
  await seedClientAuthStorage(page, sandboxRoleKeyFor(role), tenant.schoolId);

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

async function seedClientAuthStorage(
  page: Page,
  roleKey: string,
  schoolId: string,
  accessToken?: string,
): Promise<void> {
  await page.addInitScript(
    ({ role, school, access }) => {
      const currentUser = JSON.stringify({
        role,
        school_id: school,
        schoolId: school,
        token: access || "",
        access: access || "",
        access_token: access || "",
      });

      try {
        if (access) {
          sessionStorage.setItem("crown.jwt.access", access);
          sessionStorage.setItem("crown_auth_token", access);
          sessionStorage.setItem("access_token", access);
        }
        sessionStorage.setItem("crown.role", role);
        sessionStorage.setItem("crown.demo.role", role);
        sessionStorage.setItem("crown.school.id", school);
        sessionStorage.setItem("crown_school_id", school);
        sessionStorage.setItem("schoolId", school);
        sessionStorage.setItem("school_id", school);
        sessionStorage.setItem("crown_current_user", currentUser);
      } catch {
        // Storage APIs can be blocked on transient opaque documents.
      }

      try {
        if (access) {
          localStorage.setItem("crown.jwt.access", access);
          localStorage.setItem("crown_auth_token", access);
          localStorage.setItem("access_token", access);
        }
        localStorage.setItem("crown.role", role);
        localStorage.setItem("crown.demo.role", role);
        localStorage.setItem("crown.school.id", school);
        localStorage.setItem("crown_school_id", school);
        localStorage.setItem("schoolId", school);
        localStorage.setItem("school_id", school);
        localStorage.setItem("crown_current_user", currentUser);
      } catch {
        // Storage unavailability will surface later via runtime blocker assertions.
      }

      try {
        (globalThis as { __CROWN_SCHOOL_ID__?: string; __CROWN_AUTH_TOKEN__?: string }).__CROWN_SCHOOL_ID__ = school;
        if (access) {
          (globalThis as { __CROWN_AUTH_TOKEN__?: string }).__CROWN_AUTH_TOKEN__ = access;
        }
      } catch {
        // Non-fatal.
      }
    },
    { role: roleKey, school: schoolId, access: accessToken },
  );
}

async function readBrowserAuthState(page: Page): Promise<BrowserAuthState> {
  return page.evaluate(() => {
    const tokenCandidates = [
      ["session:crown.jwt.access", sessionStorage.getItem("crown.jwt.access") || ""],
      ["session:crown_auth_token", sessionStorage.getItem("crown_auth_token") || ""],
      ["session:access_token", sessionStorage.getItem("access_token") || ""],
      ["local:crown.jwt.access", localStorage.getItem("crown.jwt.access") || ""],
      ["local:crown_auth_token", localStorage.getItem("crown_auth_token") || ""],
      ["local:access_token", localStorage.getItem("access_token") || ""],
      ["global:__CROWN_AUTH_TOKEN__", (globalThis as { __CROWN_AUTH_TOKEN__?: string }).__CROWN_AUTH_TOKEN__ || ""],
    ];
    const schoolCandidates = [
      ["session:crown.school.id", sessionStorage.getItem("crown.school.id") || ""],
      ["session:crown_school_id", sessionStorage.getItem("crown_school_id") || ""],
      ["session:schoolId", sessionStorage.getItem("schoolId") || ""],
      ["session:school_id", sessionStorage.getItem("school_id") || ""],
      ["local:crown.school.id", localStorage.getItem("crown.school.id") || ""],
      ["local:crown_school_id", localStorage.getItem("crown_school_id") || ""],
      ["local:schoolId", localStorage.getItem("schoolId") || ""],
      ["local:school_id", localStorage.getItem("school_id") || ""],
      ["global:__CROWN_SCHOOL_ID__", (globalThis as { __CROWN_SCHOOL_ID__?: string }).__CROWN_SCHOOL_ID__ || ""],
    ];

    const currentUserRaw = sessionStorage.getItem("crown_current_user") || localStorage.getItem("crown_current_user") || "";
    if (currentUserRaw) {
      try {
        const currentUser = JSON.parse(currentUserRaw);
        tokenCandidates.push(["crown_current_user.token", currentUser.token || currentUser.access || currentUser.access_token || ""]);
        schoolCandidates.push(["crown_current_user.school_id", currentUser.school_id || currentUser.schoolId || ""]);
      } catch {
        // Ignore malformed legacy user payloads.
      }
    }

    const tokenEntry = tokenCandidates.find(([, value]) => Boolean(value));
    const schoolEntry = schoolCandidates.find(([, value]) => Boolean(value));

    return {
      hasToken: Boolean(tokenEntry?.[1]),
      hasSchoolId: Boolean(schoolEntry?.[1]),
      token: tokenEntry?.[1] || "",
      schoolId: schoolEntry?.[1] || "",
      tokenSources: tokenCandidates.filter(([, value]) => Boolean(value)).map(([source]) => source),
      schoolIdSources: schoolCandidates.filter(([, value]) => Boolean(value)).map(([source]) => source),
    };
  });
}

async function probeApiFromBrowser(
  page: Page,
  url: string,
  token: string,
  schoolId: string,
): Promise<ApiProbeResult> {
  return page.evaluate(async ({ targetUrl, accessToken, school }) => {
    const headers: Record<string, string> = {
      Accept: "application/json",
    };
    if (accessToken) {
      headers.Authorization = `Bearer ${accessToken}`;
    }
    if (school) {
      headers["X-School-Id"] = school;
    }

    try {
      const response = await fetch(targetUrl, {
        method: "GET",
        credentials: "include",
        headers,
      });
      return {
        ok: response.ok,
        status: response.status,
        url: targetUrl,
        code: response.ok ? "OK" : `HTTP_${response.status}`,
        hasAuthorizationHeader: Boolean(accessToken),
        hasSchoolIdHeader: Boolean(school),
      };
    } catch (error) {
      return {
        ok: false,
        status: 0,
        url: targetUrl,
        code: error instanceof Error ? error.message : "FETCH_FAILED",
        hasAuthorizationHeader: Boolean(accessToken),
        hasSchoolIdHeader: Boolean(school),
      };
    }
  }, { targetUrl: url, accessToken: token, school: schoolId });
}

function classifyProbe(name: string, probe: ApiProbeResult): string | null {
  if (probe.ok) {
    return null;
  }

  if (!probe.hasAuthorizationHeader) {
    return `AUTH_PREFLIGHT_${name}: TOKEN_NOT_SEEDED url=${probe.url}`;
  }

  if (!probe.hasSchoolIdHeader) {
    return `AUTH_PREFLIGHT_${name}: SCHOOL_ID_NOT_SEEDED url=${probe.url}`;
  }

  if (probe.status === 401) {
    return `AUTH_PREFLIGHT_${name}: API_401_WITH_TOKEN_AND_SCHOOL_ID url=${probe.url}`;
  }

  if (probe.status === 403) {
    return `AUTH_PREFLIGHT_${name}: API_403_WITH_TOKEN_AND_SCHOOL_ID url=${probe.url}`;
  }

  if (probe.status === 404) {
    return `AUTH_PREFLIGHT_${name}: API_404_MISSING_ROUTE url=${probe.url}`;
  }

  if (probe.status >= 500) {
    return `AUTH_PREFLIGHT_${name}: API_${probe.status}_SERVER_ERROR url=${probe.url}`;
  }

  return `AUTH_PREFLIGHT_${name}: ${probe.code} status=${probe.status} url=${probe.url}`;
}

async function runAuthPreflight(page: Page, role: string, tenant: CertificationTenant): Promise<string[]> {
  const authState = await readBrowserAuthState(page);
  const errors: string[] = [];

  if (!authState.hasToken) {
    errors.push(`AUTH_PREFLIGHT: TOKEN_NOT_SEEDED role=${role} tenant=${tenant.id}`);
  }

  if (!authState.hasSchoolId) {
    errors.push(`AUTH_PREFLIGHT: SCHOOL_ID_NOT_SEEDED role=${role} tenant=${tenant.id}`);
  }

  if (errors.length > 0) {
    return errors;
  }

  const summarySlug = dashboardSummarySlugFor(role);
  const summaryUrl = `${LIVE_API_BASE_URL}/api/v1/dashboards/${summarySlug}/summary`;
  const navUrl = `${LIVE_API_BASE_URL}/api/v1/nav`;

  const summaryProbe = await probeApiFromBrowser(page, summaryUrl, authState.token, authState.schoolId);
  const navProbe = await probeApiFromBrowser(page, navUrl, authState.token, authState.schoolId);

  const summaryError = classifyProbe("DASHBOARD_SUMMARY", summaryProbe);
  const navError = classifyProbe("NAV", navProbe);

  if (summaryError) {
    errors.push(`${summaryError} role=${role} tenant=${tenant.id} tokenSources=${authState.tokenSources.join("+")} schoolIdSources=${authState.schoolIdSources.join("+")}`);
  }

  if (navError) {
    errors.push(`${navError} role=${role} tenant=${tenant.id} tokenSources=${authState.tokenSources.join("+")} schoolIdSources=${authState.schoolIdSources.join("+")}`);
  }

  return errors;
}

function isAllowedExternalFailure(url: string): boolean {
  try {
    const parsed = new URL(url);
    return parsed.pathname.includes("favicon") || parsed.hostname.endsWith("visualstudio.com");
  } catch {
    return false;
  }
}

function isNoisyConsoleError(message: string): boolean {
  return /Failed to load resource: the server responded with a status of 404/.test(message);
}

function dedupeFailedRequests(rows: NetworkObservation[]): NetworkObservation[] {
  const byKey = new Map<string, NetworkObservation>();
  for (const row of rows) {
    const key = [row.method ?? "", row.url, row.status ?? "", row.failure ?? ""].join("|");
    if (!byKey.has(key)) {
      byKey.set(key, row);
    }
  }
  return [...byKey.values()];
}

async function selectSchool(page: Page, tenant: CertificationTenant): Promise<void> {
  const schoolSelect = page.locator("#login-school");
  if (!(await schoolSelect.isVisible({ timeout: 10_000 }).catch(() => false))) {
    return;
  }

  const selectedValue = await schoolSelect.evaluate((select, target) => {
    const options = Array.from((select as HTMLSelectElement).options);
    const match = options.find((option) => (
      option.value === target.schoolId
      || option.value === target.schoolKey
      || option.textContent?.toLowerCase().includes(target.label.toLowerCase())
      || option.textContent?.toLowerCase().includes(target.schoolKey.toLowerCase())
    ));
    return match?.value ?? null;
  }, tenant);

  if (!selectedValue) {
    const availableOptions = await schoolSelect.evaluate((select) => (
      Array.from((select as HTMLSelectElement).options).map((option) => ({
        value: option.value,
        label: option.textContent?.trim() ?? "",
      }))
    ));
    throw new Error(
      `Live login school option not found for tenant ${tenant.label}. `
      + `Available options: ${JSON.stringify(availableOptions)}`,
    );
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

async function performLiveLogin(page: Page, role: string, tenant: CertificationTenant): Promise<AuthMode> {
  if (USE_SANDBOX_CREDENTIAL_BUTTON) {
    await primeSandboxPersona(role, tenant);

    // Prefer direct sandbox session bootstrap when the live runtime exposes invite/session flows.
    const sessionBootstrapped = await bootstrapSandboxSession(page, role, tenant);
    if (sessionBootstrapped) {
      return "sandbox-session";
    }

    if (!IS_PRODUCTION_API) {
      const noLoginBootstrapped = await bootstrapSandboxNoLogin(page, role, tenant);
      if (noLoginBootstrapped) {
        return "sandbox-no-login";
      }
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
    throw new Error(`No live credentials available for role ${role}. Configure CROWN_LIVE_${role.toUpperCase()}_EMAIL/PASSWORD or provide a working live sandbox credential button/invite.`);
  }

  await page.getByRole("button", { name: /^sign in$/i }).click();
  await page.waitForLoadState("networkidle", { timeout: 20_000 }).catch(() => undefined);

  const alert = page.locator("[role='alert'], .error-banner").first();
  if (await alert.isVisible({ timeout: 2_000 }).catch(() => false)) {
    const loginError = await alert.innerText();
    const sessionBootstrapped = await bootstrapSandboxSession(page, role, tenant);
    if (!sessionBootstrapped) {
      if (IS_PRODUCTION_API) {
        throw new Error(
          `Live auth bootstrap failed for role ${role}: ${loginError}. `
          + "Production certification requires live credentials or sandbox session access token; sandbox-no-login fallback is disabled.",
        );
      }
      const noLoginBootstrapped = await bootstrapSandboxNoLogin(page, role, tenant);
      if (!noLoginBootstrapped) {
        throw new Error(`Live login failed for role ${role}: ${loginError}`);
      }
      return "sandbox-no-login";
    }
    return "sandbox-session";
  }

  const accessToken = await page.evaluate(() => (
    sessionStorage.getItem("crown.jwt.access")
    || sessionStorage.getItem("crown_auth_token")
    || sessionStorage.getItem("access_token")
    || localStorage.getItem("crown.jwt.access")
    || localStorage.getItem("crown_auth_token")
    || localStorage.getItem("access_token")
    || (globalThis as { __CROWN_AUTH_TOKEN__?: string }).__CROWN_AUTH_TOKEN__
    || ""
  )).catch(() => "");
  if (!accessToken) {
    const sessionBootstrapped = await bootstrapSandboxSession(page, role, tenant);
    if (sessionBootstrapped) {
      return "sandbox-session";
    }
    if (IS_PRODUCTION_API) {
      throw new Error(
        `Live auth bootstrap failed for role ${role}: login completed without crown.jwt.access token. `
        + "Production certification requires a valid live token or sandbox session access token.",
      );
    }
    const noLoginBootstrapped = await bootstrapSandboxNoLogin(page, role, tenant);
    if (noLoginBootstrapped) {
      return "sandbox-no-login";
    }
    throw new Error(`Live login failed for role ${role}: login completed without token.`);
  }

  await expect(page.locator("body")).toBeVisible();
  return "credentials";
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
      const tenantSeed = certificationTenants.find((candidate) => candidate.id === tenantId);

      if (!persona) {
        throw new Error(`Unknown certification persona: ${personaId}`);
      }

      if (!tenantSeed) {
        throw new Error(`Unknown certification tenant: ${tenantId}`);
      }

      const tenant: CertificationTenant = tenantSeed.id === "heritage"
        ? { ...tenantSeed, schoolId: HERITAGE_SCHOOL_UUID }
        : tenantSeed;

      test(`${surface.id} / ${persona.id} / ${tenant.id}`, async ({ page }, testInfo) => {
        const consoleErrors: string[] = [];
        const nonApiFailedRequests: NetworkObservation[] = [];
        let authMode: AuthMode = "credentials";

        page.on("pageerror", (error) => {
          consoleErrors.push(`[pageerror] ${error.message}`);
        });

        page.on("console", (message) => {
          if (message.type() === "error") {
            const text = message.text();
            if (!isNoisyConsoleError(text)) {
              consoleErrors.push(`[console.error] ${text}`);
            }
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

        const expectedFragments = [...(surface.expectedApiFragments ?? [])];
        const network = attachNetworkRecorder(page, expectedFragments);
        const errors: string[] = [];
        let shouldCollectPageBlockers = true;

        try {
          authMode = await performLiveLogin(page, persona.role, tenant);
          const preflightErrors = await runAuthPreflight(page, persona.role, tenant);
          if (preflightErrors.length > 0) {
            errors.push(...preflightErrors);
            shouldCollectPageBlockers = false;
          } else {
            await page.goto(absoluteLiveUrl(surface.route), { waitUntil: "networkidle" });
            await expect(page.locator("body")).toBeVisible();
          }
        } catch (error) {
          errors.push(error instanceof Error ? messageForError(error) : String(error));
        }

        const accessibility = await runAccessibilityCertification(page);
        const screenshotPath = screenshotPathFor(surface.id, persona.id, tenant.id);
        await page.screenshot({ path: screenshotPath, fullPage: true });
        await testInfo.attach("certification-screenshot", { path: screenshotPath, contentType: "image/png" });

        let pageErrors: string[] = [];
        if (shouldCollectPageBlockers) {
          try {
            pageErrors = await collectPageBlockers(
              page,
              network,
              accessibility,
              surface.expectedText ?? [],
              false,
            );
          } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            pageErrors = [`page blocker collection failed: ${message}`];
          }
        }
        const ignoredMissingApis = authMode === "credentials" ? [] : AUTH_API;
        const filteredMissingExpectedApis = network.missingExpected().filter(
          (fragment) => !ignoredMissingApis.includes(fragment),
        );
        const filteredPageErrors = pageErrors.filter(
          (error) => !error.startsWith("missing expected API calls:"),
        );
        if (filteredMissingExpectedApis.length > 0 && shouldCollectPageBlockers) {
          filteredPageErrors.push(`missing expected API calls: ${filteredMissingExpectedApis.join(", ")}`);
        }
        errors.push(...filteredPageErrors);

        if (!(surface.allowConsoleErrors ?? false) && consoleErrors.length > 0) {
          errors.push(`console errors: ${consoleErrors.length}`);
        }

        if (nonApiFailedRequests.length > 0) {
          errors.push(`failed non-API network requests: ${nonApiFailedRequests.length}`);
        }

        const missingExpectedApis = shouldCollectPageBlockers
          ? network.missingExpected().filter((fragment) => !(authMode !== "credentials" && AUTH_API.includes(fragment)))
          : [];
        const failedRequests = dedupeFailedRequests([...network.failed, ...nonApiFailedRequests]);

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

function messageForError(error: Error): string {
  return error.message || String(error);
}
