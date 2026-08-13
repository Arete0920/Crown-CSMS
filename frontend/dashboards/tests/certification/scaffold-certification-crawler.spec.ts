import { test, expect, type Page } from "@playwright/test";
import { certificationMatrix } from "./certification-matrix";
import { certificationPersonas } from "./personas";
import { certificationTenants } from "./tenants";
import { runAccessibilityCertification } from "./accessibility";
import { collectPageBlockers } from "./assertions";
import { attachNetworkRecorder } from "./network-recorder";
import { WIZARD_MANIFEST } from "../../src/routes/wizard-manifest.js";
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

const SCAFFOLD_AUTH_API = new Set([
  "/api/v1/auth/token",
  "/api/v1/auth/me",
]);

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
    school_name: "Heritage Christian Academy",
    role,
    currentUser: {
      email: `cert-${role}@heritage.example.org`,
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
        body: JSON.stringify({
          wizards: WIZARD_MANIFEST.map(({ slug, title }) => ({
            key: slug.replace(/-/g, "_"),
            slug,
            title,
            enabled: true,
          })),
          meta: { served_from: "scaffold" },
        }),
      });
    }

    if (path === "/api/dashboards/summary/") {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          widgets: [],
          generated_at: "2026-08-12T00:00:00Z",
          meta: { served_from: "scaffold" },
        }),
      });
    }

    if (path === "/api/v1/sandbox/parent/daily/") {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          child: {
            id: "11111111-1111-4111-8111-111111111111",
            student_number: "S1001",
            name: "Jordan Crown",
            grade: "7",
          },
          attendance: [],
          progress: [],
          communications: [],
          billing: {
            balance_cents: 0,
            external_payment_provider_enabled: false,
          },
          staff_controls: {
            grade_write: false,
            attendance_write: false,
            admissions_decision: false,
            finance_admin: false,
            tenant_admin: false,
          },
          meta: { served_from: "scaffold" },
        }),
      });
    }

    if (path === "/api/v1/sandbox/student/self-service/") {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          student: {
            id: "11111111-1111-4111-8111-111111111111",
            student_number: "S1001",
            name: "Jordan Crown",
            grade: "7",
          },
          schedule: [],
          learning_tasks: [],
          attendance: [],
          communications: [],
          privileged_actions: {
            grading: false,
            admissions: false,
            finance_admin: false,
            staff_admin: false,
            tenant_admin: false,
          },
          meta: { served_from: "scaffold" },
        }),
      });
    }

    if (path === "/api/v1/auth/me/" || path === "/api/auth/me/") {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          email: `cert-${role}@heritage.example.org`,
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
      body: JSON.stringify({
        ok: true,
        child: { name: "Avery Reed", grade: "11" },
        student: { name: "Avery Reed", grade: "11" },
        attendance: [],
        progress: [],
        learning_tasks: [],
        communications: [],
        schedule: [],
        billing: { balance_cents: 0, external_payment_provider_enabled: false },
        staff_controls: { grade_write: false, attendance_write: false, admissions_decision: false, finance_admin: false, tenant_admin: false },
        privileged_actions: { grading: false, admissions: false, finance_admin: false, tenant_admin: false },
        meta: { served_from: "scaffold", school_name: "Heritage Christian Academy" },
      }),
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
  if (failed.length > 0) {
    console.error("SCAFFOLD_CERTIFICATION_FAILED_ROUTES_BEGIN");
    for (const row of failed) {
      console.error(JSON.stringify({
        id: row.id,
        route: row.route,
        persona: row.persona,
        tenant: row.tenant,
        errors: row.errors,
        missingExpectedApis: row.missingExpectedApis,
        failedRequests: row.failedRequests,
        missingProvenance: row.missingProvenance ?? [],
        nonLiveProvenance: row.nonLiveProvenance ?? [],
        consoleErrors: row.consoleErrors,
        criticalAccessibilityViolations: row.criticalAccessibilityViolations,
      }));
    }
    console.error("SCAFFOLD_CERTIFICATION_FAILED_ROUTES_END");
  }

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
            consoleErrors.push(text);
          }
        });

        const sandboxRole = mapCertificationRoleToSandboxRole(persona.role);
        const session = await createSandboxSession(page, sandboxRole, tenant.schoolId);
        await installCertificationApiStubs(page, persona.role, tenant.schoolId);

        await page.addInitScript(({ sessionPayload }) => {
          localStorage.setItem("crown_access", sessionPayload.access);
          localStorage.setItem("crown_refresh", sessionPayload.refresh || "");
          localStorage.setItem("crown_current_user", JSON.stringify(sessionPayload.currentUser));
          localStorage.setItem("crown_school_id", sessionPayload.school_id);
          localStorage.setItem("crown_school_name", sessionPayload.school_name || "Heritage Christian Academy");
        }, { sessionPayload: session });

        const recorder = attachNetworkRecorder(page);
        const routeUrl = surface.route;
        await page.goto(routeUrl, { waitUntil: "domcontentloaded" });
        await page.waitForTimeout(250);

        const blockers = await collectPageBlockers(page);
        const accessibility = await runAccessibilityCertification(page);
        const network = recorder.snapshot();
        recorder.detach();

        const expectedApis = (surface.expectedApis || []).filter((apiPath) => !SCAFFOLD_AUTH_API.has(apiPath));
        const observedPaths = new Set(network.requests.map((request) => request.pathname));
        const missingExpectedApis = expectedApis.filter((apiPath) => !observedPaths.has(apiPath));
        const failedRequests = network.requests.filter((request) => request.status >= 400);
        const missingProvenance = network.requests.filter((request) => request.status < 400 && request.provenanceState === "missing");
        const nonLiveProvenance = network.requests.filter((request) => request.status < 400 && request.provenanceState === "non-live");

        const errors = [
          ...blockers,
          ...consoleErrors.map((error) => `Console error: ${error}`),
          ...missingExpectedApis.map((apiPath) => `Expected API not observed: ${apiPath}`),
          ...failedRequests.map((request) => `Failed request: ${request.method} ${request.pathname} -> ${request.status}`),
          ...accessibility.criticalViolations.map((violation) => `Critical accessibility violation: ${violation.id}`),
        ];

        const status = errors.length === 0 ? "PASS" : "FAIL";
        await page.screenshot({ path: screenshotPathFor(surface.id, persona.id, tenant.id), fullPage: true });

        appendCertificationResult({
          id: surface.id,
          route: surface.route,
          persona: persona.id,
          tenant: tenant.id,
          status,
          errors,
          missingExpectedApis,
          failedRequests,
          missingProvenance,
          nonLiveProvenance,
          consoleErrors,
          criticalAccessibilityViolations: accessibility.criticalViolations,
          testTitle: testInfo.title,
        });

        expect(errors, errors.join("\n")).toEqual([]);
      });
    }
  }
}
