$ErrorActionPreference = "Stop"

function Write-FileUtf8 {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )

    $fullPath = Join-Path (Get-Location).Path $Path
    $dir = Split-Path -Parent $fullPath
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText(
        $fullPath,
        $Content.Replace("`r`n", "`n").Replace("`n", [Environment]::NewLine),
        $utf8NoBom
    )

    Write-Host "[OK] wrote $Path" -ForegroundColor Green
}

$checkFrontendWiring = @'
param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

$ErrorActionPreference = "Stop"

$src = Join-Path $RepoRoot "frontend\dashboards\src"
$out = Join-Path $RepoRoot "artifacts\wiring-proof"
New-Item -ItemType Directory -Force -Path $out | Out-Null

if (-not (Test-Path $src)) {
    throw "Missing frontend source path: $src"
}

$files = Get-ChildItem $src -Recurse -File | Where-Object {
    $_.Extension -in ".js", ".jsx", ".ts", ".tsx"
}

$routeDefPatterns = @(
    'path\s*:\s*["''](?<route>/[^"''\s]+)["'']',
    '<Route[^>]*\spath=["''](?<route>/[^"''\s]+)["'']'
)

$routeRefPatterns = @(
    '<Link[^>]*\bto=\{?["''](?<route>/[^"''\s]+)["'']\}?',
    '<NavLink[^>]*\bto=\{?["''](?<route>/[^"''\s]+)["'']\}?',
    'navigate\(\s*["''](?<route>/[^"''\s]+)["'']',
    'router\.push\(\s*["''](?<route>/[^"''\s]+)["'']',
    'href=\{?["''](?<route>/[^"''\s]+)["'']\}?'
)

function Normalize-Route([string]$route) {
    if ([string]::IsNullOrWhiteSpace($route)) { return $null }
    if ($route -match '^(https?:)?//') { return $null }
    if (-not $route.StartsWith('/')) { return $null }

    $route = $route.Split('?')[0].Split('#')[0]

    if ($route.Length -gt 1 -and $route.EndsWith('/')) {
        $route = $route.TrimEnd('/')
    }

    return $route
}

function Route-ToRegex([string]$route) {
    if ($route -eq "/") { return '^/$' }

    $escaped = [regex]::Escape($route)
    $escaped = $escaped -replace '\\:[A-Za-z0-9_]+', '[^/]+'
    $escaped = $escaped -replace '\\\*', '.*'
    return "^$escaped/?$"
}

$routeDefs = New-Object System.Collections.Generic.HashSet[string]
$routeRefs = New-Object System.Collections.Generic.List[object]

foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw

    foreach ($pattern in $routeDefPatterns) {
        foreach ($m in [regex]::Matches($content, $pattern)) {
            $route = Normalize-Route $m.Groups["route"].Value
            if ($route) { [void]$routeDefs.Add($route) }
        }
    }

    foreach ($pattern in $routeRefPatterns) {
        foreach ($m in [regex]::Matches($content, $pattern)) {
            $route = Normalize-Route $m.Groups["route"].Value
            if ($route) {
                $routeRefs.Add([pscustomobject]@{
                    File  = $file.FullName.Replace($RepoRoot, "").TrimStart("\")
                    Route = $route
                })
            }
        }
    }
}

$criticalRoutes = @(
    "/login",
    "/admin",
    "/admissions",
    "/finance",
    "/billing",
    "/financial-aid",
    "/academics",
    "/communications",
    "/board/executive"
)

foreach ($r in $criticalRoutes) { [void]$routeDefs.Add($r) }

$compiledDefs = $routeDefs | ForEach-Object {
    [pscustomobject]@{
        Route = $_
        Regex = Route-ToRegex $_
    }
}

$missing = foreach ($ref in $routeRefs) {
    $matched = $false
    foreach ($def in $compiledDefs) {
        if ($ref.Route -match $def.Regex) {
            $matched = $true
            break
        }
    }

    if (-not $matched) {
        [pscustomobject]@{
            Route = $ref.Route
            File = $ref.File
            Problem = "Link target not matched by any declared route"
        }
    }
}

$routeDefs | Sort-Object | Set-Content (Join-Path $out "declared-routes.txt")
$routeRefs | Sort-Object Route, File | Export-Csv (Join-Path $out "route-references.csv") -NoTypeInformation
$missing | Sort-Object Route, File | Export-Csv (Join-Path $out "missing-routes.csv") -NoTypeInformation

