# PowerShell 5.1 compatible.
# Master orchestrator: Azure spike + API probe + Playwright UI audit.
# Writes artifacts/demo_audit/audit_report.md and audit_report.json
param(
  [string]$ApiBase = $env:CROWN_API_BASE,
  [string]$UiBase  = $env:CROWN_UI_BASE,
  [string]$SchoolId = $env:CROWN_SCHOOL_ID,
  [string]$TenantHeader = $(if ($env:CROWN_TENANT_HEADER) { $env:CROWN_TENANT_HEADER } else { "X-School-Id" }),
  [switch]$SkipUI,
  [switch]$SkipAPI,
  [switch]$SkipSpike
)

Set-StrictMode -Off
$ErrorActionPreference = "Stop"

function Assert-NotEmpty([string]$name, [string]$value) {
  if ([string]::IsNullOrWhiteSpace($value)) { throw "Missing required setting: $name" }
}
Assert-NotEmpty "CROWN_API_BASE (or -ApiBase)" $ApiBase
Assert-NotEmpty "CROWN_UI_BASE (or -UiBase)" $UiBase

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$artDir = Join-Path $repoRoot "artifacts\demo_audit"
if (!(Test-Path $artDir)) { New-Item -ItemType Directory -Path $artDir | Out-Null }

$reportMd  = Join-Path $artDir "audit_report.md"
$reportJson = Join-Path $artDir "audit_report.json"

$results = New-Object System.Collections.ArrayList
$passCount = 0
$warnCount = 0
$failCount = 0

function Add-Result([string]$level, [string]$name, [string]$detail) {
  $obj = [pscustomobject]@{
    level = $level
    name = $name
    detail = $detail
    ts_utc = (Get-Date).ToUniversalTime().ToString("o")
  }
  [void]$results.Add($obj)
  if ($level -eq "PASS") { $script:passCount++ }
  elseif ($level -eq "WARN") { $script:warnCount++ }
  elseif ($level -eq "FAIL") { $script:failCount++ }
}

function Curl-Status([string]$url, [hashtable]$headers) {
  $hargs = @()
  if ($headers) {
    foreach ($k in $headers.Keys) { $hargs += @("-H", "$k: $($headers[$k])") }
  }
  $code = & curl.exe -s -o NUL -w "%{http_code}" $hargs $url
  return [int]$code
}

Write-Host "=== CROWN DEMO AUDIT (FULL FUNCTIONAL) ==="
Write-Host "API: $ApiBase"
Write-Host "UI : $UiBase"
if ($SchoolId) { Write-Host "Tenant: $TenantHeader=$SchoolId" } else { Write-Host "Tenant: (none provided)" }
Write-Host ""

# A) Basic availability
try {
  $hCode = Curl-Status "$ApiBase/api/health/" $null
  if ($hCode -eq 200) { Add-Result "PASS" "[A] API /api/health/ reachable" "HTTP 200" }
  else { Add-Result "FAIL" "[A] API /api/health/ reachable" "HTTP $hCode" }
} catch {
  Add-Result "FAIL" "[A] API /api/health/ reachable" $_.Exception.Message
}

try {
  $uiCode = Curl-Status $UiBase $null
  if ($uiCode -ge 200 -and $uiCode -lt 400) { Add-Result "PASS" "[A] UI base reachable" "HTTP $uiCode" }
  else { Add-Result "FAIL" "[A] UI base reachable" "HTTP $uiCode (possible 503 spike / startup issue)" }
} catch {
  Add-Result "FAIL" "[A] UI base reachable" $_.Exception.Message
}

# B) Spike test (UI stability)
if (!$SkipSpike) {
  Write-Host ""
  Write-Host "=== Running UI spike test (503 detector) ==="
  try {
    $spikeScript = Join-Path $PSScriptRoot "azure_spike.ps1"
    $spikeOut = & PowerShell -ExecutionPolicy Bypass -File $spikeScript -Url $UiBase -Seconds 60 2>&1
    $spikeLog = Join-Path $artDir "spike_log.txt"
    [System.IO.File]::WriteAllText($spikeLog, ($spikeOut | Out-String), [System.Text.Encoding]::UTF8)

    if ($LASTEXITCODE -eq 0) { Add-Result "PASS" "[B] UI spike test" "No 503/timeouts observed (see spike_log.txt)" }
    else { Add-Result "FAIL" "[B] UI spike test" "Detected 503/timeouts (see spike_log.txt)" }
  } catch {
    Add-Result "FAIL" "[B] UI spike test" $_.Exception.Message
  }
} else {
  Add-Result "WARN" "[B] UI spike test" "Skipped by flag"
}

