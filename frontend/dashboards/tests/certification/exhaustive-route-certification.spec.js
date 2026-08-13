import { expect, test } from "@playwright/test";
import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";

const SCHOOL_ID = "19801b59-8c05-4c84-9312-5d792e4e839d";
const EVIDENCE_ROOT = path.resolve("test-results/exhaustive-route-certification");
const MANIFEST_PATH = path.join(EVIDENCE_ROOT, "manifest.json");
const ROUTE_SOURCES = [
  "src/routes/router.jsx",
  "src/routes/wizards.js",
  "src/routes/dashboardRoutes.jsx",
  "src/config/dashboardRegistry.js",
];
const ALL_ROLES = [
  "super_admin", "master_control", "school_admin", "head_of_school", "admin",
  "director", "principal", "finance_admin", "finance", "biz_office",
  "finance_director", "registrar", "attendance_admin", "academic_admin",
  "academics", "admissions_manager", "admissions_director", "advancement_officer",
  "hr_manager", "hr", "facilities_manager", "nurse", "health_office",
  "transportation_manager", "food_service_manager", "it_admin", "it_support",
  "fine_arts_director", "athletics_director", "librarian", "media_specialist",
  "extended_care_manager", "summer_camp_coordinator", "safety_manager",
  "security_officer", "curriculum_director", "pd_coordinator", "chaplain",
  "spiritual_life", "volunteer_coordinator", "service_learning_coordinator",
  "alumni_relations", "crown_implementation", "crown_data_ops",
  "crown_integrations", "crown_compliance", "crown_revenue_ops",
  "crown_platform_ops", "communications", "communications_director",
  "office_manager", "counselor", "food_service", "transportation", "facilities",
  "security", "academic_support", "fine_arts", "extended_care",
  "student_services", "teacher", "parent", "student", "board", "board_member",
  "aftercare_staff", "aid_director", "financial_aid",
];
const PARAMETER_FIXTURES = {
  id: "11111111-1111-4111-8111-111111111111",
  sectionId: "11111111-1111-4111-8111-111111111112",
  role: "school_admin",
  slug: "route-certification",
};
const APPLICATION_ERROR_TEXT = /Page Not Found|Application Error|Cannot find|\b404\b|Something went wrong|Unhandled Runtime Error/i;
const AUTHORIZATION_TEXT = /Not Authorized|Access Denied|Forbidden/i;
const AUTHORIZATION_SURFACES = new Set(["/not-authorized", "/forbidden"]);
const CREDENTIAL_FIELDS = 'input[type="password"], input[autocomplete="current-password"], input[name*="password" i]';

function slug(value) {
  const readable = value
    .replace(/^\/+/, "")
    .replace(/[^a-z0-9]+/gi, "-")
    .replace(/^-+|-+$/g, "")
    .toLowerCase() || "home";
  const digest = createHash("sha256").update(value).digest("hex").slice(0, 12);
  return `${readable}-${digest}`;
}

function concretePath(template) {
  return template
    .replace(/:([\w]+)\??/g, (_match, name) => PARAMETER_FIXTURES[name] || `route-cert-${name.toLowerCase()}`)
    .replace(/\*+$/, "route-certification");
}

function unique(values) {
  return [...new Set(values)];
}

function applicationOrigin(testInfo) {
  const configuredBaseUrl = testInfo.project.use.baseURL
    || process.env.VITE_DEV_BASE_URL
    || "http://localhost:4173";
  return new globalThis.URL(String(configuredBaseUrl)).origin;
}

