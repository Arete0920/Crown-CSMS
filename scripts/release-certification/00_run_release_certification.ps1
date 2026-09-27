param(
  [string]$RepoRoot = ".",
  [string]$EvidenceRoot = "audit-artifacts/release-certification",
  [string]$BaseUrl = "http://127.0.0.1:8000",
  [string]$FrontendUrl = "http://127.0.0.1:3000",
  [string]$RepoSlug = "Arete0920/Crown-CSMS",
  [string]$SandboxAdminEmail = "admin@heritage.test",
  [string]$SandboxAdminPassword = $env:CERT_SANDBOX_ADMIN_PASSWORD,
  [string]$SandboxSecondAdminEmail = "admin@harvest.test",
  [string]$SandboxSecondAdminPassword = $env:CERT_SANDBOX_SECOND_ADMIN_PASSWORD,
  [string]$SchoolAdminRoute = "/school-admin-dashboard",
  [string]$SwaggerPath = "/api/docs/",
  [string]$HealthPath = "/health/",
  [string]$IntegrityPath = "/api/integrity/",
  [string]$LoadHost = "",
  [switch]$SkipLoad,
  [switch]$SkipBranchProtection
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($SandboxAdminPassword) -or [string]::IsNullOrWhiteSpace($SandboxSecondAdminPassword)) { throw "Configure both sandbox admin passwords before certification." }


function Write-Section($text) {
  Write-Host ""
  Write-Host "==== $text ====" -ForegroundColor Cyan
}

function New-GateResult {
  param(
    [string]$Lane,
    [string]$Gate,
    [string]$Status,
    [string]$Evidence,
    [string]$Detail
  )
  [pscustomobject]@{
    lane     = $Lane
    gate     = $Gate
    status   = $Status
    evidence = $Evidence
    detail   = $Detail
  }
}

Set-Location $RepoRoot

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$runDir = Join-Path $EvidenceRoot $stamp
$latestDir = Join-Path $EvidenceRoot "latest"
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
New-Item -ItemType Directory -Force -Path $latestDir | Out-Null
$results = New-Object System.Collections.Generic.List[object]

Write-Section "01 Branch protection and repo controls"
try {
  $branchArgs = @(
    "-ExecutionPolicy", "Bypass",
    "-File", "scripts/release-certification/01_collect_branch_protection.ps1",
    "-OutputDir", $runDir,
    "-RepoSlug", $RepoSlug
  )
  if ($SkipBranchProtection) {
    $branchArgs += "-Skip"
  }
  & powershell @branchArgs
  if ($LASTEXITCODE -ne 0) {
    throw "Branch protection step failed"
  }
  $results.Add((New-GateResult "Security/Repo" "Branch protection export" "GREEN" "01_branch_protection.json / 01_branch_protection_manual.txt" "Collected")) | Out-Null
} catch {
  $results.Add((New-GateResult "Security/Repo" "Branch protection export" "RED" "" $_.Exception.Message)) | Out-Null
}