# C) API probe (role-based endpoints + schema)
if (!$SkipAPI) {
  Write-Host ""
  Write-Host "=== Running API functional probe (roles + widgets) ==="
  try {
    $probeScript = Join-Path $PSScriptRoot "api_probe.ps1"
    $probeOut = & PowerShell -ExecutionPolicy Bypass -File $probeScript -ApiBase $ApiBase -SchoolId $SchoolId -TenantHeader $TenantHeader -OutDir $artDir 2>&1
    $probeLog = Join-Path $artDir "api_probe_log.txt"
    [System.IO.File]::WriteAllText($probeLog, ($probeOut | Out-String), [System.Text.Encoding]::UTF8)

    if ($LASTEXITCODE -eq 0) { Add-Result "PASS" "[C] API probe" "All endpoints OK (see api_probe_log.txt + api_probe_results.json)" }
    else { Add-Result "FAIL" "[C] API probe" "Endpoint failures (see api_probe_log.txt + api_probe_results.json)" }
  } catch {
    Add-Result "FAIL" "[C] API probe" $_.Exception.Message
  }
} else {
  Add-Result "WARN" "[C] API probe" "Skipped by flag"
}

# D) UI Playwright (roles + nav + network errors)
if (!$SkipUI) {
  Write-Host ""
  Write-Host "=== Running Playwright UI audit (network errors are FAIL) ==="
  try {
    $feDir = Join-Path $repoRoot "frontend\dashboards"
    if (!(Test-Path $feDir)) { throw "Frontend directory not found: $feDir" }
    Push-Location $feDir

    $env:CROWN_UI_BASE = $UiBase
    $env:CROWN_API_BASE = $ApiBase
    if ($SchoolId) { $env:CROWN_SCHOOL_ID = $SchoolId }
    $env:CROWN_TENANT_HEADER = $TenantHeader

    $pwOut = & npx playwright test tests/ui/demo-audit.spec.ts --reporter=line --workers=1 2>&1
    $pwLog = Join-Path $artDir "playwright_demo_audit.txt"
    [System.IO.File]::WriteAllText($pwLog, ($pwOut | Out-String), [System.Text.Encoding]::UTF8)

    Pop-Location

    if ($LASTEXITCODE -eq 0) { Add-Result "PASS" "[D] Playwright UI audit" "All checks passed (see playwright_demo_audit.txt)" }
    else { Add-Result "FAIL" "[D] Playwright UI audit" "Failures detected (see playwright_demo_audit.txt)" }
  } catch {
    try { Pop-Location } catch {}
    Add-Result "FAIL" "[D] Playwright UI audit" $_.Exception.Message
  }
} else {
  Add-Result "WARN" "[D] Playwright UI audit" "Skipped by flag"
}

# REPORT
$verdict = "PASS"
if ($failCount -gt 0) { $verdict = "FAIL" }
elseif ($warnCount -gt 0) { $verdict = "WARN" }

$md = New-Object System.Text.StringBuilder
[void]$md.AppendLine("# Crown Demo Audit Report")
[void]$md.AppendLine("")
[void]$md.AppendLine("Generated UTC: $((Get-Date).ToUniversalTime().ToString('o'))")
[void]$md.AppendLine("")
[void]$md.AppendLine("## Summary")
[void]$md.AppendLine("")
[void]$md.AppendLine("* Verdict: **$verdict**")
[void]$md.AppendLine("* PASS: $passCount | WARN: $warnCount | FAIL: $failCount")
[void]$md.AppendLine("")
[void]$md.AppendLine("## Results")
[void]$md.AppendLine("")
foreach ($r in $results) {
  [void]$md.AppendLine("- **$($r.level)** $($r.name) — $($r.detail)")
}

[System.IO.File]::WriteAllText($reportMd, $md.ToString(), [System.Text.Encoding]::UTF8)
($results | ConvertTo-Json -Depth 6) | Out-File -FilePath $reportJson -Encoding ascii

Write-Host ""
Write-Host "Report written:"
Write-Host "  $reportMd"
Write-Host "  $reportJson"
Write-Host ""
Write-Host "VERDICT: $verdict (PASS=$passCount WARN=$warnCount FAIL=$failCount)"

if ($verdict -eq "FAIL") { exit 2 }
elseif ($verdict -eq "WARN") { exit 1 }
else { exit 0 }