async function buildInventory() {
  const pathSource = await readFile("src/routes/paths.js", "utf8");
  const constants = new Map(
    [...pathSource.matchAll(/^\s*([A-Z0-9_]+):\s*(["'])(.*?)\2,?\s*$/gm)]
      .map((match) => [match[1], match[3]]),
  );
  expect(constants.size).toBeGreaterThanOrEqual(140);

  const routes = new Map();
  const add = (routePath, source) => {
    if (routePath === "*") return;
    expect(routePath, `${source}: route path must resolve`).toBeTruthy();
    expect(routePath.startsWith("/"), `${source}: ${routePath}`).toBeTruthy();
    const sources = routes.get(routePath) || new Set();
    sources.add(source);
    routes.set(routePath, sources);
  };

  for (const file of ROUTE_SOURCES) {
    const source = await readFile(file, "utf8");
    for (const match of source.matchAll(/\bpath\s*:\s*(["'])([^"']+)\1/g)) {
      add(match[2], file);
    }
    for (const match of source.matchAll(/\bpath\s*:\s*PATHS\.([A-Z0-9_]+)/g)) {
      const constantName = match[1];
      expect(constants.has(constantName), `${file}: unknown PATHS.${constantName}`).toBeTruthy();
      add(constants.get(constantName), `${file}:PATHS.${constantName}`);
    }
  }

  const inventory = [...routes]
    .map(([template, sources]) => ({
      template,
      concrete: concretePath(template),
      sources: [...sources].sort(),
    }))
    .sort((left, right) => left.concrete.localeCompare(right.concrete));
  const registeredTemplates = new Set(inventory.map((entry) => entry.template));
  const missing = [...new Set(
    [...constants.values()].filter((value) => value !== "*" && !registeredTemplates.has(value)),
  )].sort();

  expect(inventory.length).toBeGreaterThanOrEqual(196);
  expect(missing).toEqual([]);
  return { inventory, missing };
}

function universalCollection() {
  return {
    ok: true,
    count: 0,
    next: null,
    previous: null,
    results: [],
    items: [],
    rows: [],
    records: [],
    data: [],
    schools: [],
    students: [],
    families: [],
    guardians: [],
    sections: [],
    classes: [],
    courses: [],
    terms: [],
    assignments: [],
    grades: [],
    attendance: [],
    invoices: [],
    payments: [],
    transactions: [],
    disputes: [],
    applications: [],
    messages: [],
    threads: [],
    alerts: [],
    tasks: [],
    events: [],
    widgets: [],
    kpis: [],
    wizards: [],
    counts: {},
    deps: {},
    errors: [],
  };
}

function fixture(pathname, method) {
  if (pathname === "/api/v1/board/kpis/") {
    return { enrollment: 312, netTuition: 2_850_000, aidAwarded: 640_000, attendancePct: 94.6 };
  }
  if (pathname === "/api/v1/board/trends/") return { enrollment: [], netTuition: [] };
  if (["/api/v1/board/risk/", "/api/v1/board/drivers/"].includes(pathname)) return [];
  if (["/api/v1/signals/board/compass/", "/api/v1/signals/board/risk-counts/"].includes(pathname)) return null;
  if (pathname === "/api/v1/aftercare/board/summary/") {
    return {
      as_of: "2026-08-05",
      active_enrollment: 0,
      sessions_mtd: 0,
      late_pickups_mtd: 0,
      incidents_mtd: 0,
      late_fee_revenue_mtd: 0,
    };
  }
  if (pathname === "/api/v1/nav/") return { groups: [] };
  if (pathname === "/api/v1/sandbox/parent/daily/") {
    return {
      child: { name: "Avery Reed", grade: "8" },
      attendance: [],
      progress: [],
      communications: [],
      billing: { balance_cents: 0, external_payment_provider_enabled: false },
      staff_controls: {
        grade_write: false,
        attendance_write: false,
        admissions_decision: false,
        finance_admin: false,
        tenant_admin: false,
      },
    };
  }
  if (pathname === "/api/v1/sandbox/student/self-service/") {
    return {
      student: { name: "Avery Reed", grade: "8" },
      schedule: [],
      learning_tasks: [],
      attendance: [],
      communications: [],
      privileged_actions: {
        grading: false,
        admissions: false,
        finance_admin: false,
        tenant_admin: false,
      },
    };
  }
  return {
    ...universalCollection(),
    id: PARAMETER_FIXTURES.id,
    school_id: SCHOOL_ID,
    schoolId: SCHOOL_ID,
    status: method === "POST" ? "created" : "ready",
  };
}

async function installStubs(page, seenRoles) {
  await page.route("**/*", async (route) => {
    const request = route.request();
    if (!["fetch", "xhr"].includes(request.resourceType())) return route.continue();

    const pathname = new globalThis.URL(request.url()).pathname;
    const method = request.method();
    const json = (body, status = 200) => route.fulfill({
      status,
      contentType: "application/json",
      body: JSON.stringify(body),
    });

    if (pathname === "/api/v1/sandbox/session/") {
      const payload = request.postDataJSON() || {};
      const role = payload.role || "school_admin";
      const destination = {
        school_admin: "/school-admin-dashboard",
        admissions_director: "/admissions-dashboard",
        finance_director: "/finance",
        teacher: "/teacher",
        parent: "/parent",
        student: "/student",
      }[role] || "/school-admin-dashboard";
      seenRoles?.push(role);
      return json({
        access: `route-cert-${role}-access-token`,
        refresh: "",
        school_id: SCHOOL_ID,
        school_name: "Heritage Christian Academy",
        role,
        route: destination,
        command_center: { route: "/sandbox/command-center" },
      }, 201);
    }

    if (["/api/v1/auth/me/", "/api/v1/users/me/", "/api/auth/me/"].includes(pathname)) {
      return json({ role: "super_admin", roles: ALL_ROLES, school_id: SCHOOL_ID, schoolId: SCHOOL_ID });
    }
    if (method === "DELETE") return route.fulfill({ status: 204, body: "" });
    return json(fixture(pathname, method), method === "POST" ? 201 : 200);
  });
}

async function seedSession(page) {
  await page.addInitScript(({ schoolId, roles }) => {
    const token = "route-cert-super-admin-access-token";
    const user = { role: "super_admin", roles, school_id: schoolId, schoolId, token };
    globalThis.__CROWN_USER_ROLES__ = roles;
    for (const store of [globalThis.sessionStorage, globalThis.localStorage]) {
      for (const key of ["crown.role", "crown.active.role", "crown.demo.role"]) store.removeItem(key);
      for (const [key, value] of Object.entries({
        "crown.jwt.access": token,
        "crown.jwt.refresh": "",
        "crown.school.id": schoolId,
        "crown.school.name": "Heritage Christian Academy",
        schoolId,
        crown_user: JSON.stringify(user),
        crown_current_user: JSON.stringify(user),
        crown_user_roles: JSON.stringify(roles),
      })) store.setItem(key, value);
    }
  }, { schoolId: SCHOOL_ID, roles: ALL_ROLES });
}

async function loadPersonas() {
  const source = await readFile("src/sandbox/sandboxExperience.js", "utf8");
  const block = source.match(/export const SANDBOX_PERSONAS\s*=\s*\[([\s\S]*?)\n\s*\];/);
  expect(block).not.toBeNull();
  const personas = [...block[1].matchAll(/\{\s*value:\s*["']([^"']+)["'][\s\S]*?label:\s*["']([^"']+)["'][\s\S]*?route:\s*["']([^"']+)["']/g)]
    .map((match) => ({ value: match[1], label: match[2], route: match[3] }));
  expect(personas).toHaveLength(6);
  return personas;
}

test.describe.configure({ retries: 0 });

test.beforeAll(async () => {
  await mkdir(path.join(EVIDENCE_ROOT, "screenshots"), { recursive: true });
});

test("Heritage roles launch", async ({ page }) => {
  const personas = await loadPersonas();
  const seenRoles = [];
  await installStubs(page, seenRoles);

  for (const persona of personas) {
    await page.goto("/sandbox");
    await expect(page.locator(CREDENTIAL_FIELDS)).toHaveCount(0);

    const card = page.locator(".persona-card").filter({
      has: page.getByText(persona.label, { exact: true }),
    });
    await expect(card).toBeVisible();
    await card.getByRole("button").click();

    await expect(page).toHaveURL(new RegExp(`${persona.route.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}$`));
    await expect(page.locator(CREDENTIAL_FIELDS)).toHaveCount(0);
    await expect.poll(() => page.evaluate(() => globalThis.sessionStorage.getItem("crown.role"))).toBe(persona.value);
    await expect.poll(() => page.evaluate(() => globalThis.sessionStorage.getItem("crown.jwt.access")))
      .toBe(`route-cert-${persona.value}-access-token`);
    await expect.poll(() => page.evaluate(() => globalThis.sessionStorage.getItem("crown.school.id"))).toBe(SCHOOL_ID);
    await expect.poll(() => page.evaluate(() => globalThis.localStorage.getItem("crown.demo.role"))).toBe(persona.value);
    await expect.poll(() => page.evaluate(() => globalThis.localStorage.getItem("crown.demo.school_id"))).toBe(SCHOOL_ID);
  }

  expect(seenRoles).toEqual(personas.map((persona) => persona.value));
});

test("all registered URLs render without HTTP or browser errors", async ({ context }, testInfo) => {
  test.setTimeout(45 * 60_000);
  const { inventory, missing } = await buildInventory();
  const appOrigin = applicationOrigin(testInfo);
  const results = [];

  for (const entry of inventory) {
    const routePage = await context.newPage();
    const consoleErrors = [];
    const pageErrors = [];
    const requestFailures = [];
    const badResponses = [];
    const blockers = [];
    let response;
    let bodyText;
    let finalPath;

    try {
      await seedSession(routePage);
      await installStubs(routePage);

      routePage.on("console", (message) => {
        const text = message.text();
        if (message.type() === "error"
          && !/favicon|ResizeObserver loop|Failed to load resource: the server responded with a status of 404 \(\)/i.test(text)) {
          consoleErrors.push(text);
        }
      });
      routePage.on("pageerror", (error) => pageErrors.push(error.message));
      routePage.on("requestfailed", (request) => {
        const requestUrl = new globalThis.URL(request.url());
        if (requestUrl.origin === appOrigin) {
          requestFailures.push(`${request.method()} ${request.url()} ${request.failure()?.errorText || "failed"}`);
        }
      });
      routePage.on("response", (currentResponse) => {
        const url = new globalThis.URL(currentResponse.url());
        if (currentResponse.status() >= 400 && !/favicon\.ico$/i.test(url.pathname)) {
          const target = url.origin === appOrigin ? url.pathname : url.toString();
          badResponses.push(`${currentResponse.status()} ${currentResponse.request().method()} ${target}`);
        }
      });

      response = await routePage.goto(entry.concrete, { waitUntil: "domcontentloaded", timeout: 30_000 });
      await expect(routePage.locator("#root")).toBeVisible({ timeout: 15_000 });
      await routePage.waitForLoadState("networkidle", { timeout: 15_000 }).catch(() => undefined);
      await routePage.waitForTimeout(150);

      bodyText = (await routePage.locator("body").innerText()).trim();
      finalPath = new globalThis.URL(routePage.url()).pathname;
    } catch (error) {
      blockers.push(`route execution error: ${error instanceof Error ? error.message : String(error)}`);
      finalPath = new globalThis.URL(routePage.url()).pathname;
      bodyText = await routePage.locator("body").innerText().catch(() => "");
    }

    if (bodyText.length < 20) blockers.push(`blank body (${bodyText.length} characters)`);
    if (APPLICATION_ERROR_TEXT.test(bodyText)) blockers.push("application error text");
    if (!AUTHORIZATION_SURFACES.has(entry.concrete) && AUTHORIZATION_TEXT.test(bodyText)) blockers.push("authorization error");
    if (!["/login", "/logout", "/not-authorized", "/forbidden"].includes(entry.concrete)
      && ["/login", "/not-authorized", "/forbidden"].includes(finalPath)) {
      blockers.push(`redirect ${finalPath}`);
    }

    const finalConsoleErrors = unique(consoleErrors);
    const finalPageErrors = unique(pageErrors);
    const finalRequestFailures = unique(requestFailures);
    const finalBadResponses = unique(badResponses);
    if (finalConsoleErrors.length) blockers.push(`${finalConsoleErrors.length} console errors`);
    if (finalPageErrors.length) blockers.push(`${finalPageErrors.length} page errors`);
    if (finalRequestFailures.length) blockers.push(`${finalRequestFailures.length} failed requests`);
    if (finalBadResponses.length) blockers.push(`${finalBadResponses.length} HTTP errors`);
    if (response && response.status() >= 400) blockers.push(`document ${response.status()}`);

    const screenshot = `screenshots/${slug(entry.concrete)}.png`;
    await routePage.screenshot({
      path: path.join(EVIDENCE_ROOT, screenshot),
      fullPage: true,
      animations: "disabled",
    }).catch((error) => blockers.push(`screenshot error: ${error instanceof Error ? error.message : String(error)}`));

    results.push({
      template: entry.template,
      requestedPath: entry.concrete,
      finalPath,
      status: blockers.length ? "FAIL" : "PASS",
      responseStatus: response?.status() ?? null,
      bodyLength: bodyText.length,
      consoleErrors: finalConsoleErrors,
      pageErrors: finalPageErrors,
      requestFailures: finalRequestFailures,
      badResponses: finalBadResponses,
      blockers,
      screenshot,
    });

    await routePage.close().catch(() => undefined);
  }

  const failures = results.filter((result) => result.status === "FAIL");
  const screenshotPaths = results.map((result) => result.screenshot);
  const uniqueScreenshotCount = new Set(screenshotPaths).size;
  const screenshotCollisionCount = screenshotPaths.length - uniqueScreenshotCount;
  const manifest = {
    schemaVersion: 3,
    evidenceType: "exhaustive-frontend-route-runtime-certification",
    generatedAt: new Date().toISOString(),
    schoolId: SCHOOL_ID,
    applicationOrigin: appOrigin,
    routeCount: inventory.length,
    passedRoutes: inventory.length - failures.length,
    failedRoutes: failures.length,
    uniqueScreenshotCount,
    screenshotCollisionCount,
    unregisteredPathConstantCount: missing.length,
    unregisteredPathConstants: missing,
    results,
    sourceInventory: inventory,
  };
  await writeFile(MANIFEST_PATH, `${JSON.stringify(manifest, null, 2)}\n`);

  expect(
    screenshotCollisionCount,
    `Expected ${inventory.length} unique screenshots; found ${uniqueScreenshotCount}`,
  ).toBe(0);
  expect(
    failures,
    failures.map((failure) => `${failure.requestedPath}: ${failure.blockers.join("; ")}`).join("\n"),
  ).toEqual([]);
});
