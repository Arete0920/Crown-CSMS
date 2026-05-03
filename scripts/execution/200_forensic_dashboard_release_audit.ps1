# CROWN FORENSIC DASHBOARD + RELEASE AUDIT
# READ-ONLY AGAINST SOURCE.
# NO SOURCE PATCHES. NO ROUTE INJECTION. NO STAGING. NO COMMITS. NO DEPLOY.
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Step($Name) {
    Write-Host ""
    Write-Host "============================================================"
    Write-Host $Name
    Write-Host "============================================================"
}
function Require-Cmd($Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Missing required command: $Name"
    }
}
Require-Cmd git
Require-Cmd node
Require-Cmd npm
Require-Cmd curl.exe

Step "RESOLVE REPO"
$Repo = ""
try {
    $Repo = (git rev-parse --show-toplevel 2>$null).Trim()
} catch {
    throw "Current terminal is not inside a Git repo."
}
if (-not $Repo -or -not (Test-Path $Repo)) { throw "Could not resolve repo root." }
Set-Location $Repo

$Router = "frontend\dashboards\src\routes\router.jsx"
$FrontendDir = "frontend\dashboards"
$SrcDir = "frontend\dashboards\src"
$PackageJson = "frontend\dashboards\package.json"

if (-not (Test-Path $Router)) { throw "Missing expected router file: $Router" }
if (-not (Test-Path $FrontendDir)) { throw "Missing frontend dir: $FrontendDir" }
if (-not (Test-Path $SrcDir)) { throw "Missing frontend src dir: $SrcDir" }
if (-not (Test-Path $PackageJson)) { throw "Missing package.json: $PackageJson" }

