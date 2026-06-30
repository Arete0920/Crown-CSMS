import { expect, type Page } from "@playwright/test";
import type { AccessibilityResult } from "./accessibility";
import type { NetworkRecorder } from "./network-recorder";

export async function collectPageBlockers(
  page: Page,
  network: NetworkRecorder,
  accessibility: AccessibilityResult,
  expectedText: string[] = [],
  allowFailedRequests = false,
): Promise<string[]> {
  const errors: string[] = [];

  const bodyText = await page.locator("body").innerText({ timeout: 8_000 }).catch(() => "");
  if (!bodyText.trim()) {
    errors.push("blank page body");
  }

  const pageTitle = await page.title().catch(() => "");
  if (!pageTitle.trim()) {
    errors.push("missing page title");
  }

  const crashText = ["Something went wrong", "Unhandled Runtime Error", "Application error", "React error"];
  if (crashText.some((marker) => bodyText.includes(marker))) {
    errors.push("possible crash boundary text detected");
  }

  for (const expected of expectedText) {
    if (!bodyText.toLowerCase().includes(expected.toLowerCase())) {
      errors.push(`missing expected text: ${expected}`);
    }
  }

  const missingApis = network.missingExpected();
  if (missingApis.length > 0) {
    errors.push(`missing expected API calls: ${missingApis.join(", ")}`);
  }

  if (!allowFailedRequests && network.failed.length > 0) {
    errors.push(`failed API/network requests: ${network.failed.length}`);
  }

  if (accessibility.criticalOrSeriousCount > 0) {
    errors.push(`critical/serious accessibility violations: ${accessibility.criticalOrSeriousCount}`);
  }

  await expect(page.locator("body")).toBeVisible();

  return errors;
}
