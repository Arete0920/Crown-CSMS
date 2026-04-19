param(
  [string]$RepoRoot = (Get-Location).Path,
  [string]$BaseUrl = "http://127.0.0.1:8000",
  [switch]$RunFullRegression,
  [switch]$RunFrontendBuild,
  [int]$FullRegressionMaxFail = 1
)

$ErrorActionPreference = "Continue"
Set-Location $RepoRoot

$evidence = "docs\audit\evidence"
$logs = "artifacts\deep-audit\logs"
New-Item -ItemType Directory -Force -Path $evidence | Out-Null
New-Item -ItemType Directory -Force -Path $logs | Out-Null

function Get-PythonExe {
  $candidates = @(
    ".venv\Scripts\python.exe",
    "venv\Scripts\python.exe",
    "backend\venv\Scripts\python.exe"
  )
  foreach ($c in $candidates) {
    if (Test-Path $c) { return (Resolve-Path $c).Path }
  }
  return "python"
}

function Add-Result {
  param(
    [string]$Check,
    [string]$Status,
    [string]$Artifact,
    [string]$Notes
  )
  $script:results += [pscustomobject]@{
    Check = $Check
    Status = $Status
    Artifact = $Artifact
    Notes = $Notes
  }
}

function Run-Capture {
  param(
    [string]$Check,
    [string]$Command,
    [string[]]$CommandArgs,
    [string]$LogPath
  )
  $start = Get-Date
  $stdout = "$LogPath.stdout"
  $stderr = "$LogPath.stderr"
  Remove-Item $LogPath,$stdout,$stderr -Force -ErrorAction SilentlyContinue
  $exitCode = 1
  try {
    $proc = Start-Process -FilePath $Command -ArgumentList $CommandArgs -NoNewWindow -Wait -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    $exitCode = $proc.ExitCode
  } catch {
    $_ | Out-String | Set-Content $stderr -Encoding UTF8
  }
  $duration = [math]::Round(((Get-Date) - $start).TotalSeconds, 2)
  if (Test-Path $stdout) { Get-Content $stdout | Set-Content $LogPath -Encoding UTF8 } else { '' | Set-Content $LogPath -Encoding UTF8 }
  if (Test-Path $stderr) {
    Add-Content $LogPath -Value "`n--- STDERR ---" -Encoding UTF8
    Get-Content $stderr | Add-Content $LogPath -Encoding UTF8
  }
  Add-Content $LogPath -Value "`n__END__ exit=$exitCode duration_seconds=$duration" -Encoding UTF8
  Remove-Item $stdout,$stderr -Force -ErrorAction SilentlyContinue
  if ($exitCode -eq 0) {
    Add-Result -Check $Check -Status "PASS" -Artifact $LogPath -Notes "duration_seconds=$duration"
  } else {
    Add-Result -Check $Check -Status "FAIL" -Artifact $LogPath -Notes "exit=$exitCode duration_seconds=$duration"
  }
}

$results = @()
$python = Get-PythonExe

if (-not $env:DJANGO_SECRET_KEY) {
  $env:DJANGO_SECRET_KEY = "deep-audit-local-secret-key"
}
if (-not $env:DATABASE_URL) {
  $env:DATABASE_URL = "sqlite:///./ci.sqlite3"
}

$script:localServerProcess = $null

function Start-LocalServerIfNeeded {
  param(
    [string]$ProbeUrl
  )

  if ($script:localServerProcess -and -not $script:localServerProcess.HasExited) {
    return $true
  }

  if (-not (Test-Path "backend\manage.py")) {
    return $false
  }

  $stdout = "$logs\LOCAL_SERVER.stdout"
  $stderr = "$logs\LOCAL_SERVER.stderr"
  Remove-Item $stdout,$stderr -Force -ErrorAction SilentlyContinue

  $script:localServerProcess = Start-Process -FilePath $python -ArgumentList @("backend\manage.py","runserver","127.0.0.1:8000","--noreload") -PassThru -NoNewWindow -RedirectStandardOutput $stdout -RedirectStandardError $stderr

  for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 1
    try {
      $probe = Invoke-WebRequest -Uri $ProbeUrl -UseBasicParsing -TimeoutSec 3
      if ($probe.StatusCode -ge 200 -and $probe.StatusCode -lt 500) {
        return $true
      }
    } catch {
      if ($script:localServerProcess.HasExited) {
        break
      }
    }
  }

  return $false
}

