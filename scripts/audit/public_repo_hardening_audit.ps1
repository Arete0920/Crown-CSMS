$ErrorActionPreference = "Stop"

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$out = "audit-artifacts/public-repo-hardening-audit/$stamp"
New-Item -ItemType Directory -Force -Path $out | Out-Null

$checks = New-Object System.Collections.Generic.List[object]

function Add-Check {
  param(
    [string] $Name,
    [bool] $Pass,
    [string] $Detail
  )

  $checks.Add([pscustomobject]@{
    Check = $Name
    Pass = $Pass
    Detail = $Detail
  })
}

$forbidden = @("debug_auth.py", "test_custom_login.py", "seed_a535.py", "seed_a535_clean.py")
foreach ($f in $forbidden) {
  Add-Check "Forbidden root file absent: $f" (-not (Test-Path $f)) $f
}

$required = @(
  "README.md",
  "SECURITY.md",
  "docs/PUBLIC_REPO_STATUS.md",
  "docs/KNOWN_LIMITATIONS.md",
  "docs/release/README.md",
  "docs/governance/GITHUB_REQUIRED_CHECKS.md",
  "docs/dashboard/DASHBOARD_PRODUCTION_GATE.md",
  "docs/engineering/PUBLIC_REPO_HARDENING.md",
  ".env.example",
  ".github/CODEOWNERS",
  ".github/workflows/public-repo-quality-gate.yml"
)
foreach ($f in $required) {
  Add-Check "Required file present: $f" (Test-Path $f) $f
}

$trackedEnv = git ls-files |
  Select-String -Pattern '(^|/)\.env($|\.|/)' |
  Where-Object { $_.Line -notmatch '(^|/)\.env(\.[A-Za-z0-9_-]+)?\.(example|sample)$' }
Add-Check "No tracked env files except approved env examples/samples" (-not $trackedEnv) (($trackedEnv | ForEach-Object Line) -join "; ")

$checks | Export-Csv "$out/public_repo_hardening_audit.csv" -NoTypeInformation
$failed = $checks | Where-Object { -not $_.Pass }

"=== PUBLIC REPO HARDENING AUDIT ===" | Out-File "$out/summary.txt"
"Generated: $stamp" | Add-Content "$out/summary.txt"
"Total: $($checks.Count)" | Add-Content "$out/summary.txt"
"Passed: $(($checks | Where-Object Pass).Count)" | Add-Content "$out/summary.txt"
"Failed: $($failed.Count)" | Add-Content "$out/summary.txt"

if ($failed) {
  Write-Host "Public repo hardening audit FAILED. See $out" -ForegroundColor Red
  exit 1
}

Write-Host "Public repo hardening audit PASSED. See $out" -ForegroundColor Green
