import { test, expect, type Page } from "@playwright/test";
import { certificationMatrix } from "./certification-matrix";
import { certificationPersonas } from "./personas";
import { certificationTenants } from "./tenants";
import { runAccessibilityCertification } from "./accessibility";
import { collectPageBlockers } from "./assertions";
import { attachNetworkRecorder } from "./network-recorder";
import {
  appendCertificationResult,
  loadCertificationResults,
  resetEvidenceRoot,
  screenshotPathFor,
  writeCertificationSummary,
} from "./evidence-writer";

type SandboxSession = {
  access: string;
  refresh?: string;
  school_id: string;
  school_name?: string;
  role: string;
  currentUser: {
    email: string;
    username: string;
    role: string;
    roles: string[];
    school_id: string;
    schoolId: string;
    token: string;
  };
};

const IGNORED_CONSOLE_PATTERNS = [
  /net::ERR_/,
  /Failed to fetch/,
  /Failed to load resource/,
  /favicon/i,
  /ResizeObserver loop/,
];

function mapCertificationRoleToSandboxRole(role: string): string {
  switch (role) {
    case "admin":
      return "school_admin";
    case "teacher":
      return "teacher";
    case "parent":
      return "parent";
    case "student":
      return "student";
    case "board":
      return "board";
    default:
      throw new Error(`Unsupported certification role: ${role}`);
  }
}

async function createSandboxSession(_page: Page, role: string, schoolId: string): Promise<SandboxSession> {
  return {
    access: `cert-${role}-access-token`,
    refresh: "",
    school_id: schoolId,
    school_name: "Certification Demo School",
    role,
    currentUser: {
      email: `cert-${role}@example.local`,
      username: `cert-${role}`,
      role,
      roles: [role],
      school_id: schoolId,
      schoolId,
      token: `cert-${role}-token`,
    },
  };
}

async function installCertificationApiStubs(page: Page, role: string, schoolId: string): Promise<void> {
  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;

    if (path === "/api/v1/nav/") {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          groups: [
            {
              title: "Navigation",
              items: [
                { label: "Administration", href: "/admin" },
                { label: "Teacher", href: "/teacher" },
                { label: "Parent", href: "/parent" },
                { label: "Student", href: "/student" },
                { label: "Wizards", href: "/wizards" },
              ],
            },
          ],
        }),
      });
    }

    if (path === "/api/v1/wizards/") {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ wizards: [] }),
      });
    }

    if (path === "/api/v1/auth/me/" || path === "/api/auth/me/") {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          email: `cert-${role}@example.local`,
          username: `cert-${role}`,
          role,
          roles: [role],
          school_id: schoolId,
          schoolId,
        }),
      });
    }

    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ ok: true }),
    });
  });
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
        page.on("pageerror", (error) => {
          consoleErrors.push(`[pageerror] ${error.message}`);
        });
        page.on("console", (message) => {
          if (message.type() === "error") {
            const text = message.text();
            if (IGNORED_CONSOLE_PATTERNS.some((pattern) => pattern.test(text))) {
              return;
            }
            consoleErrors.push(`[console.error] ${text}`);
          }
        });

        const sandboxRole = mapCertificationRoleToSandboxRole(persona.role);
        const session = await createSandboxSession(page, sandboxRole, tenant.schoolId);
        await installCertificationApiStubs(page, sandboxRole, tenant.schoolId);
        await page.addInitScript((sessionData) => {
          sessionStorage.setItem("crown.jwt.access", sessionData.access);
          sessionStorage.setItem("crown.jwt.refresh", sessionData.refresh || "");
          sessionStorage.setItem("crown.school.id", sessionData.school_id);
          sessionStorage.setItem("crown.school.name", sessionData.school_name || "");
          sessionStorage.setItem("crown.role", sessionData.role);
          sessionStorage.setItem("crown.active.role", sessionData.role);
          sessionStorage.setItem("crown_user", JSON.stringify(sessionData.currentUser));
          sessionStorage.setItem("crown_current_user", JSON.stringify(sessionData.currentUser));
          sessionStorage.setItem("crown_user_roles", JSON.stringify(sessionData.currentUser.roles));

          localStorage.setItem("crown.jwt.access", sessionData.access);
          localStorage.setItem("crown.school.id", sessionData.school_id);
          localStorage.setItem("crown.role", sessionData.role);
          localStorage.setItem("crown_user", JSON.stringify(sessionData.currentUser));
          localStorage.setItem("crown_current_user", JSON.stringify(sessionData.currentUser));
          localStorage.setItem("crown_user_roles", JSON.stringify(sessionData.currentUser.roles));
        }, session);

        const network = attachNetworkRecorder(page, surface.expectedApiFragments ?? []);
        const target = surface.route;

        await page.goto(target, { waitUntil: "networkidle" });
        await expect(page.locator("body")).toBeVisible();

        const accessibility = await runAccessibilityCertification(page);
        const screenshotPath = screenshotPathFor(surface.id, persona.id, tenant.id);
        await page.screenshot({ path: screenshotPath, fullPage: true });
        await testInfo.attach("certification-screenshot", { path: screenshotPath, contentType: "image/png" });

        const missingExpectedApis = network.missingExpected();
        const errors = await collectPageBlockers(
          page,
          network,
          accessibility,
          surface.expectedText ?? [],
          surface.allowFailedRequests ?? false,
        );

        if (!(surface.allowConsoleErrors ?? false) && consoleErrors.length > 0) {
          errors.push(`console errors: ${consoleErrors.length}`);
        }

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
          networkFailed: network.failed.length,
          failedRequests: network.failed,
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