function Stop-LocalServer {
  if ($script:localServerProcess -and -not $script:localServerProcess.HasExited) {
    Stop-Process -Id $script:localServerProcess.Id -Force -ErrorAction SilentlyContinue
  }
}

if (Test-Path "backend\manage.py") {
  Run-Capture -Check "DJANGO_CHECK" -Command $python -CommandArgs @("backend\manage.py","check") -LogPath "$logs\DJANGO_CHECK.txt"
  Run-Capture -Check "SHOW_MIGRATIONS" -Command $python -CommandArgs @("backend\manage.py","showmigrations") -LogPath "$logs\SHOW_MIGRATIONS.txt"
} else {
  Add-Result -Check "DJANGO_CHECK" -Status "FAIL" -Artifact "" -Notes "backend\manage.py missing"
  Add-Result -Check "SHOW_MIGRATIONS" -Status "FAIL" -Artifact "" -Notes "backend\manage.py missing"
}

$openApiOut = "$evidence\openapi.yaml"
if (Test-Path "backend\manage.py") {
  & $python "backend\manage.py" "spectacular" "--file" $openApiOut *> "$logs\OPENAPI_EXPORT.txt"
  if ($LASTEXITCODE -eq 0 -and (Test-Path $openApiOut)) {
    Add-Result -Check "OPENAPI_EXPORT" -Status "PASS" -Artifact $openApiOut -Notes ""
  } else {
    & $python "backend\manage.py" "generateschema" "--file" $openApiOut *> "$logs\OPENAPI_EXPORT.txt"
    if ($LASTEXITCODE -eq 0 -and (Test-Path $openApiOut)) {
      Add-Result -Check "OPENAPI_EXPORT" -Status "PASS" -Artifact $openApiOut -Notes "generated via generateschema"
    } else {
      Add-Result -Check "OPENAPI_EXPORT" -Status "FAIL" -Artifact "$logs\OPENAPI_EXPORT.txt" -Notes "schema export failed"
    }
  }
}

$criticalTests = @(
  "backend\crown_api\tests\test_students_api.py",
  "backend\finance\tests\test_finance_api.py",
  "backend\ledger\tests\test_revenue_integrity.py",
  "backend\crown_api\billing_api\tests\test_school_override_header.py",
  "backend\crown_api\billing_api\tests\test_payments_record_api.py",
  "backend\crown_api\billing_api\tests\test_payments_record_multi_alloc_api.py",
  "backend\crown_api\billing_api\tests\test_billing_audit_override_capture.py",
  "backend\outreach\tests\test_outreach.py",
  "backend\ledger\tests\test_ledger_api.py",
  "backend\ledger\tests\test_ledger_allocations_api.py",
  "backend\ledger\tests\test_ledger_write_safety.py",
  "backend\ledger\tests\test_gate2b_charge_void_reversal.py",
  "backend\ledger\tests\test_ledger_void_endpoints_api.py",
  "backend\ledger\tests\test_ledger_statements_api.py",
  "backend\ledger\tests\test_ledger_payments_correctness_api.py",
  "backend\ledger\tests\test_ledger_invariants.py"
) | Where-Object { Test-Path $_ }

if ($criticalTests.Count -gt 0) {
  Run-Capture -Check "CRITICAL_TEST_CLUSTER" -Command $python -CommandArgs (@("-m","pytest") + $criticalTests + @("-q")) -LogPath "$logs\CRITICAL_TEST_CLUSTER.txt"
} else {
  Add-Result -Check "CRITICAL_TEST_CLUSTER" -Status "FAIL" -Artifact "" -Notes "no critical tests found"
}

