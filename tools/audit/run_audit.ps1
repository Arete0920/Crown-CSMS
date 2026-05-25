# tools/audit/run_audit.ps1
# Crown2026 Deep Audit Runner (repo-wide + dashboards focus)
# Produces: ./AUDIT_REPORT.md and ./audit_artifacts/*

$ErrorActionPreference = "Continue"

# Build markdown code-fence from char code to avoid PowerShell backtick confusion
$tick  = [char]96
$fence = "$tick$tick$tick"

function Section($t) {
  Write-Host ""
  Write-Host "==============================================="
  Write-Host $t
  Write-Host "==============================================="
}

function TryRun($label, $block) {
  Write-Host "  -> $label"
  try {
    $out = (& $block) 2>&1 | Out-String
    return @{ ok=$true; out=$out }
  } catch {
    return @{ ok=$false; out=($_ | Out-String) }
  }
}

function RunWithTimeout($label, $TimeoutSec, $block) {
  Write-Host "  -> $label (timeout ${TimeoutSec}s)"
  $job = Start-Job -ScriptBlock $block
  $done = Wait-Job $job -Timeout $TimeoutSec
  if ($done) {
    $out = Receive-Job $job 2>&1 | Out-String
    Remove-Job $job -Force
    return @{ ok=$true; out=$out }
  } else {
    Stop-Job  $job -ErrorAction SilentlyContinue
    Remove-Job $job -Force
    return @{ ok=$false; out="TIMED OUT after ${TimeoutSec}s" }
  }
}

function AppendFenced($heading, $content) {
  if ($heading) { $heading | Add-Content $report }
  $fence    | Add-Content $report
  $content  | Add-Content $report
  $fence    | Add-Content $report
  ""        | Add-Content $report
}

