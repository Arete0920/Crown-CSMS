import { test, expect } from "@playwright/test";
import { readFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const source = fileURLToPath(new URL("../../../sites/jireh/dist/", import.meta.url));
const shots = fileURLToPath(new URL("../jireh-proof/", import.meta.url));
const html = readFileSync(join(source, "index.html"));
const css = readFileSync(join(source, "styles.css"));

test.beforeEach(async ({ page }) => {
  await page.route("**/*", async route => {
    const url = new URL(route.request().url());
    if (url.hostname !== "jireh.test") return route.abort();
    if (url.pathname === "/" || url.pathname === "/index.html") {
      return route.fulfill({ status: 200, contentType: "text/html; charset=utf-8", body: html });
    }
    if (url.pathname === "/styles.css") {
      return route.fulfill({ status: 200, contentType: "text/css; charset=utf-8", body: css });
    }
    if (url.pathname === "/favicon.ico") return route.fulfill({ status: 204 });
    return route.fulfill({ status: 404, body: "Not found" });
  });
});

for (const width of [320, 375, 768, 1440]) {
  test(`Jireh renders cleanly at ${width}px`, async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", error => errors.push(error.message));
    page.on("console", msg => { if (msg.type() === "error") errors.push(msg.text()); });
    await page.setViewportSize({ width, height: 900 });
    const response = await page.goto("http://jireh.test/", { waitUntil: "networkidle" });
    expect(response?.status()).toBe(200);
    await expect(page.getByRole("heading", { level: 1 })).toContainText("Provision with Purpose.");
    await expect(page.getByRole("heading", { level: 1 })).toContainText("Stewardship with Wisdom.");
    const cta=page.getByRole("link", { name: /Request a Jireh demonstration/i }).first();
    await expect(cta).toBeVisible();
    await expect(cta).toHaveAttribute("href", /areteadvisorygroup\.com\/contact/);
    await expect(page.getByText("JIREH FINANCIAL AID").first()).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow, `unexpected horizontal overflow at ${width}px`).toBeLessThanOrEqual(1);
    expect(errors).toEqual([]);
    mkdirSync(shots, { recursive: true });
    await page.screenshot({ path: join(shots, `jireh-${width}.png`), fullPage: true });
  });
}

test("Jireh mobile navigation opens and reaches both product offerings", async ({page}) => {
  await page.setViewportSize({ width:375,height:812 });
  await page.goto("http://jireh.test/", {waitUntil:"domcontentloaded"});
  const toggle=page.getByText("Menu",{exact:true});
  await expect(toggle).toBeVisible();
  await toggle.click();
  const links=page.locator(".mobile-menu .mobile-links");
  await expect(links.getByRole("link", { name: "SGO solution" })).toBeVisible();
  await links.getByRole("link", { name: "SGO solution" }).click();
  await expect(page).toHaveURL(/#sgo$/);
  await expect(page.getByRole("heading", { name: /Jireh SGO/i })).toBeVisible();
});

test("Jireh CTA retains school aid versus SGO lead distinction", async ({page}) => {
  await page.goto("http://jireh.test/", {waitUntil:"domcontentloaded"});
  const school=page.getByRole("link", { name: /Request a Jireh demonstration/i }).first();
  const sgo=page.getByRole("link", { name: /Request an SGO pilot discussion/i });
  const shref=await school.getAttribute("href");
  const sghref=await sgo.getAttribute("href");
  expect(shref).toContain("Jireh%20school%20financial%20aid");
  expect(sghref).toContain("Jireh%20SGO%20design%20partner");
  expect(shref).not.toEqual(sghref);
  await expect(page.locator("meta[name='robots']")).toHaveAttribute("content","noindex,nofollow");
});