if ($RunFullRegression) {
  $fullRegressionArgs = @("-m","pytest","backend","-q")
  if ($FullRegressionMaxFail -gt 0) {
    $fullRegressionArgs += "--maxfail=$FullRegressionMaxFail"
  }
  Run-Capture -Check "FULL_BACKEND_REGRESSION" -Command $python -CommandArgs $fullRegressionArgs -LogPath "$logs\FULL_BACKEND_REGRESSION.txt"
} else {
  Add-Result -Check "FULL_BACKEND_REGRESSION" -Status "FAIL" -Artifact "" -Notes "not run; use -RunFullRegression"
}

$preferredFrontendPackage = "frontend\dashboards\package.json"
$packageJson = $null
if (Test-Path $preferredFrontendPackage) {
  $packageJson = Get-Item $preferredFrontendPackage
} else {
  $packageJson = Get-ChildItem "frontend" -Recurse -File -Filter package.json -ErrorAction SilentlyContinue | Select-Object -First 1
}
if ($packageJson) {
  $frontendDir = Split-Path $packageJson.FullName -Parent
  if ($RunFrontendBuild) {
    $lintLog = Join-Path $RepoRoot "$logs\FRONTEND_LINT.txt"
    $buildLog = Join-Path $RepoRoot "$logs\FRONTEND_BUILD.txt"
    Push-Location $frontendDir
    cmd /c npm run lint *> $lintLog
    if ($LASTEXITCODE -eq 0) {
      Add-Result -Check "FRONTEND_LINT" -Status "PASS" -Artifact "$logs\FRONTEND_LINT.txt" -Notes ""
    } else {
      Add-Result -Check "FRONTEND_LINT" -Status "FAIL" -Artifact "$logs\FRONTEND_LINT.txt" -Notes "lint failed"
    }
    cmd /c npm run build *> $buildLog
    if ($LASTEXITCODE -eq 0) {
      Add-Result -Check "FRONTEND_BUILD" -Status "PASS" -Artifact "$logs\FRONTEND_BUILD.txt" -Notes ""
    } else {
      Add-Result -Check "FRONTEND_BUILD" -Status "FAIL" -Artifact "$logs\FRONTEND_BUILD.txt" -Notes "build failed"
    }
    Pop-Location
  } else {
    Add-Result -Check "FRONTEND_LINT" -Status "FAIL" -Artifact "" -Notes "not run; use -RunFrontendBuild"
    Add-Result -Check "FRONTEND_BUILD" -Status "FAIL" -Artifact "" -Notes "not run; use -RunFrontendBuild"
  }
} else {
  Add-Result -Check "FRONTEND_LINT" -Status "FAIL" -Artifact "" -Notes "package.json not found"
  Add-Result -Check "FRONTEND_BUILD" -Status "FAIL" -Artifact "" -Notes "package.json not found"
}

try {
  $health = Invoke-WebRequest -Uri "$BaseUrl/api/health/" -UseBasicParsing -TimeoutSec 20
  $health.Content | Set-Content "$evidence\health.json" -Encoding UTF8
  Add-Result -Check "HEALTH_ENDPOINT" -Status "PASS" -Artifact "$evidence\health.json" -Notes ""
} catch {
  $started = Start-LocalServerIfNeeded -ProbeUrl "$BaseUrl/api/health/"
  if ($started) {
    try {
      $health = Invoke-WebRequest -Uri "$BaseUrl/api/health/" -UseBasicParsing -TimeoutSec 20
      $health.Content | Set-Content "$evidence\health.json" -Encoding UTF8
      Add-Result -Check "HEALTH_ENDPOINT" -Status "PASS" -Artifact "$evidence\health.json" -Notes "started local backend"
    } catch {
      $_ | Out-String | Set-Content "$logs\HEALTH_ENDPOINT.txt" -Encoding UTF8
      Add-Result -Check "HEALTH_ENDPOINT" -Status "FAIL" -Artifact "$logs\HEALTH_ENDPOINT.txt" -Notes "health endpoint unavailable"
    }
  } else {
    $_ | Out-String | Set-Content "$logs\HEALTH_ENDPOINT.txt" -Encoding UTF8
    Add-Result -Check "HEALTH_ENDPOINT" -Status "FAIL" -Artifact "$logs\HEALTH_ENDPOINT.txt" -Notes "health endpoint unavailable"
  }
}