# ── repo root guard ──────────────────────────────────────────────────────────
if (!(Test-Path ".\backend") -or !(Test-Path ".\frontend")) {
  throw "Run from repo root (must contain .\backend and .\frontend)"
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$art   = Join-Path (Get-Location) "audit_artifacts"
New-Item -ItemType Directory -Force -Path $art | Out-Null

$report = Join-Path (Get-Location) "AUDIT_REPORT.md"
"## Crown2026 Deep Audit Report"        | Set-Content  $report
"**Generated:** $stamp"                 | Add-Content $report
""                                      | Add-Content $report

# ── 1) Git state ─────────────────────────────────────────────────────────────
Section "1) Git / Repo state"
$gitBranch = TryRun "git branch" { git branch --show-current }
$gitSha    = TryRun "git SHA"    { git rev-parse HEAD }
$gitStatus = TryRun "git status" { git status }
$gitDiff   = TryRun "git diff"   { git diff --stat }

"### Git state"                                     | Add-Content $report
"**Branch:** $($gitBranch.out.Trim())"              | Add-Content $report
"**SHA:** $($gitSha.out.Trim())"                    | Add-Content $report
""                                                  | Add-Content $report
AppendFenced "" ($gitStatus.out + $gitDiff.out)

# ── 2) Environment ───────────────────────────────────────────────────────────
Section "2) Environment"
$pyVer   = TryRun "python"  { python --version }
$pipVer  = TryRun "pip"     { python -m pip --version }
$nodeVer = TryRun "node"    { node --version }
$npmVer  = TryRun "npm"     { npm --version }

"### Environment"                                   | Add-Content $report
AppendFenced "" ($pyVer.out + $pipVer.out + $nodeVer.out + $npmVer.out)

# ── 3) Backend audit ─────────────────────────────────────────────────────────
Section "3) Backend audit"
Push-Location ".\backend"

$venvPy = "C:\Users\JMega\OneDrive\Desktop\Crown2026\.venv\Scripts\python.exe"
if (!(Test-Path $venvPy)) { $venvPy = "python" }

$reqPath = "..\requirements.txt"
if (Test-Path $reqPath) {
  $hasPA = & $venvPy -m pip show pip-audit 2>$null
  if ($hasPA) {
    $pipAudit = RunWithTimeout "pip-audit" 90 {
      $py = "C:\Users\JMega\OneDrive\Desktop\Crown2026\.venv\Scripts\python.exe"
      if (!(Test-Path $py)) { $py = "python" }
      & $py -m pip_audit -r "C:\Users\JMega\OneDrive\Desktop\Crown2026\requirements.txt" 2>&1
    }
  } else {
    $pipAudit = @{ ok=$false; out="pip-audit not installed - skipping" }
  }
} else {
  $pipAudit = @{ ok=$false; out="requirements.txt not found" }
}

$hasB = & $venvPy -m pip show bandit 2>$null
if ($hasB) {
  $bandit = RunWithTimeout "bandit" 60 {
    $py = "C:\Users\JMega\OneDrive\Desktop\Crown2026\.venv\Scripts\python.exe"
    if (!(Test-Path $py)) { $py = "python" }
    Set-Location "C:\Users\JMega\OneDrive\Desktop\Crown2026\backend"
    & $py -m bandit -r . -q -ll 2>&1
  }
} else {
  $bandit = @{ ok=$false; out="bandit not installed - skipping" }
}

$pytest = RunWithTimeout "pytest" 120 {
  Set-Location "C:\Users\JMega\OneDrive\Desktop\Crown2026\backend"
  $py = "C:\Users\JMega\OneDrive\Desktop\Crown2026\.venv\Scripts\python.exe"
  if (!(Test-Path $py)) { $py = "python" }
  & $py -m pytest -q --tb=no -x 2>&1
}

Pop-Location

"### Backend: security + tests"                     | Add-Content $report
AppendFenced "#### pip-audit"  $pipAudit.out
AppendFenced "#### bandit"     $bandit.out
AppendFenced "#### pytest"     $pytest.out

# ── 4) Frontend audit ────────────────────────────────────────────────────────
Section "4) Frontend audit"

# Find frontend root with package.json
$feRoot = ".\frontend\dashboards"
if (!(Test-Path "$feRoot\package.json")) { $feRoot = ".\frontend" }
Push-Location $feRoot
$feActual = (Get-Location).Path   # capture for background jobs

if (!(Test-Path ".\node_modules")) {
  $npmI = @{ ok=$false; out="node_modules not found - run 'npm ci' manually before auditing" }
} else {
  $npmI = @{ ok=$true; out="node_modules present - skipped npm ci" }
}

$npmAudit  = RunWithTimeout "npm audit"     60  { Set-Location $using:feActual; npm audit --audit-level=high 2>&1 }
$lint      = RunWithTimeout "npm lint"      30  { Set-Location $using:feActual; npm run -s lint 2>&1 }
$typecheck = RunWithTimeout "npm typecheck" 30  { Set-Location $using:feActual; npm run -s typecheck 2>&1 }
$npmTest   = RunWithTimeout "npm test"      60  { Set-Location $using:feActual; npm test --silent 2>&1 }
$build     = RunWithTimeout "npm build"     90  { Set-Location $using:feActual; npm run -s build 2>&1 }

Pop-Location

"### Frontend: audit + quality gates"               | Add-Content $report
AppendFenced "#### npm install"    $npmI.out
AppendFenced "#### npm audit"      $npmAudit.out
AppendFenced "#### lint"           $lint.out
AppendFenced "#### typecheck"      $typecheck.out
AppendFenced "#### test"           $npmTest.out
AppendFenced "#### build"          $build.out

# ── 5) Dashboards deep scan ───────────────────────────────────────────────────
Section "5) Dashboards deep scan"
"### Dashboards module forensic output"             | Add-Content $report

function Scan($label, $block) {
  $r = TryRun $label $block
  AppendFenced "#### $label" $r.out
}

Scan "Locate dashboards directories" {
  Get-ChildItem -Recurse -Filter "dashboards" -Directory |
    Select-Object -First 20 FullName | Format-Table | Out-String
}

Scan "Tenant header usage (X-School-Id)" {
  Get-ChildItem -Recurse -Path ".\backend" -Filter "*.py" |
    Select-String -Pattern "X-School-Id|HTTP_X_SCHOOL_ID|CANONICAL_SCHOOL_HEADER" -SimpleMatch |
    Select-Object -First 100 | Format-Table Filename,LineNumber,Line -AutoSize | Out-String
}

Scan "ALLOW_DEMO_ROLE_HEADER references" {
  Get-ChildItem -Recurse -Path ".\backend",".\frontend" -Include "*.py","*.js","*.jsx","*.ts","*.tsx" |
    Select-String -Pattern "ALLOW_DEMO_ROLE_HEADER|X-Demo-Role" -SimpleMatch |
    Select-Object -First 50 | Format-Table Filename,LineNumber,Line -AutoSize | Out-String
}

Scan "Widget key references" {
  Get-ChildItem -Recurse -Path ".\frontend",".\backend" -Include "*.jsx","*.tsx","*.py" |
    Select-String -Pattern "alerts_flip|missing_work|grades_trend|quick_actions|balances|enrollment_snapshot" -SimpleMatch |
    Select-Object -First 100 | Format-Table Filename,LineNumber,Line -AutoSize | Out-String
}

Scan "WidgetDispatcher coverage" {
  Get-Content ".\frontend\dashboards\src\components\dashboard\WidgetDispatcher.jsx" -ErrorAction SilentlyContinue | Out-String
}

Scan "Dashboard URL registrations" {
  Get-Content ".\backend\crown_api\dashboards\urls.py" -ErrorAction SilentlyContinue | Out-String
}

Scan "RoleDashboardPage exists" {
  Test-Path ".\frontend\dashboards\src\pages\RoleDashboardPage.jsx" | Out-String
}

Scan "Contract test exists" {
  Test-Path ".\backend\crown_api\tests\test_dashboards_role_contract.py" | Out-String
}

Scan "Playwright dashboard tests" {
  Get-ChildItem -Recurse -Path ".\frontend" -Filter "*dashboard*spec*" -ErrorAction SilentlyContinue |
    Select-Object FullName | Format-Table | Out-String
}

Scan "summary.py widget builders" {
  Get-Content ".\backend\crown_api\dashboards\summary.py" -ErrorAction SilentlyContinue |
    Select-String -Pattern "^def |ROLE_WIDGETS|role.*widget" -SimpleMatch | Out-String
}

Scan "Tenant scope in views.py" {
  Get-Content ".\backend\crown_api\dashboards\views.py" -ErrorAction SilentlyContinue |
    Select-String -Pattern "get_dashboard_school_id|school_id|_resolve_role" -SimpleMatch | Out-String
}

# ── 6) Summary verdict ────────────────────────────────────────────────────────
Section "6) Summary verdict"
$failures = @()
if (-not $pytest.ok)   { $failures += "Backend pytest failed or errored" }
if ($pipAudit.ok -and ($pipAudit.out -match "VULNERABLE|Vulnerability|HIGH|CRITICAL")) {
  $failures += "pip-audit found vulnerabilities"
}
if ($npmAudit.ok -and ($npmAudit.out -match "high|critical")) {
  $failures += "npm audit found high/critical vulnerabilities"
}

"## Summary"                                        | Add-Content $report
if ($failures.Count -eq 0) {
  "PASS - No hard-stops detected (review findings above for soft issues)." | Add-Content $report
} else {
  "FAIL - Hard-stops detected:"                     | Add-Content $report
  foreach ($f in $failures) { "- $f"               | Add-Content $report }
}
""                                                  | Add-Content $report
"Artifacts: $report"                               | Add-Content $report

Write-Host ""
Write-Host "Done. Report written to: $report"

