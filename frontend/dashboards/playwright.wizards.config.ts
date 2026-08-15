import { defineConfig, devices } from "@playwright/test";

const BASE_URL = process.env.CERT_FRONTEND_URL || "http://127.0.0.1:4173";

export default defineConfig({
  testDir: "../../tests/e2e",
  testMatch: /.*_wizard_spec\.ts$/,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  retries: 0,
  fullyParallel: false,
  workers: 1,
  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-wizard-report", open: "never" }],
  ],
  use: {
    baseURL: BASE_URL,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
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
      VITE_SANDBOX_MODE: process.env.VITE_SANDBOX_MODE || "1",
      VITE_DEMO_MODE: process.env.VITE_DEMO_MODE || "sandbox",
      VITE_API_BASE: process.env.VITE_API_BASE || "http://127.0.0.1:8000",
    },
  },
});