try {
  $integrity = Invoke-WebRequest -Uri "$BaseUrl/api/integrity/" -UseBasicParsing -TimeoutSec 20
  $integrity.Content | Set-Content "$evidence\integrity.json" -Encoding UTF8
  Add-Result -Check "INTEGRITY_ENDPOINT" -Status "PASS" -Artifact "$evidence\integrity.json" -Notes ""
} catch {
  $started = Start-LocalServerIfNeeded -ProbeUrl "$BaseUrl/api/health/"
  if ($started) {
    try {
      $integrity = Invoke-WebRequest -Uri "$BaseUrl/api/integrity/" -UseBasicParsing -TimeoutSec 20
      $integrity.Content | Set-Content "$evidence\integrity.json" -Encoding UTF8
      Add-Result -Check "INTEGRITY_ENDPOINT" -Status "PASS" -Artifact "$evidence\integrity.json" -Notes "started local backend"
    } catch {
      $_ | Out-String | Set-Content "$logs\INTEGRITY_ENDPOINT.txt" -Encoding UTF8
      Add-Result -Check "INTEGRITY_ENDPOINT" -Status "FAIL" -Artifact "$logs\INTEGRITY_ENDPOINT.txt" -Notes "integrity endpoint unavailable"
    }
  } else {
    $_ | Out-String | Set-Content "$logs\INTEGRITY_ENDPOINT.txt" -Encoding UTF8
    Add-Result -Check "INTEGRITY_ENDPOINT" -Status "FAIL" -Artifact "$logs\INTEGRITY_ENDPOINT.txt" -Notes "integrity endpoint unavailable"
  }
}

$gh = Get-Command gh -ErrorAction SilentlyContinue
if ($gh) {
  gh pr list --limit 200 --json number,title,state,isDraft,headRefName,baseRefName > "$evidence\GH_PR_LIST.json" 2> "$logs\GH_PR_LIST.txt"
  if ($LASTEXITCODE -eq 0) {
    Add-Result -Check "GH_PR_LIST" -Status "PASS" -Artifact "$evidence\GH_PR_LIST.json" -Notes ""
  } else {
    Add-Result -Check "GH_PR_LIST" -Status "FAIL" -Artifact "$logs\GH_PR_LIST.txt" -Notes "gh pr list failed"
  }

  gh run list --limit 100 --json databaseId,displayTitle,status,conclusion,workflowName,headBranch,createdAt > "$evidence\GH_RUN_LIST.json" 2> "$logs\GH_RUN_LIST.txt"
  if ($LASTEXITCODE -eq 0) {
    Add-Result -Check "GH_RUN_LIST" -Status "PASS" -Artifact "$evidence\GH_RUN_LIST.json" -Notes ""
  } else {
    Add-Result -Check "GH_RUN_LIST" -Status "FAIL" -Artifact "$logs\GH_RUN_LIST.txt" -Notes "gh run list failed"
  }
}

$results | Export-Csv "$evidence\PROOF_SUMMARY.csv" -NoTypeInformation -Encoding UTF8

$md = @()
$md += "# Proof Summary"
$md += ""
$md += "| Check | Status | Artifact | Notes |"
$md += "|---|---|---|---|"
foreach ($r in $results) {
  $md += "| $($r.Check) | $($r.Status) | $($r.Artifact) | $($r.Notes) |"
}
$md | Set-Content "$evidence\PROOF_SUMMARY.md" -Encoding UTF8

Stop-LocalServer

Write-Host "Runtime checks complete."
Write-Host "Open docs\audit\evidence\PROOF_SUMMARY.csv"




