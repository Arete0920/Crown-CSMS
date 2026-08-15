import { defineConfig, devices } from "@playwright/test";

const BASE_URL = process.env.CERT_FRONTEND_URL || "http://127.0.0.1:4173";
const SCHOOL_ID = process.env.CROWN_DEMO_SCHOOL_ID || "19801b59-8c05-4c84-9312-5d792e4e839d";

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
    extraHTTPHeaders: {
      "X-School-Id": SCHOOL_ID,
    },
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
