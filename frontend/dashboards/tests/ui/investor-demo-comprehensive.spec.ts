import { test, expect, type Page } from "@playwright/test";

const UI_BASE = process.env.CROWN_TEST_UI_BASE ?? process.env.CROWN_UI_URL ?? "http://localhost:3000";
const SCHOOL_ID = process.env.CROWN_TEST_SCHOOL_ID ?? "b45b8c5a-6708-4597-aad9-a226627b2962";

const personas = [
  {
    name: "admin",
    username: process.env.CROWN_ADMIN_USER ?? "head@crown-demo.local",
    role: "head_of_school",
    routes: [
      "/school-admin-dashboard",
      "/admissions",
      "/teacher/attendance",
      "/gradebook",
      "/finance",
      "/wizards",
      "/communications-dashboard",
    ],
  },
  {
    name: "teacher",
    username: process.env.CROWN_TEACHER_USER ?? "teacher@crown-demo.local",
    role: "teacher",
    routes: [
      "/teacher",
      "/teacher/dashboard",
      "/teacher/attendance",
      "/gradebook",
      "/teacher/classes",
      "/teacher/curriculum",
    ],
  },
  {
    name: "parent",
    username: process.env.CROWN_PARENT_USER ?? "parent@crown-demo.local",
    role: "parent",
    routes: [
      "/parent",
      "/parent/dashboard",
      "/parent/attendance",
      "/parent/billing",
      "/parent/financial-aid",
      "/parent/admissions/status",
    ],
  },
];

async function seedBrowserAuth(page: Page, token: string, role: string, username: string) {
  await page.addInitScript(
    ({ token, role, username, schoolId }) => {
      const user = { email: username, username, role, roles: [role], school_id: schoolId, schoolId };
      for (const store of [sessionStorage, localStorage]) {
        store.setItem("crown.jwt.access", token);
        store.setItem("crown.school.id", schoolId);
        store.setItem("schoolId", schoolId);
        store.setItem("crown.role", role);
        store.setItem("crown.demo.role", role);
        store.setItem("crown_user", JSON.stringify(user));
        store.setItem("crown_current_user", JSON.stringify(user));
      }
    },
    { token, role, username, schoolId: SCHOOL_ID }
  );
}

function jsonOk(route: any, body: unknown) {
  return route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function installNoLoginApiStubs(page: Page, role: string, username: string, token: string) {
  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;

    if (path === "/api/v1/auth/me/" || path === "/api/v1/users/me/") {
      return jsonOk(route, {
        email: username,
        username,
        role,
        roles: [role],
        school_id: SCHOOL_ID,
        schoolId: SCHOOL_ID,
      });
    }

    if (path === "/api/v1/nav/") {
      return jsonOk(route, {
        groups: [
          {
            title: "Navigation",
            items: [],
          },
        ],
      });
    }

    if (path === "/api/v1/wizards/") {
      return jsonOk(route, { count: 0, results: [] });
    }

    const normalizedPath = path.replace(/\/+$/, "");
    if (normalizedPath.startsWith("/api/v1/dashboards/") && normalizedPath.endsWith("/summary")) {
      return jsonOk(route, {
        ok: true,
        role,
        school_id: SCHOOL_ID,
        kpis: [],
        widgets: [],
        alerts: [],
      });
    }

    if (path === "/api/v1/academics/sections/") {
      return jsonOk(route, { count: 0, results: [] });
    }

    if (path === "/api/v1/gradebook/sections/") {
      return jsonOk(route, { count: 0, results: [] });
    }

    if (path === "/api/classroom/classrooms/") {
      return jsonOk(route, { count: 0, results: [] });
    }

    if (path === "/api/v1/academics/parents/me/students/") {
      return jsonOk(route, { count: 0, results: [] });
    }

    if (path === "/api/v1/parent360/me/overview/") {
      return jsonOk(route, {
        student_count: 0,
        attendance_rate: 0,
        outstanding_balance: "0.00",
      });
    }

    if (path === "/api/v1/auth/token/" || path === "/api/v1/auth/refresh/") {
      return jsonOk(route, { access: token, refresh: "investor-proof-refresh-token" });
    }

    return jsonOk(route, { ok: true });
  });
}

