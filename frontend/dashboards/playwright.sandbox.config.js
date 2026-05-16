import { defineConfig, devices } from "@playwright/test";
import process from "node:process";
import { URL } from "node:url";

const BASE_URL = process.env.CROWN_BASE_URL ?? "http://127.0.0.1:3000";
const parsedBaseUrl = new URL(BASE_URL);
const serverHost = parsedBaseUrl.hostname || "127.0.0.1";
const serverPort = parsedBaseUrl.port || "3000";

export default defineConfig({
  testDir: "./tests",
  testMatch: ["**/ui/sandbox-20-schools-proof.spec.ts"],
  timeout: 60_000,
  expect: { timeout: 10_000 },
  retries: process.env.CI ? 1 : 0,
  reporter: [
    ["line"],
    ["html", { outputFolder: "playwright-report-sandbox", open: "never" }],
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
  webServer: {
    command: process.env.CI
      ? `npm run build && npm run preview -- --host ${serverHost} --port ${serverPort} --strictPort`
      : `npm run dev -- --host ${serverHost} --port ${serverPort}`,
    url: BASE_URL,
    reuseExistingServer: true,
    timeout: process.env.CI ? 240_000 : 120_000,
    stdout: "ignore",
    stderr: "pipe",
  },
});