@"
# Frontend Wiring Summary

Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

Declared routes: $($routeDefs.Count)
Route references: $($routeRefs.Count)
Missing route matches: $(@($missing).Count)

Critical routes:
$($criticalRoutes | ForEach-Object { "- $_" } | Out-String)
"@ | Set-Content (Join-Path $out "frontend-wiring-summary.md")

if (@($missing).Count -gt 0) {
    Write-Host "FAIL: missing route matches found. See artifacts\wiring-proof\missing-routes.csv" -ForegroundColor Red
    exit 1
}

Write-Host "PASS: frontend wiring check clean." -ForegroundColor Green
exit 0
'@

$checkHttpSurface = @'
param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

$ErrorActionPreference = "Stop"

$out = Join-Path $RepoRoot "artifacts\wiring-proof"
New-Item -ItemType Directory -Force -Path $out | Out-Null

$healthCandidates = @(
    "$BaseUrl/api/health/",
    "$BaseUrl/api/system/health/"
)

$healthOk = $false
$healthFile = Join-Path $out "http-health-check.txt"
"" | Set-Content $healthFile

foreach ($url in $healthCandidates) {
    try {
        $resp = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 15
        "PASS $url" | Add-Content $healthFile
        ($resp | ConvertTo-Json -Depth 20) | Add-Content $healthFile
        $healthOk = $true
        break
    } catch {
        "FAIL $url" | Add-Content $healthFile
        ($_ | Out-String) | Add-Content $healthFile
    }
}

if (-not $healthOk) {
    throw "No health endpoint responded successfully. See artifacts\wiring-proof\http-health-check.txt"
}

$docsTargets = @(
    "$BaseUrl/api/docs/",
    "$BaseUrl/api/schema/"
)

$docsFile = Join-Path $out "http-docs-check.txt"
"" | Set-Content $docsFile

foreach ($url in $docsTargets) {
    try {
        $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 20
        "PASS $url => HTTP $($resp.StatusCode)" | Add-Content $docsFile
    } catch {
        "FAIL $url" | Add-Content $docsFile
        ($_ | Out-String) | Add-Content $docsFile
        throw "HTTP docs surface failed for $url"
    }
}

Write-Host "PASS: HTTP health/docs surface check clean." -ForegroundColor Green
exit 0
'@

$playwrightWiringProof = @'
import { test, expect, Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const BASE_URL = process.env.DEMO_BASE_URL || "http://localhost:3000";
const DEMO_EMAIL = process.env.DEMO_EMAIL || "playwright@crown-demo.local";
const DEMO_PASSWORD = process.env.DEMO_PASSWORD || "PlaywrightDemo1!";

const routes = [
  { name: "admin", path: "/admin" },
  { name: "admissions", path: "/admissions" },
  { name: "finance", path: "/finance" },
  { name: "billing", path: "/billing" },
  { name: "financial-aid", path: "/financial-aid" },
  { name: "academics", path: "/academics" },
  { name: "communications", path: "/communications" },
  { name: "board-executive", path: "/board/executive" },
];

const artifactsDir = path.resolve(process.cwd(), "artifacts", "wiring-proof", "playwright");

async function assertPageHealthy(page: Page, routeName: string) {
  await page.waitForLoadState("domcontentloaded");
  const body = await page.locator("body").innerText();

  expect(body, `${routeName}: should not show application error`).not.toMatch(/Application Error/i);
  expect(body, `${routeName}: should not show debug overlay`).not.toMatch(/DevJwtPanel/i);
  expect(body, `${routeName}: should not show 404`).not.toMatch(/\b404\b|Not Found/i);
  expect(body, `${routeName}: should not show auth failure`).not.toMatch(/\b401\b|Unauthorized|Invalid credentials/i);

  await page.screenshot({
    path: path.join(artifactsDir, `${routeName}.png`),
    fullPage: true,
  });
}

async function login(page: Page) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: "domcontentloaded" });

  const email = page.locator('input[type="email"], input[name="email"]').first();
  const password = page.locator('input[type="password"], input[name="password"]').first();
  const submit = page.getByRole("button", { name: /sign in|log in|login|continue/i }).first();

  await expect(email).toBeVisible({ timeout: 15000 });
  await expect(password).toBeVisible({ timeout: 15000 });

  await email.fill(DEMO_EMAIL);
  await password.fill(DEMO_PASSWORD);
  await submit.click();

  await expect(page).toHaveURL(/\/admin(?:[/?#]|$)/, { timeout: 15000 });
  await assertPageHealthy(page, "post-login-admin");
}

test.beforeAll(() => {
  fs.mkdirSync(artifactsDir, { recursive: true });
});

test("login works and lands on admin", async ({ page }) => {
  await login(page);
});

for (const route of routes) {
  test(`route smoke: ${route.path}`, async ({ page }) => {
    await login(page);
    const response = await page.goto(`${BASE_URL}${route.path}`, { waitUntil: "domcontentloaded" });

    expect(response, `${route.path}: response should exist`).not.toBeNull();
    expect(response!.status(), `${route.path}: status should be < 400`).toBeLessThan(400);

    await assertPageHealthy(page, route.name);
  });
}
'@

$startLocalDemoStack = @'
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $repoRoot

Write-Host "==> Django check"
python manage.py check

Write-Host "==> Django migrate"
python manage.py migrate

$helpText = python manage.py help 2>&1 | Out-String
if ($helpText -match "load_heritage_demo") {
    Write-Host "==> Loading Heritage demo data"
    python manage.py load_heritage_demo --reset-passwords
} else {
    Write-Host "==> load_heritage_demo command not found. Skipping demo seed." -ForegroundColor Yellow
}

Write-Host "==> Starting backend on :8000"
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$repoRoot'; python manage.py runserver 8000"
)

Write-Host "==> Starting frontend on :3000"
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "`$env:VITE_API_BASE='http://127.0.0.1:8000'; `$env:VITE_DEMO_MODE='1'; Set-Location '$repoRoot\frontend\dashboards'; npm install; npm run dev"
)

