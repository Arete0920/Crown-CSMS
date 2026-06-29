import { test, expect, type Page, type APIRequestContext } from "@playwright/test";

const API_BASE = process.env.CROWN_TEST_API_BASE ?? "http://127.0.0.1:8000";
const UI_BASE = process.env.CROWN_TEST_UI_BASE ?? process.env.CROWN_UI_URL ?? "http://localhost:3000";
const SCHOOL_ID = process.env.CROWN_TEST_SCHOOL_ID ?? "b45b8c5a-6708-4597-aad9-a226627b2962";
const PASSWORD = process.env.CROWN_TEST_PASS ?? "Crown2026!";

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

async function tokenFor(request: APIRequestContext, username: string) {
  const response = await request.post(`${API_BASE}/api/v1/auth/token/`, {
    data: { username, password: PASSWORD },
  });
  expect(response.status(), `[${username}] login must return 200`).toBe(200);
  const data: any = await response.json();
  const token = data?.access ?? data?.access_token ?? data?.token;
  expect(token, `[${username}] token missing`).toBeTruthy();
  return token as string;
}

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

for (const persona of personas) {
  test(`${persona.name} investor path: routes, links, buttons, network, console, screenshots`, async ({ page, request }, testInfo) => {
    test.setTimeout(180_000);

    const token = await tokenFor(request, persona.username);
    await seedBrowserAuth(page, token, persona.role, persona.username);

    const consoleErrors: string[] = [];
    const requestFailures: string[] = [];
    const badResponses: string[] = [];
    const visited = new Set<string>();

    page.on("console", (msg) => {
      if (msg.type() === "error") consoleErrors.push(msg.text());
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
          headers: { Authorization: `Bearer ${token}`, "X-School-Id": SCHOOL_ID },
        });
        expect(
          linkResp.status(),
          `[${persona.name}] discovered UI link should be reachable: ${url.pathname}`
        ).toBeLessThan(500);
      }

      const enabledButtons = surface.buttons.filter((button) => !button.disabled);
      expect(
        enabledButtons.length + surface.links.length,
        `[${persona.name}] expected at least one enabled action or visible same-origin link on ${route}`
      ).toBeGreaterThan(0);
    }

    expect(requestFailures, `[${persona.name}] browser request failures`).toEqual([]);
    expect(badResponses, `[${persona.name}] failed API responses`).toEqual([]);
    expect(consoleErrors, `[${persona.name}] browser console errors`).toEqual([]);
  });
}
