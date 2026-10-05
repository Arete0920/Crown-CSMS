import { defineConfig, devices } from "@playwright/test";

/**
 * CROWN Playwright configuration.
 *
 * Local dev: `npm run test:e2e` (starts Vite via webServer automatically)
 * Headed:    `npm run test:e2e:headed`
 * CI:        `npm run test:e2e` (PLAYWRIGHT_CI=1 -> retries=2, no headed)
 *
 * VITE_DEV_BASE_URL env var overrides the local preview baseURL.
 * CROWN_LIVE_FRONTEND_URL is used only by live runtime certification.
 */

const IS_LIVE_RUNTIME_CERTIFICATION = process.env.CROWN_CERTIFICATION_LIVE_RUNTIME === "1";
// Structured guidance is enabled only in the stubbed smoke contract lane.
const IS_GUIDANCE_CONTRACT = process.env.npm_lifecycle_event === "test:e2e:smoke";
const IS_SCAFFOLD_CERTIFICATION = process.env.npm_lifecycle_event === "certify:scaffold-crawler";
const BASE_URL = IS_LIVE_RUNTIME_CERTIFICATION
  ? process.env.CROWN_LIVE_FRONTEND_URL
  : (process.env.VITE_DEV_BASE_URL ?? "http://localhost:4173");

if (IS_LIVE_RUNTIME_CERTIFICATION && !BASE_URL) {
  throw new Error("CROWN_LIVE_FRONTEND_URL is required when CROWN_CERTIFICATION_LIVE_RUNTIME=1.");
}

export default defineConfig({
  testDir: "./tests",

  /* Give each test 30 s; navigation on first load can be slow in CI */
  timeout: IS_LIVE_RUNTIME_CERTIFICATION ? 60_000 : 30_000,
  expect: { timeout: IS_LIVE_RUNTIME_CERTIFICATION ? 10_000 : 8_000 },

  /* Retry once in normal CI; live runtime certification must be deterministic evidence. */
  retries: IS_LIVE_RUNTIME_CERTIFICATION ? 0 : (process.env.CI ? 2 : 0),

  /* Live runtime evidence is serial by design so route failures are readable. */
  fullyParallel: IS_LIVE_RUNTIME_CERTIFICATION ? false : !!process.env.CI,
  workers: IS_LIVE_RUNTIME_CERTIFICATION ? 1 : (process.env.CI ? 2 : 1),

  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report", open: "never" }],
  ],

  use: {
    baseURL: BASE_URL,
    screenshot: IS_LIVE_RUNTIME_CERTIFICATION ? "on" : "only-on-failure",
    trace: IS_LIVE_RUNTIME_CERTIFICATION ? "on" : "on-first-retry",
    video: IS_LIVE_RUNTIME_CERTIFICATION ? "retain-on-failure" : "off",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  /* Auto-start Vite only for local/scaffold lanes. Live certification must target deployed runtime. */
  ...(IS_LIVE_RUNTIME_CERTIFICATION ? {} : {
    webServer: {
      command: process.env.CI
        ? "npm run build && npm run preview -- --port 4173 --strictPort"
        : "npm run preview -- --port 4173 --strictPort",
      url: BASE_URL,
      reuseExistingServer: !process.env.CI,
      timeout: process.env.CI ? 180_000 : 60_000,
      stdout: "ignore",
      stderr: "pipe",
      env: {
        ...process.env,
        ...(IS_GUIDANCE_CONTRACT ? { VITE_SOLOMON_GUIDANCE_ENABLED: "true", VITE_SOLOMON_EXTERNAL_ENABLED: "true" } : {}),
        ...(IS_SCAFFOLD_CERTIFICATION ? { VITE_SANDBOX_MODE: "1" } : {}),
      },
    },
  }),
});
