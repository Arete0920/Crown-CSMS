const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");
const outDir = process.argv[2];
const baseUrl = process.argv[3] || "http://127.0.0.1:5173";
const routes = [
  "/",
  "/login",
  "/director",
  "/admissions",
  "/attendance",
  "/gradebook",
  "/billing",
  "/communications",
  "/parent",
  "/teacher",
  "/feedback"
];
function csvEscape(value) {
  const s = String(value ?? "");
  return `"${s.replace(/"/g, '""')}"`;
}
(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const results = [];
  for (const route of routes) {
    const url = `${baseUrl}${route}`;
    const page = await browser.newPage();
    const consoleMessages = [];
    const pageErrors = [];
    const failedRequests = [];
    page.on("console", msg => {
      const type = msg.type();
      const text = msg.text();
      if (["error", "warning"].includes(type)) {
        consoleMessages.push({ type, text });
      }
    });
    page.on("pageerror", err => {
      pageErrors.push(String(err && err.message ? err.message : err));
    });
    page.on("requestfailed", req => {
      failedRequests.push({
        url: req.url(),
        method: req.method(),
        failure: req.failure() ? req.failure().errorText : ""
      });
    });
    let statusCode = "";
    let loadResult = "FAIL";
    let error = "";
    try {
      const response = await page.goto(url, {
        waitUntil: "networkidle",
        timeout: 20000
      });
      statusCode = response ? response.status() : "";
      loadResult = response && response.status() < 400 ? "PASS" : "FAIL";
      await page.screenshot({
        path: path.join(outDir, `screenshot_${route.replaceAll("/", "_") || "root"}.png`),
        fullPage: true
      });
    } catch (e) {
      error = e && e.message ? e.message : String(e);
    }
    const consoleErrorCount = consoleMessages.filter(m => m.type === "error").length;
    const pageErrorCount = pageErrors.length;
    const failedRequestCount = failedRequests.length;
    const result =
      loadResult === "PASS" &&
      consoleErrorCount === 0 &&
      pageErrorCount === 0 &&
      failedRequestCount === 0
        ? "PASS"
        : "FAIL";
    results.push({
      route,
      url,
      statusCode,
      loadResult,
      consoleErrorCount,
      consoleWarningCount: consoleMessages.filter(m => m.type === "warning").length,
      pageErrorCount,
      failedRequestCount,
      result,
      error,
      consoleMessages,
      pageErrors,
      failedRequests
    });
    await page.close();
  }
  await browser.close();
  const jsonPath = path.join(outDir, "browser_console_smoke_results.json");
  fs.writeFileSync(jsonPath, JSON.stringify(results, null, 2));
  const csvRows = [
    [
      "Route",
      "Url",
      "StatusCode",
      "LoadResult",
      "ConsoleErrors",
      "ConsoleWarnings",
      "PageErrors",
      "FailedRequests",
      "Result",
      "Error"
    ].join(",")
  ];
  for (const r of results) {
    csvRows.push([
      csvEscape(r.route),
      csvEscape(r.url),
      csvEscape(r.statusCode),
      csvEscape(r.loadResult),
      csvEscape(r.consoleErrorCount),
      csvEscape(r.consoleWarningCount),
      csvEscape(r.pageErrorCount),
      csvEscape(r.failedRequestCount),
      csvEscape(r.result),
      csvEscape(r.error)
    ].join(","));
  }
  fs.writeFileSync(path.join(outDir, "browser_console_smoke_results.csv"), csvRows.join("\n"));
  const pass = results.filter(r => r.result === "PASS").length;
  const fail = results.filter(r => r.result === "FAIL").length;
  const summary = `# Browser Console Smoke Proof\nBase URL: ${baseUrl}\nPASS: ${pass}\nFAIL: ${fail}\nTOTAL: ${results.length}\nDecision: ${fail === 0 ? "BROWSER CONSOLE PROOF GREEN" : "NO-GO: browser console/smoke proof has failures"}\n\n## Failed Rows\n${results.filter(r => r.result === "FAIL").map(r => `- ${r.route}: status=${r.statusCode}, load=${r.loadResult}, consoleErrors=${r.consoleErrorCount}, pageErrors=${r.pageErrorCount}, failedRequests=${r.failedRequestCount}, error=${r.error}`).join("\n") || "None"}`;
  fs.writeFileSync(path.join(outDir, "SUMMARY.md"), summary);
})();
