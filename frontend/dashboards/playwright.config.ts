import { defineConfig, devices } from "@playwright/test";

/**
 * Crown2026 Playwright configuration.
 *
 * Local dev: `npm run test:e2e` (starts Vite via webServer automatically)
 * Headed:    `npm run test:e2e:headed`
 * CI:        `npm run test:e2e` (PLAYWRIGHT_CI=1 → retries=2, no headed)
 *
 * VITE_DEV_BASE_URL env var overrides the baseURL (e.g. for staging).
 */

// Port 4173 = Vite preview default — avoids collision with port 3000 dev servers
// in concurrent CI jobs. Can be overridden via VITE_DEV_BASE_URL env var.
const BASE_URL = process.env.VITE_DEV_BASE_URL ?? "http://localhost:4173";

export default defineConfig({
  testDir: "./tests",

  /* Give each test 30 s; navigation on first load can be slow in CI */
  timeout: 30_000,
  expect: { timeout: 8_000 },

  /* Retry once in CI so transient startup timing doesn't fail the gate */
  retries: process.env.CI ? 2 : 0,

  /* Run tests in parallel within a file in CI; sequentially locally for easier debugging */
  fullyParallel: !!process.env.CI,
  workers: process.env.CI ? 2 : 1,

  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report", open: "never" }],
  ],

  use: {
    baseURL: BASE_URL,
    screenshot: "only-on-failure",
    trace: "on-first-retry",
    video: "off",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  /* Auto-start the Vite dev server when running locally or in CI.
   * CI: Playwright is the sole owner of the server lifecycle — no separate
   * workflow step pre-starts Vite, so reuseExistingServer=false is correct.
   * Local: reuse an existing server if one is already running on the port. */
  webServer: {
    command: "npm run dev -- --port 4173 --strictPort",
    url: BASE_URL,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
    stdout: "ignore",
    stderr: "pipe",
  },
});