$RouterText = Get-Content $Router -Raw
if ($RouterText -notmatch "createBrowserRouter") {
    throw "router.jsx does not contain createBrowserRouter."
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Out = "audit-artifacts\forensic-dashboard-release-audit\$Stamp"
New-Item -ItemType Directory -Force -Path $Out | Out-Null
Write-Host "Repo: $Repo"
Write-Host "Packet: $Out"

Step "CAPTURE GIT STATE"
git rev-parse --show-toplevel | Out-File "$Out\01_repo_root.txt" -Encoding utf8
git branch --show-current | Out-File "$Out\02_branch.txt" -Encoding utf8
git rev-parse HEAD | Out-File "$Out\03_head_sha.txt" -Encoding utf8
git remote -v | Out-File "$Out\04_remotes.txt" -Encoding utf8
git status --short | Out-File "$Out\05_git_status_short.txt" -Encoding utf8
git diff --name-only | Out-File "$Out\06_dirty_files.txt" -Encoding utf8
git diff --stat | Out-File "$Out\07_dirty_stat.txt" -Encoding utf8
git diff --cached --name-status | Out-File "$Out\08_cached_status.txt" -Encoding utf8
$Cached = Get-Content "$Out\08_cached_status.txt" -Raw
if (-not [string]::IsNullOrWhiteSpace($Cached)) {
    throw "There are staged files. Stop and review/unstage first. See $Out\08_cached_status.txt"
}

Step "COPY CRITICAL SOURCE FILES INTO EVIDENCE PACKET"
$KeyFiles = @(
    "frontend\dashboards\src\routes\router.jsx",
    "frontend\dashboards\src\pages\SchoolAdministratorDashboard.jsx",
    "frontend\dashboards\src\config\dashboardTemplates\schoolAdministratorDashboard.js",
    "frontend\dashboards\src\components\crown-dashboard\CrownDashboardActionGrid.jsx",
    "frontend\dashboards\src\components\crown-dashboard\CrownDashboardFlipCard.jsx",
    "frontend\dashboards\src\components\launch\CrownActionCard.jsx",
    "frontend\dashboards\package.json"
)
"File,Exists,Size" | Out-File "$Out\09_key_file_existence.csv" -Encoding utf8
foreach ($File in $KeyFiles) {
    $Exists = Test-Path $File
    $Size = if ($Exists) { (Get-Item $File).Length } else { 0 }
    "`"$File`",$Exists,$Size" | Add-Content "$Out\09_key_file_existence.csv" -Encoding utf8
    if ($Exists) {
        $Safe = $File.Replace("\", "__").Replace("/", "__")
        Copy-Item $File "$Out\$Safe"
    }
}

Step "EXTRACT ROUTER TABLE"
"=== ROUTER HITS ===" | Out-File "$Out\10_router_hits.txt" -Encoding utf8
Select-String -Path $Router `
    -Pattern "createBrowserRouter|path:|element:|children:|loader:|errorElement|Navigate|redirect|Dashboard|Admin|SchoolAdministrator|Parent|Teacher|Admissions|Finance|Billing|Attendance|Communications|Students|Families|Reports|Settings|Enrollment" |
    ForEach-Object { "{0}:{1}:{2}" -f $_.Path,$_.LineNumber,$_.Line.Trim() } |
    Add-Content "$Out\10_router_hits.txt" -Encoding utf8

Step "EXTRACT LINK/ACTION/PLACEHOLDER RISKS"
$SourceFiles = Get-ChildItem $SrcDir -Recurse -File -Include *.js,*.jsx,*.ts,*.tsx
"=== LINK / ACTION HITS ===" | Out-File "$Out\11_link_action_hits.txt" -Encoding utf8
foreach ($Pattern in @(
    "to=","href=","navigate(","onClick","button","actions","ActionCard",
    "CrownActionCard","CrownDashboardActionGrid","disabled","route","path","module","wizard"
)) {
    "===== $Pattern =====" | Add-Content "$Out\11_link_action_hits.txt" -Encoding utf8
    Select-String -Path ($SourceFiles.FullName) -Pattern $Pattern -SimpleMatch 2>$null |
        ForEach-Object { "{0}:{1}:{2}" -f $_.Path,$_.LineNumber,$_.Line.Trim() } |
        Add-Content "$Out\11_link_action_hits.txt" -Encoding utf8
}

"=== DEAD / PLACEHOLDER HITS ===" | Out-File "$Out\12_dead_placeholder_hits.txt" -Encoding utf8
foreach ($Pattern in @(
    "TODO","FIXME","placeholder","coming soon","lorem",
    'href="#"',"href='#'",'to="#"',"to='#'","javascript:void","alert(",
    "console.log(","return null","onClick={() => {}}","onClick={}",
    "NotImplemented","Not Implemented","mock","dummy"
)) {
    "===== $Pattern =====" | Add-Content "$Out\12_dead_placeholder_hits.txt" -Encoding utf8
    Select-String -Path ($SourceFiles.FullName) -Pattern $Pattern -SimpleMatch 2>$null |
        ForEach-Object { "{0}:{1}:{2}" -f $_.Path,$_.LineNumber,$_.Line.Trim() } |
        Add-Content "$Out\12_dead_placeholder_hits.txt" -Encoding utf8
}

Step "RUN FRONTEND BUILD"
Push-Location $FrontendDir
cmd /c "npm run build > ..\..\$Out\13_frontend_build.txt 2>&1"
$BuildExit = $LASTEXITCODE
Pop-Location
if ($BuildExit -ne 0) {
    Get-Content "$Out\13_frontend_build.txt" -Tail 160
    throw "Frontend build failed. Packet captured: $Out"
}

Step "CREATE AUDIT SCRIPT OUTSIDE SOURCE TREE"
$AuditJs = Join-Path $Out "live-dashboard-audit.mjs"
@'
import fs from "fs";
import path from "path";
import { chromium } from "playwright";

const baseUrl = process.env.CROWN_FRONTEND_URL;
const outDir = process.env.CROWN_AUDIT_OUT;
const routerFile = process.env.CROWN_ROUTER_FILE;
if (!baseUrl) throw new Error("CROWN_FRONTEND_URL is required");
if (!outDir) throw new Error("CROWN_AUDIT_OUT is required");
if (!routerFile) throw new Error("CROWN_ROUTER_FILE is required");
fs.mkdirSync(outDir, { recursive: true });

const routerText = fs.readFileSync(routerFile, "utf8");
const routeSet = new Set([
  "/","/dashboard","/admin","/admin/dashboard","/school-admin","/school-administrator",
  "/parent","/parent/dashboard","/teacher","/teacher/dashboard","/admissions","/admissions/dashboard",
  "/finance","/finance/dashboard","/billing","/billing/dashboard","/attendance","/communications",
  "/students","/families","/staff","/reports","/settings","/enrollment"
]);
const pathRegexes = [
  /path\s*:\s*["'`]([^"'`]+)["'`]/g,
  /path\s*=\s*["'`]([^"'`]+)["'`]/g
];
for (const rx of pathRegexes) {
  let m;
  while ((m = rx.exec(routerText))) {
    const p = m[1].trim();
    if (!p) continue;
    if (p === "*") continue;
    if (p.startsWith(":")) continue;
    if (p.includes("*")) continue;
    if (p.startsWith("/")) routeSet.add(p);
    else routeSet.add("/" + p);
  }
}
const routes = [...routeSet].sort();

function csvEscape(value) {
  const s = String(value ?? "");
  return `"${s.replace(/"/g, '""')}"`;
}
function visibleErrorText(text) {
  return /404|not found|page not found|cannot get|application error|something went wrong|undefined is not|cannot read/i.test(text);
}
function classify(row) {
  const failures = [];
  if (Number(row.status) >= 400) failures.push(`HTTP ${row.status}`);
  if (row.visibleErrorText) failures.push("visible error text");
  if (row.textLength < 120) failures.push("blank/nearly blank");
  if (row.badHrefCount > 0) failures.push(`${row.badHrefCount} bad hrefs`);
  if (row.emptyButtonCount > 0) failures.push(`${row.emptyButtonCount} empty buttons`);
  if (row.pageErrorCount > 0) failures.push(`${row.pageErrorCount} page errors`);
  const lower = `${row.title} ${row.h1} ${row.bodySample}`.toLowerCase();
  if (lower.includes("coming soon")) failures.push("coming soon visible");
  if (lower.includes("placeholder")) failures.push("placeholder visible");
  row.pass = failures.length === 0;
  row.failure = failures.join("; ");
  return row;
}

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1440, height: 1000 },
  ignoreHTTPSErrors: true
});

const rows = [];
const consoleRows = [];
const pageErrors = [];

for (let i = 0; i < routes.length; i++) {
  const route = routes[i];
  const page = await context.newPage();
  const row = {
    route, url: new URL(route, baseUrl).toString(), status: "", pass: false, failure: "",
    title: "", h1: "", bodySample: "", textLength: 0, linkCount: 0, badHrefCount: 0,
    emptyButtonCount: 0, consoleErrorCount: 0, pageErrorCount: 0, visibleErrorText: false, screenshot: ""
  };
  const beforeConsole = consoleRows.length;
  const beforePageErrors = pageErrors.length;
  page.on("console", msg => {
    if (["error", "warning"].includes(msg.type())) {
      consoleRows.push({ route, type: msg.type(), text: msg.text(), location: msg.location() });
    }
  });
  page.on("pageerror", err => {
    pageErrors.push({ route, message: err.message, stack: err.stack });
  });
  try {
    const response = await page.goto(row.url, { waitUntil: "networkidle", timeout: 30000 });
    row.status = response ? response.status() : "";
    await page.waitForTimeout(900);
    row.title = await page.title().catch(() => "");
    row.h1 = await page.locator("h1").first().innerText({ timeout: 2500 }).catch(() => "");
    const bodyText = await page.locator("body").innerText({ timeout: 5000 }).catch(() => "");
    row.bodySample = bodyText.trim().slice(0, 500).replace(/\s+/g, " ");
    row.textLength = bodyText.trim().length;
    row.visibleErrorText = visibleErrorText(bodyText);
    const links = await page.locator("a").evaluateAll(nodes => nodes.map(a => ({
      text: (a.innerText || "").trim(),
      href: a.getAttribute("href") || "",
      aria: a.getAttribute("aria-label") || ""
    }))).catch(() => []);
    const buttons = await page.locator("button").evaluateAll(nodes => nodes.map(b => ({
      text: (b.innerText || "").trim(),
      aria: b.getAttribute("aria-label") || "",
      disabled: b.hasAttribute("disabled")
    }))).catch(() => []);
    row.linkCount = links.length;
    row.badHrefCount = links.filter(l =>
      !l.href || l.href === "#" || l.href.toLowerCase().startsWith("javascript:")
    ).length;
    row.emptyButtonCount = buttons.filter(b => !b.text && !b.aria).length;
    row.consoleErrorCount = consoleRows.length - beforeConsole;
    row.pageErrorCount = pageErrors.length - beforePageErrors;
    const safeRouteName = route === "/" ? "root" : route.replace(/[^a-z0-9]+/gi, "_");
    const screenshot = path.join(outDir, `${String(i + 1).padStart(3, "0")}_${safeRouteName}.png`);
    await page.screenshot({ path: screenshot, fullPage: true });
    row.screenshot = screenshot;
    classify(row);
  } catch (err) {
    row.pass = false;
    row.failure = err.message;
  } finally {
    await page.close().catch(() => {});
  }
  rows.push(row);
}
await browser.close();

const headers = ["route","status","pass","failure","title","h1","textLength","linkCount","badHrefCount","emptyButtonCount","consoleErrorCount","pageErrorCount","screenshot","bodySample"];
const csv = [headers.join(","), ...rows.map(row => headers.map(h => csvEscape(row[h])).join(","))].join("\n");
fs.writeFileSync(path.join(outDir, "DASHBOARD_PASS_FAIL_MATRIX.csv"), csv);
fs.writeFileSync(path.join(outDir, "CONSOLE_ERRORS.json"), JSON.stringify(consoleRows, null, 2));
fs.writeFileSync(path.join(outDir, "PAGE_ERRORS.json"), JSON.stringify(pageErrors, null, 2));

const failed = rows.filter(r => !r.pass);
const passed = rows.filter(r => r.pass);
const failedCsv = [headers.join(","), ...failed.map(row => headers.map(h => csvEscape(row[h])).join(","))].join("\n");
fs.writeFileSync(path.join(outDir, "FAILED_DASHBOARD_ROUTES.csv"), failedCsv);

const brokenActions = rows.filter(r =>
  Number(r.badHrefCount) > 0 || Number(r.emptyButtonCount) > 0 || Number(r.pageErrorCount) > 0);
fs.writeFileSync(path.join(outDir, "BROKEN_LINK_ACTION_QUEUE.json"), JSON.stringify(brokenActions, null, 2));

const md = [
  "# CROWN Live Dashboard Evidence","",
  `Base URL: ${baseUrl}`,
  `Routes checked: ${rows.length}`,
  `Passed: ${passed.length}`,
  `Failed: ${failed.length}`,
  `Pass rate: ${Math.round((passed.length / rows.length) * 100)}%`,
  "","## Failed routes","","| Route | Status | Failure | Screenshot |","| --- | ---: | --- | --- |",
  ...failed.map(r => `| ${r.route} | ${r.status} | ${String(r.failure).replace(/\|/g, "/")} | ${r.screenshot} |`),
  "","## Passed routes","","| Route | Status | H1 / Title |","| --- | ---: | --- |",
  ...passed.map(r => `| ${r.route} | ${r.status} | ${String(r.h1 || r.title).replace(/\|/g, "/")} |`)
].join("\n");
fs.writeFileSync(path.join(outDir, "SUMMARY.md"), md);

console.log(JSON.stringify({
  baseUrl, total: rows.length, pass: passed.length, fail: failed.length,
  passRate: Math.round((passed.length / rows.length) * 100)
}, null, 2));

if (failed.length > 0) process.exitCode = 1;
'@ | Set-Content $AuditJs -Encoding utf8

Step "RUN LIVE DASHBOARD BROWSER AUDIT"
Push-Location $FrontendDir
try {
    npx playwright install chromium | Out-File "..\..\$Out\14_playwright_install.txt" -Encoding utf8
} catch {
    $_ | Out-String | Out-File "..\..\$Out\14_playwright_install_ERROR.txt" -Encoding utf8
}
$env:CROWN_FRONTEND_URL = "https://yellow-forest-0eecc8b0f.7.azurestaticapps.net"
$env:CROWN_AUDIT_OUT = (Resolve-Path "..\..\$Out").Path
$env:CROWN_ROUTER_FILE = (Resolve-Path "..\..\$Router").Path
cmd /c "node ..\..\$AuditJs > ..\..\$Out\15_live_dashboard_audit_stdout.json 2>&1"
$AuditExit = $LASTEXITCODE
Pop-Location

Step "POST-RUN SAFETY CHECK"
git status --short | Out-File "$Out\16_git_status_after.txt" -Encoding utf8
git diff --name-only | Out-File "$Out\17_diff_name_only_after.txt" -Encoding utf8
git diff --stat | Out-File "$Out\18_diff_stat_after.txt" -Encoding utf8
git diff --cached --name-status | Out-File "$Out\19_cached_diff_after.txt" -Encoding utf8
$CachedAfter = Get-Content "$Out\19_cached_diff_after.txt" -Raw
if (-not [string]::IsNullOrWhiteSpace($CachedAfter)) {
    git reset | Out-File "$Out\20_git_reset_cached_after.txt" -Encoding utf8
}

$SummaryText = if (Test-Path "$Out\SUMMARY.md") {
    Get-Content "$Out\SUMMARY.md" -Raw
} else {
    Get-Content "$Out\15_live_dashboard_audit_stdout.json" -Raw
}

@"
# CROWN Forensic Dashboard Release Audit
Repo: $Repo
Packet: $Out
Frontend: https://yellow-forest-0eecc8b0f.7.azurestaticapps.net
Build exit: $BuildExit
Audit exit: $AuditExit

Files changed by this script: None in source tree.
Files created: Only audit packet files under $Out

No staging. No commits. No route changes. No placeholder fallback. No source patching.

Open:
- SUMMARY.md
- DASHBOARD_PASS_FAIL_MATRIX.csv
- FAILED_DASHBOARD_ROUTES.csv
- 10_router_hits.txt
- 11_link_action_hits.txt
- 12_dead_placeholder_hits.txt
- screenshots

Live dashboard summary:
$SummaryText
"@ | Out-File "$Out\00_README.txt" -Encoding utf8

Step "DONE"
Write-Host "PACKET: $Out"
Write-Host ""
Get-Content "$Out\00_README.txt"
