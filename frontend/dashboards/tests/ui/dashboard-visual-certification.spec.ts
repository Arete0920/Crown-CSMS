import { expect, test } from "@playwright/test";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const BASE = process.env.VITE_DEV_BASE_URL || "http://localhost:4173";
const DEMO_SCHOOL_ID =
  process.env.CROWN_DEMO_SCHOOL_ID || "19801b59-8c05-4c84-9312-5d792e4e839d";
const DEMO_TOKEN = process.env.CROWN_DEMO_TOKEN || "playwright-demo-token";
const KNOWN_DISPLAY_MOJIBAKE = /\u00e2\u20ac(?:\u201d|\u201c|\u2122|\u0153|\u00a6)/u;

// Visual-only route inventory. Presence here does not certify a persona as an
// active supported dashboard role. Certified supported roles remain governed by
// docs/CURRENT_RELEASE_STATUS.md and issue #1619.
const DASHBOARD_SURFACES = [
  { path: "/school-admin-dashboard", role: "school_admin" },
  { path: "/board", role: "board" },
  { path: "/teacher", role: "teacher" },
  { path: "/parent", role: "parent" },
  { path: "/student", role: "student" },
  { path: "/it", role: "it_director" },
  { path: "/financial-aid", role: "aid_director" },
  { path: "/marketing", role: "marketing" },
  { path: "/advancement", role: "advancement" },
  { path: "/spiritual-life", role: "chaplain" },
  { path: "/office", role: "office_manager" },
  { path: "/health", role: "nurse" },
  { path: "/counseling", role: "counselor" },
  { path: "/food", role: "food_service" },
  { path: "/athletics", role: "athletic_director" },
  { path: "/transportation", role: "transportation" },
  { path: "/facilities", role: "facilities" },
  { path: "/security", role: "security" },
  { path: "/academic-support", role: "academic_support" },
  { path: "/fine-arts", role: "fine_arts" },
  { path: "/library", role: "librarian" },
  { path: "/extended-care", role: "extended_care" },
  { path: "/registrar", role: "registrar" },
  { path: "/communications-director", role: "communications_director" },
  { path: "/pd", role: "pd_director" },
  { path: "/student-services", role: "student_services" },
  { path: "/sandbox", role: "school_admin" },
  { path: "/sandbox/command-center", role: "school_admin" },
] as const;

const VIEWPORTS = [
  { name: "desktop", width: 1440, height: 1024 },
  { name: "tablet", width: 1024, height: 768 },
  { name: "mobile", width: 390, height: 844 },
] as const;

const EVIDENCE_DIR = path.resolve("test-results/visual-dashboard-review");
const MANIFEST_PATH = path.join(EVIDENCE_DIR, "manifest.json");
const EXPECTED_SCREENSHOTS = DASHBOARD_SURFACES.length * VIEWPORTS.length;

async function seedDemoSession(page, role: string) {
  await page.addInitScript(
    ({ role, token, schoolId }) => {
      sessionStorage.setItem("crown.jwt.access", token);
      sessionStorage.setItem("crown.role", role);
      sessionStorage.setItem("crown.school.id", schoolId);
      localStorage.setItem("crown.jwt.access", token);
      localStorage.setItem("crown.role", role);
      localStorage.setItem("crown.school.id", schoolId);
      localStorage.setItem("crown.demo.role", role);
    },
    { role, token: DEMO_TOKEN, schoolId: DEMO_SCHOOL_ID }
  );
}

async function installVisualReviewApiStubs(page) {
  await page.route("**/api/**", async (route) => {
    if (route.request().method() !== "GET") {
      await route.continue();
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({}),
    });
  });
}

