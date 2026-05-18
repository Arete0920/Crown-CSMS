#!/usr/bin/env pwsh
Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

$STAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$OUT = "audit-artifacts/final-scorecard/$STAMP"
New-Item -ItemType Directory -Force -Path $OUT | Out-Null

function Run-Step($Name, $Command) {
  $safe = $Name -replace "[^a-zA-Z0-9]+", "_"
  $log = "$OUT/$safe.txt"

  "COMMAND: $Command" | Out-File $log
  Invoke-Expression $Command *>> $log
  $code = $LASTEXITCODE

  if ($null -eq $code) { $code = 0 }

  [PSCustomObject]@{
    Name = $Name
    Command = $Command
    ExitCode = $code
    Log = $log
  }
}

$results = @()
$results += Run-Step "django_check" "python backend/manage.py check"
$results += Run-Step "migration_drift" "python backend/manage.py makemigrations --check --dry-run"
$results += Run-Step "accounting_tests" "python backend/manage.py test apps.accounting"
$results += Run-Step "readiness_check" "python backend/manage.py crown_readiness_check"

Push-Location frontend/dashboards
$results += Run-Step "frontend_build" "npm run build"
$results += Run-Step "frontend_tests" "npm test"
Pop-Location

$pass = ($results | Where-Object { $_.ExitCode -eq 0 }).Count
$total = $results.Count
$score = [math]::Round(($pass / $total) * 100, 2)

@"
# CROWN2026 Final Production Scorecard

Generated: $(Get-Date -Format o)
HEAD: $(git rev-parse HEAD)

| Gate | Exit Code | Log |
|---|---:|---|
$($results | ForEach-Object { "| $($_.Name) | $($_.ExitCode) | $($_.Log) |" } | Out-String)

## Automated Gate Score

$score / 100

## Decision

$(if ($score -ge 95) { "GO CANDIDATE" } else { "NO-GO UNTIL FAILING GATES CLOSE" })
"@ | Set-Content "$OUT/FINAL_SCORECARD.md"

Get-Content "$OUT/FINAL_SCORECARD.md"