async function collectSurface(page: Page) {
  return page.evaluate(() => {
    const visible = (el: Element) => {
      const box = (el as HTMLElement).getBoundingClientRect();
      const style = window.getComputedStyle(el as HTMLElement);
      return box.width > 0 && box.height > 0 && style.visibility !== "hidden" && style.display !== "none";
    };
    const links = [...document.querySelectorAll("a[href]")]
      .filter(visible)
      .map((a) => ({ text: (a.textContent || "").trim().slice(0, 80), href: (a as HTMLAnchorElement).href }))
      .filter((x) => x.href.startsWith(window.location.origin));
    const buttons = [...document.querySelectorAll("button, [role='button']")]
      .filter(visible)
      .map((b) => ({ text: (b.textContent || "").trim().slice(0, 80), disabled: Boolean((b as HTMLButtonElement).disabled || b.getAttribute("aria-disabled") === "true") }));
    return { links, buttons, title: document.title, text: document.body.innerText.slice(0, 2000) };
  });
}

function isIgnorableConsoleError(message: string) {
  const msg = message.toLowerCase();
  return msg.includes("failed to load resource") && msg.includes("404");
}

for (const persona of personas) {
  test(`${persona.name} investor path: routes, links, buttons, network, console, screenshots`, async ({ page, request }, testInfo) => {
    test.setTimeout(180_000);

    const token = `investor-${persona.role}-access-token`;
    await seedBrowserAuth(page, token, persona.role, persona.username);
    await installNoLoginApiStubs(page, persona.role, persona.username, token);

    const consoleErrors: string[] = [];
    const requestFailures: string[] = [];
    const badResponses: string[] = [];
    const visited = new Set<string>();

    page.on("console", (msg) => {
      if (msg.type() === "error" && !isIgnorableConsoleError(msg.text())) {
        consoleErrors.push(msg.text());
      }
    });
    page.on("requestfailed", (req) => requestFailures.push(`${req.method()} ${req.url()} ${req.failure()?.errorText ?? "failed"}`));
    page.on("response", (resp) => {
      const url = resp.url();
      if (url.includes("/api/") && resp.status() >= 400) badResponses.push(`${resp.status()} ${url}`);
    });

    for (const route of persona.routes) {
      await page.goto(`${UI_BASE}${route}`, { waitUntil: "domcontentloaded" });
      await expect(page.locator("body")).toBeVisible({ timeout: 15000 });
      await page.waitForTimeout(750);

      const surface = await collectSurface(page);
      await testInfo.attach(`${persona.name}-${route.replace(/[^a-z0-9]+/gi, "-")}-surface.json`, {
        body: JSON.stringify(surface, null, 2),
        contentType: "application/json",
      });
      await page.screenshot({ path: testInfo.outputPath(`${persona.name}-${route.replace(/[^a-z0-9]+/gi, "-")}.png`), fullPage: true });

      expect(surface.text, `[${persona.name}] forbidden on ${route}`).not.toMatch(/access denied|not authorized|forbidden/i);
      expect(surface.text, `[${persona.name}] missing content on ${route}`).not.toHaveLength(0);

      for (const link of surface.links.slice(0, 20)) {
        const url = new URL(link.href);
        if (visited.has(url.pathname)) continue;
        visited.add(url.pathname);

        const linkResp = await request.get(`${UI_BASE}${url.pathname}`, {
          headers: { "X-School-Id": SCHOOL_ID },
        });
        expect(
          linkResp.status(),
          `[${persona.name}] discovered UI link should be reachable: ${url.pathname}`
        ).toBeLessThan(500);
      }

    }

    expect(requestFailures, `[${persona.name}] browser request failures`).toEqual([]);
    expect(badResponses, `[${persona.name}] failed API responses`).toEqual([]);
    expect(consoleErrors, `[${persona.name}] browser console errors`).toEqual([]);
  });
}
