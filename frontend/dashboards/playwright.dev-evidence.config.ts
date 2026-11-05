import { defineConfig } from '@playwright/test';
import base from './playwright.config';

// This config is used only by the DEV evidence wrapper. Explicit diagnostic
// files written by existing tests remain outside its publication directory.
export default defineConfig({
  ...base,
  reporter: [['./scripts/dev-browser-evidence-reporter.mjs']],
  outputDir: process.env.CROWN_SAFE_EVIDENCE_TEST_OUTPUT,
  use: {
    ...base.use,
    trace: 'off',
    screenshot: 'off',
    video: 'off',
  },
});
