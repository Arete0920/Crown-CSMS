import { expect, test, type Page } from "@playwright/test";

const frontendUrl = process.env.CERT_FRONTEND_URL || "http://127.0.0.1:4173";

async function openFinanceSandbox(page: Page) {
  await page.goto(`${frontendUrl}/login`, { waitUntil: "networkidle" });
  const roleSelect = page.locator("#login-role").first();
  await expect(roleSelect).toBeVisible();
  await roleSelect.selectOption("finance_director");
  const previewButton = page.getByRole("button", { name: /continue to heritage preview/i }).first();
  await previewButton.click();
  await expect(page).not.toHaveURL(/\/login(?:\?.*)?$/i, { timeout: 30000 });
}

async function verifyFinanceCannotEnterUnrelatedPrivilegedWorkspaces(page: Page) {
  const forbidden = [
    { path: "/school-admin-dashboard", pattern: /\/school-admin-dashboard(?:$|\?)/i },
    { path: "/admissions/pipeline", pattern: /\/admissions\/pipeline(?:$|\?)/i },
    { path: "/teacher", pattern: /\/teacher(?:$|\?)/i },
  ];

  for (const target of forbidden) {
    await page.goto(`${frontendUrl}${target.path}`, { waitUntil: "networkidle" });
    await expect(page, `Finance Director must be denied ${target.path}`).not.toHaveURL(target.pattern);
  }
}

test("sandbox finance director works family account, settlement, reconciliation, and controls", async ({ page }) => {
  await openFinanceSandbox(page);
  await page.goto(`${frontendUrl}/finance`, { waitUntil: "domcontentloaded" });

  const panel = page.getByTestId("sandbox-finance-transaction");
  await expect(panel).toBeVisible();
  await expect(page.getByTestId("finance-family-account")).toHaveText("Reed Family");
  await expect(panel).toContainText("HCA-DEMO-TUITION-01");
  await expect(page.getByTestId("finance-void-integrity")).toContainText("$125.00");

  const balanceBeforeText = await page.getByTestId("finance-authoritative-balance").innerText();
  const paymentPromise = page.waitForResponse(
    (response) => response.url().includes("/api/v1/sandbox/finance/apply-payment/") && response.request().method() === "POST",
    { timeout: 30000 },
  );
  await panel.getByRole("button", { name: "Apply Demo Payment" }).click();
  const response = await paymentPromise;
  expect(response.ok(), `finance transaction returned ${response.status()}`).toBeTruthy();
  const payload = await response.json();
  expect(payload.reconciliation_status).toBe("reconciled");
  expect(payload.exception_control_status).toBe("verified");
  expect(payload.voided_charges_excluded_from_balance).toBe(true);
  expect(payload.over_refund_blocked).toBe(true);
  expect(payload.external_payment_processed).toBe(false);

  await expect(page.getByTestId("finance-remaining")).toHaveText("$0.00");
  await expect(page.getByTestId("finance-reconciliation")).toHaveText("reconciled");
  await expect(page.getByTestId("finance-exception-control")).toHaveText("verified");
  await expect(page.getByTestId("finance-payment-history")).not.toHaveText("0");
  await expect(page.getByTestId("finance-allocation-history")).not.toHaveText("0");
  await expect(page.getByTestId("finance-authoritative-balance")).not.toHaveText(balanceBeforeText);
  await expect(panel).toContainText("voided charges excluded");
  await expect(panel).toContainText("No external payment processed");

  await page.reload({ waitUntil: "networkidle" });
  await expect(page.getByTestId("finance-reconciliation")).toHaveText("reconciled");
  await expect(page.getByTestId("finance-exception-control")).toHaveText("verified");
  await expect(page.getByTestId("finance-void-integrity")).toContainText("$125.00");

  await verifyFinanceCannotEnterUnrelatedPrivilegedWorkspaces(page);
});