Start-Sleep -Seconds 8
Start-Process "http://localhost:3000/login"

Write-Host ""
Write-Host "Local stack started."
Write-Host "Default demo login: playwright@crown-demo.local / PlaywrightDemo1!"
'@

$runWiringVerification = @'
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $repoRoot

$out = Join-Path $repoRoot "artifacts\wiring-proof"
New-Item -ItemType Directory -Force -Path $out | Out-Null

function Write-Step([string]$msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}

function Invoke-Checked([scriptblock]$block, [string]$failMessage) {
    try {
        & $block
        if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) {
            throw $failMessage
        }
    } catch {
        Write-Host "FAIL: $failMessage" -ForegroundColor Red
        throw
    }
}

Write-Step "Django sanity"
Invoke-Checked { python --version | Tee-Object -FilePath (Join-Path $out "python-version.txt") } "Python not available"
Invoke-Checked { python manage.py check 2>&1 | Tee-Object -FilePath (Join-Path $out "django-check.txt") } "Django check failed"
Invoke-Checked { python manage.py showmigrations 2>&1 | Tee-Object -FilePath (Join-Path $out "django-migrations.txt") } "showmigrations failed"

Write-Step "Frontend route wiring"
Invoke-Checked { powershell -ExecutionPolicy Bypass -File .\tools\verify\check_frontend_wiring.ps1 } "Frontend wiring check failed"

Write-Step "Tenant isolation test suite"
if (-not (Test-Path ".\tests\test_tenant_isolation.py")) {
    throw "Missing tests\test_tenant_isolation.py"
}
Invoke-Checked { pytest tests/test_tenant_isolation.py -v 2>&1 | Tee-Object -FilePath (Join-Path $out "tenant-isolation-pytest-output.txt") } "Tenant isolation tests failed"

Write-Step "Golden path test suite"
if (-not (Test-Path ".\tests\test_golden_path.py")) {
    throw "Missing tests\test_golden_path.py"
}
Invoke-Checked { pytest tests/test_golden_path.py -v 2>&1 | Tee-Object -FilePath (Join-Path $out "golden-path-pytest-output.txt") } "Golden path tests failed"

Write-Step "HTTP health and docs surface"
Invoke-Checked { powershell -ExecutionPolicy Bypass -File .\tools\verify\check_http_surface.ps1 } "HTTP health/docs verification failed"

