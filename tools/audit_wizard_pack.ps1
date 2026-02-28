<#
CrownMagus — Post-Wizard Pack #20-#24 Integrity Audit
Audits the current branch (feat/wizard-pack-20-24 / PR #465).
Does NOT switch to main — audits the feature branch state.
#>

$ErrorActionPreference = "Stop"

$ts = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$REPORT_PATH = "AUDIT_REPORT_$ts.md"

$global:REPORT    = @"
# CrownMagus — Wizard Pack #20-#24 Integrity Audit
- **Timestamp**: $ts
- **Branch**: $(git branch --show-current)
- **HEAD SHA**: $(git rev-parse HEAD)
- **PR**: #465 (feat/wizard-pack-20-24 → main)

"@
$global:SUCCESSES = @()
$global:FAILURES  = @()
$global:WARNINGS  = @()

function Write-Section([string]$t) {
  $sep = "=" * 80
  Write-Host "`n$sep`n  $t`n$sep"
}

function Add-Section([string]$header, [string]$body) {
  $global:REPORT += "`n## $header`n`n``````text`n$body`n``````n`n"
}

function Gate([string]$label, [int]$code) {
  if ($code -eq 0) { $global:SUCCESSES += "- ✅ PASS: $label" }
  else             { $global:FAILURES  += "- ❌ FAIL: $label (exit=$code)" }
}

# ──────────────────────────────────────────────────────────────────────────────
Write-Section "A) Git Snapshot"
$gitLog = git log --oneline -10 2>&1 | Out-String
$gitStat = git diff --stat HEAD~1 HEAD 2>&1 | Out-String
Add-Section "A) Git Snapshot" "$gitLog`n--- diff stat ---`n$gitStat"
Write-Host $gitLog

# ──────────────────────────────────────────────────────────────────────────────
Write-Section "B) Django System Check"
$checkOut = & ".venv\Scripts\python.exe" backend\manage.py check 2>&1 | Out-String
$checkExit = $LASTEXITCODE
Add-Section "B) manage.py check" $checkOut
Gate "manage.py check" $checkExit
Write-Host $checkOut.Trim()

if ($checkExit -ne 0) {
  Write-Host "FATAL: system check failed — aborting"
  $global:REPORT += "`n## Gates Summary`n" + ($global:SUCCESSES -join "`n") + "`n" + ($global:FAILURES -join "`n")
  Set-Content -Path $REPORT_PATH -Value $global:REPORT -Encoding UTF8
  exit 1
}

# ──────────────────────────────────────────────────────────────────────────────
Write-Section "C) Wizard Contract + Discovery (core contract suite)"
$contractOut = & ".venv\Scripts\python.exe" -m pytest `
  backend/tests/test_wizard_contract.py `
  backend/tests/test_wizard_discovery.py `
  -v --tb=short 2>&1 | Out-String
$contractExit = $LASTEXITCODE
Add-Section "C) Wizard Contract + Discovery" $contractOut
Gate "pytest wizard_contract+discovery" $contractExit
Write-Host $contractOut

# ──────────────────────────────────────────────────────────────────────────────
Write-Section "D) New Wizard App Tests (#20-#24)"
$newTestOut = & ".venv\Scripts\python.exe" -m pytest `
  backend/staff_setup_wizard/tests/ `
  backend/course_catalog_wizard/tests/ `
  backend/room_setup_wizard/tests/ `
  backend/promotion_wizard/tests/ `
  backend/section_scheduler_wizard/tests/ `
  -v --tb=short 2>&1 | Out-String
$newTestExit = $LASTEXITCODE
Add-Section "D) New Wizard App Tests" $newTestOut
Gate "pytest wizard-pack-20-24 apps" $newTestExit
Write-Host $newTestOut

# ──────────────────────────────────────────────────────────────────────────────
Write-Section "E) Migration Integrity"
$migOut = & ".venv\Scripts\python.exe" backend\manage.py showmigrations `
  staff_setup_wizard course_catalog_wizard room_setup_wizard `
  promotion_wizard section_scheduler_wizard 2>&1 | Out-String
Add-Section "E) showmigrations (new apps)" $migOut
Write-Host $migOut

# Fingerprint all 0001_initial.py files 
$fpOut = Get-ChildItem backend\*\migrations\0001_initial.py -ErrorAction SilentlyContinue |
  ForEach-Object {
    $h = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
    "$($_.FullName.Replace((Get-Location).Path,''))  $h"
  } | Sort-Object | Out-String
Add-Section "E2) 0001_initial.py SHA256 Fingerprints" $fpOut

# ──────────────────────────────────────────────────────────────────────────────
Write-Section "F) URL Surface Spot-Check (show_urls)"
$urlOut = & ".venv\Scripts\python.exe" backend\manage.py show_urls 2>&1 |
  Select-String "section-scheduler|staff-setup|course-catalog|room-setup|promotion-wizard" |
  Out-String
Add-Section "F) New Wizard URL Routes" ($urlOut | Out-String)
Write-Host $urlOut

# ──────────────────────────────────────────────────────────────────────────────
Write-Section "G) Tenant Isolation Tripwire"
if (Test-Path "tools\verify_backend_gate.py") {
  $gateOut = & ".venv\Scripts\python.exe" tools\verify_backend_gate.py 2>&1 | Out-String
  $gateExit = $LASTEXITCODE
  Add-Section "G) verify_backend_gate.py" $gateOut
  Gate "verify_backend_gate.py" $gateExit
  Write-Host $gateOut
} else {
  $global:WARNINGS += "- ⚠️ WARN: tools\verify_backend_gate.py not found"
  Add-Section "G) Tenant Tripwires" "tools\verify_backend_gate.py not found — skipped"
}

# ──────────────────────────────────────────────────────────────────────────────
Write-Section "H) Security Grep (pattern scan)"
$secOut = Select-String `
  -Path "backend\**\*.py" `
  -Pattern "BEGIN PRIVATE KEY|AKIA[A-Z0-9]{16}|password\s*=\s*['\`"][^'\`"]{6}|-----BEGIN RSA" `
  -ErrorAction SilentlyContinue |
  Where-Object { $_.Path -notmatch "migrations|tests" } |
  Select-Object Path, LineNumber, Line |
  Select-Object -First 50 | Out-String
Add-Section "H) Security Pattern Scan" (if ($secOut) { $secOut } else { "No high-risk patterns found." })
Write-Host "Security scan: $( if ($secOut.Trim()) { 'HITS found — see report' } else { 'Clean' })"

# ──────────────────────────────────────────────────────────────────────────────
Write-Section "I) Frontend Build"
Push-Location frontend\dashboards
$npmOut = npm run build 2>&1 | Out-String
$npmExit = $LASTEXITCODE
Pop-Location
Add-Section "I) npm run build" "$npmOut`nEXIT:$npmExit"
Gate "npm run build" $npmExit
Write-Host "npm build EXIT:$npmExit"

# ──────────────────────────────────────────────────────────────────────────────
Write-Section "J) Registry Coherence Check"
$regPy = @"
import sys, os
sys.path.insert(0, 'backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
import django; django.setup()
from crown_api.wizard_registry import WIZARDS
expected = {'section_scheduler_wizard', 'staff_setup_wizard', 'course_catalog_wizard', 'room_setup_wizard', 'promotion_wizard'}
found = {w['urls_module'].split('.')[0] for w in WIZARDS}
missing = expected - found
if missing:
    print('MISSING FROM REGISTRY:', missing)
    sys.exit(1)
else:
    print('All 5 new wizards present in registry. Total WIZARDS:', len(WIZARDS))
    sys.exit(0)
"@
$regOut = & ".venv\Scripts\python.exe" -c $regPy 2>&1 | Out-String
$regExit = $LASTEXITCODE
Add-Section "J) Registry Coherence" $regOut
Gate "wizard_registry coherence" $regExit
Write-Host $regOut.Trim()

# ──────────────────────────────────────────────────────────────────────────────
Write-Section "SUMMARY"

$global:REPORT += @"

## Gates Summary

### ✅ Passes
$($global:SUCCESSES -join "`n")

### ⚠️ Warnings
$($global:WARNINGS -join "`n")

### ❌ Failures
$($global:FAILURES -join "`n")
"@

Set-Content -Path $REPORT_PATH -Value $global:REPORT -Encoding UTF8

Write-Host "`nREPORT: $REPORT_PATH"
Write-Host "PASSES : $($global:SUCCESSES.Count)"
Write-Host "WARNINGS: $($global:WARNINGS.Count)"
Write-Host "FAILURES: $($global:FAILURES.Count)"

if ($global:FAILURES.Count -gt 0) {
  Write-Host "`nFAILURES detected — see $REPORT_PATH"
  exit 1
}
Write-Host "`nAll gates passed."
exit 0