function screenshotRelativePath(viewport: string, routePath: string) {
  const slug = routePath.replace(/^\//, "").replaceAll("/", "-") || "root";
  return `${viewport}/${slug}.png`;
}

async function assertFlipCardGeometry(page, viewport: (typeof VIEWPORTS)[number], routePath: string) {
  const cards = await page.locator(".launch-dashboard-grid-module > .launch-flip-card").evaluateAll((elements) => (
    elements
      .filter((element) => (element as HTMLElement).offsetParent !== null)
      .map((element) => {
        const rect = element.getBoundingClientRect();
        return {
          top: Math.round(rect.top),
          width: Math.round(rect.width),
          height: Math.round(rect.height),
          minHeight: getComputedStyle(element).minHeight,
        };
      })
  ));

  if (cards.length < 2) return;

  const widthSpread = Math.max(...cards.map((card) => card.width)) - Math.min(...cards.map((card) => card.width));
  expect(widthSpread, `${routePath} flip-card widths diverge at ${viewport.name}`).toBeLessThanOrEqual(2);

  if (viewport.width <= 1180) {
    expect(
      cards.every((card) => card.minHeight !== "360px"),
      `${routePath} retains oversized 360px flip-card minimum at ${viewport.name}`
    ).toBe(true);
    return;
  }

  const rows = new Map<number, typeof cards>();
  cards.forEach((card) => {
    const rowTop = [...rows.keys()].find((top) => Math.abs(top - card.top) <= 2) ?? card.top;
    rows.set(rowTop, [...(rows.get(rowTop) || []), card]);
  });

  rows.forEach((rowCards, rowTop) => {
    if (rowCards.length < 2) return;
    const heightSpread = Math.max(...rowCards.map((card) => card.height)) - Math.min(...rowCards.map((card) => card.height));
    expect(
      heightSpread,
      `${routePath} flip-card heights diverge in desktop row ${rowTop}`
    ).toBeLessThanOrEqual(2);
  });
}

async function appendManifestEntry(entry: {
  viewport: string;
  route: string;
  role: string;
  screenshot: string;
}) {
  await mkdir(EVIDENCE_DIR, { recursive: true });
  let screenshots: typeof entry[] = [];
  try {
    const current = JSON.parse(await readFile(MANIFEST_PATH, "utf-8"));
    screenshots = Array.isArray(current.screenshots) ? current.screenshots : [];
  } catch {
    screenshots = [];
  }
  screenshots.push(entry);
  screenshots.sort((a, b) =>
    `${a.viewport}:${a.route}`.localeCompare(`${b.viewport}:${b.route}`)
  );
  await writeFile(
    MANIFEST_PATH,
    JSON.stringify(
      {
        schemaVersion: 1,
        evidenceType: "visual-route-inventory",
        expectedScreenshots: EXPECTED_SCREENSHOTS,
        screenshots,
      },
      null,
      2
    ) + "\n",
    "utf-8"
  );
}

test.describe("Dashboard visual evidence", () => {
  test.beforeAll(async () => {
    await mkdir(EVIDENCE_DIR, { recursive: true });
    await writeFile(
      MANIFEST_PATH,
      JSON.stringify(
        {
          schemaVersion: 1,
          evidenceType: "visual-route-inventory",
          expectedScreenshots: EXPECTED_SCREENSHOTS,
          screenshots: [],
        },
        null,
        2
      ) + "\n",
      "utf-8"
    );
  });

  for (const viewport of VIEWPORTS) {
    for (const dashboard of DASHBOARD_SURFACES) {
      test(`${viewport.name}: ${dashboard.path}`, async ({ page }) => {
        await page.setViewportSize({ width: viewport.width, height: viewport.height });
        await installVisualReviewApiStubs(page);
        await seedDemoSession(page, dashboard.role);
        await page.goto(BASE + dashboard.path, { waitUntil: "domcontentloaded" });
        await page.waitForTimeout(350);

        await expect(page).toHaveURL((url) => url.pathname === dashboard.path);
        await expect(page.locator("#root")).toBeVisible();
        await expect(page.locator("body")).not.toContainText(
          /Not Authorized|Page Not Found|Application Error|Cannot find|\b404\b/i
        );
        await expect(
          page.locator("body"),
          `${dashboard.path} contains known display mojibake at ${viewport.name}`
        ).not.toContainText(KNOWN_DISPLAY_MOJIBAKE);

        const geometry = await page.evaluate(() => ({
          viewportWidth: window.innerWidth,
          documentWidth: document.documentElement.scrollWidth,
          bodyWidth: document.body.scrollWidth,
        }));
        expect(
          Math.max(geometry.documentWidth, geometry.bodyWidth),
          `${dashboard.path} has horizontal page overflow at ${viewport.name}`
        ).toBeLessThanOrEqual(geometry.viewportWidth + 2);

        await assertFlipCardGeometry(page, viewport, dashboard.path);

        const relativeScreenshot = screenshotRelativePath(viewport.name, dashboard.path);
        const screenshotPath = path.join(EVIDENCE_DIR, relativeScreenshot);
        await mkdir(path.dirname(screenshotPath), { recursive: true });
        await page.screenshot({
          path: screenshotPath,
          fullPage: true,
          animations: "disabled",
        });
        await appendManifestEntry({
          viewport: viewport.name,
          route: dashboard.path,
          role: dashboard.role,
          screenshot: `visual-dashboard-review/${relativeScreenshot}`,
        });
      });
    }
  }
});