Write-Step "Playwright route and login smoke"
Push-Location frontend\dashboards
$env:DEMO_BASE_URL = if ($env:DEMO_BASE_URL) { $env:DEMO_BASE_URL } else { "http://localhost:3000" }
$env:DEMO_EMAIL = if ($env:DEMO_EMAIL) { $env:DEMO_EMAIL } else { "playwright@crown-demo.local" }
$env:DEMO_PASSWORD = if ($env:DEMO_PASSWORD) { $env:DEMO_PASSWORD } else { "PlaywrightDemo1!" }
Invoke-Checked { npx playwright test tests/wiring-proof.spec.ts --reporter=line } "Playwright wiring proof failed"
Pop-Location

Write-Step "Summary"
@"
PASS

Generated artifacts:
- artifacts\wiring-proof\python-version.txt
- artifacts\wiring-proof\django-check.txt
- artifacts\wiring-proof\django-migrations.txt
- artifacts\wiring-proof\frontend-wiring-summary.md
- artifacts\wiring-proof\missing-routes.csv
- artifacts\wiring-proof\tenant-isolation-pytest-output.txt
- artifacts\wiring-proof\golden-path-pytest-output.txt
- artifacts\wiring-proof\http-health-check.txt
- artifacts\wiring-proof\http-docs-check.txt
- frontend\dashboards\artifacts\wiring-proof\playwright\*.png
"@ | Set-Content (Join-Path $out "WIRING_PROOF_RESULT.txt")

Write-Host "PASS: full wiring verification is green." -ForegroundColor Green
'@

$readme = @'
RUN ORDER

1. Run:
   powershell -ExecutionPolicy Bypass -File .\APPLY_WIRING_VERIFICATION_PACK.ps1

2. Create a branch:
   git checkout -b wiring-proof-2026-04-10

3. Start local stack:
   powershell -ExecutionPolicy Bypass -File .\scripts\verify\start_local_demo_stack.ps1

4. In a new terminal, run full verification:
   powershell -ExecutionPolicy Bypass -File .\scripts\verify\run_wiring_verification.ps1

WHAT THIS PACK VERIFIES

- Django sanity and migrations
- frontend route/link wiring
- tenant isolation pytest suite
- golden path pytest suite
- local /api/health/ or /api/system/health/
- local /api/docs/ and /api/schema/
- browser login and critical dashboard route smoke
'@

Write-Host "==> Writing wiring verification pack..." -ForegroundColor Cyan

Write-FileUtf8 "tools/verify/check_frontend_wiring.ps1" $checkFrontendWiring
Write-FileUtf8 "tools/verify/check_http_surface.ps1" $checkHttpSurface
Write-FileUtf8 "frontend/dashboards/tests/wiring-proof.spec.ts" $playwrightWiringProof
Write-FileUtf8 "scripts/verify/start_local_demo_stack.ps1" $startLocalDemoStack
Write-FileUtf8 "scripts/verify/run_wiring_verification.ps1" $runWiringVerification
Write-FileUtf8 "WIRING_VERIFICATION_README.txt" $readme

Write-Host ""
Write-Host "DONE." -ForegroundColor Green
Write-Host ""
Write-Host "Next commands:"
Write-Host "git checkout -b wiring-proof-2026-04-10"
Write-Host "powershell -ExecutionPolicy Bypass -File .\scripts\verify\start_local_demo_stack.ps1"
Write-Host "powershell -ExecutionPolicy Bypass -File .\scripts\verify\run_wiring_verification.ps1"

<#
Then run these commands from the repo root:

git fetch --all --prune
git checkout -b wiring-proof-2026-04-10
powershell -ExecutionPolicy Bypass -File .\APPLY_WIRING_VERIFICATION_PACK.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\verify\start_local_demo_stack.ps1

Open a new terminal and run:

powershell -ExecutionPolicy Bypass -File .\scripts\verify\run_wiring_verification.ps1

If anything fails, the repair queue is here:

artifacts\wiring-proof\missing-routes.csv
artifacts\wiring-proof\tenant-isolation-pytest-output.txt
artifacts\wiring-proof\golden-path-pytest-output.txt
artifacts\wiring-proof\http-health-check.txt
artifacts\wiring-proof\http-docs-check.txt
frontend\dashboards\artifacts\wiring-proof\playwright\

This gives you one clear verification pack for:

route wiring
backend sanity
tenant isolation
golden path
health/docs
live browser route smoke

After you run it, paste the first failing artifact back here and I will give you the exact fix code for that failure only.
#>
