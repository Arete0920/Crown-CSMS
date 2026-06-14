param(
  [string]$RepoRoot = (Get-Location).Path,
  [int]$PytestTimeoutSeconds = 900,
  [int]$WarmupTimeoutSeconds = 300,
  [switch]$RunFrontendBuild
)

$ErrorActionPreference = 'Stop'
Set-Location $RepoRoot

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$outDir = "audit-artifacts/runtime-certification-strict/$stamp"
$logDir = Join-Path $outDir 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$python = if (Test-Path '.venv\Scripts\python.exe') {
  '.\.venv\Scripts\python.exe'
} elseif (Test-Path 'venv\Scripts\python.exe') {
  '.\venv\Scripts\python.exe'
} elseif (Test-Path 'backend\venv\Scripts\python.exe') {
  '.\backend\venv\Scripts\python.exe'
} else {
  'python'
}

if (-not $env:DJANGO_SECRET_KEY) { $env:DJANGO_SECRET_KEY = 'deep-audit-local-secret-key' }
if (-not $env:DATABASE_URL) { $env:DATABASE_URL = 'sqlite:///./ci.sqlite3' }

$rows = New-Object System.Collections.Generic.List[object]

function Add-Row {
  param(
    [string]$Check,
    [string]$Status,
    [int]$ExitCode,
    [string]$Log,
    [string]$Notes = ''
  )

  $script:rows.Add([pscustomobject]@{
    Check = $Check
    Status = $Status
    ExitCode = $ExitCode
    Log = $Log
    Notes = $Notes
  }) | Out-Null
}

function Invoke-LoggedCommand {
  param(
    [string]$Check,
    [string]$Log,
    [scriptblock]$Command
  )

  try {
    & $Command *> $Log
    $exitCode = $LASTEXITCODE
    if ($null -eq $exitCode) { $exitCode = 0 }
    if ($exitCode -eq 0) {
      Add-Row -Check $Check -Status 'PASS' -ExitCode 0 -Log $Log
      return $true
    }
    Add-Row -Check $Check -Status 'FAIL' -ExitCode $exitCode -Log $Log
    return $false
  } catch {
    $_ | Out-String | Set-Content $Log -Encoding UTF8
    Add-Row -Check $Check -Status 'FAIL' -ExitCode 1 -Log $Log -Notes 'command threw PowerShell error'
    return $false
  }
}

function Invoke-Pytest {
  param(
    [string]$Check,
    [string[]]$Targets,
    [string]$Log,
    [int]$TimeoutSeconds
  )

  Invoke-LoggedCommand -Check $Check -Log $Log -Command {
    & $python -m pytest @Targets --reuse-db --nomigrations -q --tb=short --disable-warnings --maxfail=1 --timeout=$TimeoutSeconds --timeout-method=thread
  } | Out-Null
}

$warmupTarget = 'backend\crown_api\tests\test_students_api.py::StudentsApiTests::test_list_students_parent_scoped_to_household'
if (Test-Path 'backend\crown_api\tests\test_students_api.py') {
  Invoke-Pytest -Check 'PYTEST_WARMUP' -Targets @($warmupTarget) -Log (Join-Path $logDir 'pytest_warmup.log') -TimeoutSeconds $WarmupTimeoutSeconds
} else {
  Add-Row -Check 'PYTEST_WARMUP' -Status 'FAIL' -ExitCode 1 -Log '' -Notes 'students API test file missing'
}

$criticalTests = @(
  'backend\crown_api\tests\test_students_api.py',
  'backend\finance\tests\test_finance_api.py',
  'backend\ledger\tests\test_revenue_integrity.py',
  'backend\crown_api\billing_api\tests\test_school_override_header.py',
  'backend\crown_api\billing_api\tests\test_payments_record_api.py',
  'backend\crown_api\billing_api\tests\test_payments_record_multi_alloc_api.py',
  'backend\crown_api\billing_api\tests\test_billing_audit_override_capture.py',
  'backend\outreach\tests\test_outreach.py',
  'backend\ledger\tests\test_ledger_api.py',
  'backend\ledger\tests\test_ledger_allocations_api.py',
  'backend\ledger\tests\test_ledger_write_safety.py',
  'backend\ledger\tests\test_gate2b_charge_void_reversal.py',
  'backend\ledger\tests\test_ledger_void_endpoints_api.py',
  'backend\ledger\tests\test_ledger_statements_api.py',
  'backend\ledger\tests\test_ledger_payments_correctness_api.py',
  'backend\ledger\tests\test_ledger_invariants.py'
) | Where-Object { Test-Path $_ }

if ($criticalTests.Count -eq 0) {
  Add-Row -Check 'CRITICAL_TESTS' -Status 'FAIL' -ExitCode 1 -Log '' -Notes 'no critical tests found'
} else {
  foreach ($test in $criticalTests) {
    $safeName = ($test -replace '[^A-Za-z0-9_.-]', '_')
    Invoke-Pytest -Check "CRITICAL_TEST::$test" -Targets @($test) -Log (Join-Path $logDir "$safeName.log") -TimeoutSeconds $PytestTimeoutSeconds
  }
}

if ($RunFrontendBuild) {
  if (Test-Path 'frontend\dashboards\package.json') {
    Invoke-LoggedCommand -Check 'FRONTEND_LINT' -Log (Join-Path $logDir 'frontend_lint.log') -Command {
      cmd /c npm --prefix frontend\dashboards run lint
    } | Out-Null
    Invoke-LoggedCommand -Check 'FRONTEND_BUILD' -Log (Join-Path $logDir 'frontend_build.log') -Command {
      cmd /c npm --prefix frontend\dashboards run build
    } | Out-Null
  } else {
    Add-Row -Check 'FRONTEND_LINT' -Status 'FAIL' -ExitCode 1 -Log '' -Notes 'frontend dashboards package.json missing'
    Add-Row -Check 'FRONTEND_BUILD' -Status 'FAIL' -ExitCode 1 -Log '' -Notes 'frontend dashboards package.json missing'
  }
} else {
  Add-Row -Check 'FRONTEND_LINT' -Status 'SKIP' -ExitCode 0 -Log '' -Notes 'not requested; pass -RunFrontendBuild to require it'
  Add-Row -Check 'FRONTEND_BUILD' -Status 'SKIP' -ExitCode 0 -Log '' -Notes 'not requested; pass -RunFrontendBuild to require it'
}

$summary = Join-Path $outDir 'STRICT_RUNTIME_SUMMARY.csv'
$verdict = Join-Path $outDir 'VERDICT.txt'
$exitCodeFile = Join-Path $outDir 'exit_code.txt'
$rows | Export-Csv $summary -NoTypeInformation -Encoding UTF8

$bad = @($rows | Where-Object { $_.Status -eq 'FAIL' -or $_.Status -eq 'TIMEOUT' })
if ($bad.Count -eq 0) {
  'PASS' | Set-Content $verdict -Encoding UTF8
  '0' | Set-Content $exitCodeFile -Encoding UTF8
  "OUT_DIR=$outDir"
  'VERDICT=PASS'
  exit 0
}

'FAIL' | Set-Content $verdict -Encoding UTF8
'1' | Set-Content $exitCodeFile -Encoding UTF8
"OUT_DIR=$outDir"
'VERDICT=FAIL'
"FAIL_COUNT=$($bad.Count)"
$bad | Format-Table Check,Status,ExitCode,Log,Notes -AutoSize | Out-String
exit 1