Write-Section "02 Backend, runtime, OpenAPI, health, integrity"
try {
  powershell -ExecutionPolicy Bypass -File "scripts/release-certification/02_run_backend_and_runtime.ps1" `
    -OutputDir $runDir `
    -BaseUrl $BaseUrl `
    -SwaggerPath $SwaggerPath `
    -HealthPath $HealthPath `
    -IntegrityPath $IntegrityPath
  if ($LASTEXITCODE -ne 0) {
    throw "Backend/runtime step failed"
  }
  $results.Add((New-GateResult "Backend/Runtime" "Deploy/runtime checks" "GREEN" "02_backend_runtime_summary.json" "Backend/runtime checks passed")) | Out-Null
} catch {
  $results.Add((New-GateResult "Backend/Runtime" "Deploy/runtime checks" "RED" "" $_.Exception.Message)) | Out-Null
}

Write-Section "03 Golden path, tenant isolation, and sandbox admin dashboard proof"
try {
  powershell -ExecutionPolicy Bypass -File "scripts/release-certification/03_run_playwright_and_golden_path.ps1" `
    -OutputDir $runDir `
    -BaseUrl $BaseUrl `
    -FrontendUrl $FrontendUrl `
    -SandboxAdminEmail $SandboxAdminEmail `
    -SandboxAdminPassword $SandboxAdminPassword `
    -SandboxSecondAdminEmail $SandboxSecondAdminEmail `
    -SandboxSecondAdminPassword $SandboxSecondAdminPassword `
    -SchoolAdminRoute $SchoolAdminRoute
  if ($LASTEXITCODE -ne 0) {
    throw "Golden path/UI step failed"
  }
  $results.Add((New-GateResult "Golden Path/UI" "Playwright + pytest proof" "GREEN" "03_playwright_summary.json / pytest outputs" "Golden path and UI proof executed")) | Out-Null
} catch {
  $results.Add((New-GateResult "Golden Path/UI" "Playwright + pytest proof" "RED" "" $_.Exception.Message)) | Out-Null
}

Write-Section "04 Load and resilience"
try {
  $loadArgs = @(
    "-ExecutionPolicy", "Bypass",
    "-File", "scripts/release-certification/04_run_load_and_resilience.ps1",
    "-OutputDir", $runDir
  )
  if ($SkipLoad) {
    $loadArgs += "-Skip"
  } elseif (-not [string]::IsNullOrWhiteSpace($LoadHost)) {
    $loadArgs += @("-LoadHost", $LoadHost)
  }
  & powershell @loadArgs
  if ($LASTEXITCODE -ne 0) {
    throw "Load/resilience step failed"
  }
  $status = if ($SkipLoad) { "AMBER" } else { "GREEN" }
  $detail = if ($SkipLoad) { "Load skipped by operator" } else { "Load executed" }
  $results.Add((New-GateResult "Performance/Resilience" "Load and resilience" $status "04_load_summary.json" $detail)) | Out-Null
} catch {
  $results.Add((New-GateResult "Performance/Resilience" "Load and resilience" "RED" "" $_.Exception.Message)) | Out-Null
}

Write-Section "06 Phase 2 gates: transcript, export, reporting, and sandbox role route regression"
try {
  powershell -ExecutionPolicy Bypass -File "scripts/release-certification/06_run_phase2_gates.ps1" `
    -OutputDir $runDir
  if ($LASTEXITCODE -ne 0) {
    throw "Phase 2 gates step failed"
  }
  $results.Add((New-GateResult "Reporting/Export/Transcript + Role Routing" "Phase 2 gates" "GREEN" "06_phase2_summary.json" "Reporting/export/transcript and role-route regression executed")) | Out-Null
} catch {
  $results.Add((New-GateResult "Reporting/Export/Transcript + Role Routing" "Phase 2 gates" "RED" "" $_.Exception.Message)) | Out-Null
}

Write-Section "07 Final signoff packet"
try {
  powershell -ExecutionPolicy Bypass -File "scripts/release-certification/07_build_final_signoff_packet.ps1" `
    -OutputDir $runDir
  if ($LASTEXITCODE -ne 0) {
    throw "Final signoff packet step failed"
  }
  $results.Add((New-GateResult "Governance/Signoff" "Final signoff packet" "GREEN" "FINAL_RELEASE_SIGNOFF_PACKET.md" "Generated")) | Out-Null
} catch {
  $results.Add((New-GateResult "Governance/Signoff" "Final signoff packet" "RED" "" $_.Exception.Message)) | Out-Null
}

Write-Section "05 Build evidence binder and final matrix"
$results | Export-Csv (Join-Path $runDir "00_release_gate_results.csv") -NoTypeInformation -Encoding UTF8
$results | ConvertTo-Json -Depth 6 | Out-File (Join-Path $runDir "00_release_gate_results.json") -Encoding utf8
powershell -ExecutionPolicy Bypass -File "scripts/release-certification/05_build_evidence_binder.ps1" `
  -OutputDir $runDir `
  -LatestDir $latestDir

$redCount = @($results | Where-Object {$_.status -eq "RED"}).Count
$amberCount = @($results | Where-Object {$_.status -eq "AMBER"}).Count
$greenCount = @($results | Where-Object {$_.status -eq "GREEN"}).Count
$final = [pscustomobject]@{
  run_dir      = $runDir
  green        = $greenCount
  amber        = $amberCount
  red          = $redCount
  release_gate = if ($redCount -eq 0 -and $amberCount -eq 0) { "PASS" } else { "FAIL" }
}
$final | ConvertTo-Json -Depth 4 | Out-File (Join-Path $runDir "00_release_certification_summary.json") -Encoding utf8

Write-Host ""
Write-Host "Release certification complete."
Write-Host ("Run dir: " + $runDir)
Write-Host ("GREEN=" + $greenCount + " AMBER=" + $amberCount + " RED=" + $redCount)
Write-Host ("FINAL=" + $final.release_gate)

if ($final.release_gate -ne "PASS") {
  exit 1
}
