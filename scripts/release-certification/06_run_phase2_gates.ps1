param(
  [string]$OutputDir
)

$ErrorActionPreference = "Stop"

$resolvedOutputDir = (Resolve-Path $OutputDir).Path

$defaultGateTimeoutSec = 420
if (-not [string]::IsNullOrWhiteSpace($env:CROWN_PHASE2_GATE_TIMEOUT_SEC)) {
  [int]$parsedGateTimeout = 0
  if ([int]::TryParse($env:CROWN_PHASE2_GATE_TIMEOUT_SEC, [ref]$parsedGateTimeout) -and $parsedGateTimeout -gt 0) {
    $defaultGateTimeoutSec = $parsedGateTimeout
  }
}

$backendTimeoutSec = $defaultGateTimeoutSec
if (-not [string]::IsNullOrWhiteSpace($env:CROWN_STEP06_BACKEND_TIMEOUT_SEC)) {
  [int]$parsedBackendTimeout = 0
  if ([int]::TryParse($env:CROWN_STEP06_BACKEND_TIMEOUT_SEC, [ref]$parsedBackendTimeout) -and $parsedBackendTimeout -gt 0) {
    $backendTimeoutSec = $parsedBackendTimeout
  }
}

$playwrightTimeoutSec = $defaultGateTimeoutSec
if (-not [string]::IsNullOrWhiteSpace($env:CROWN_STEP06_PLAYWRIGHT_TIMEOUT_SEC)) {
  [int]$parsedPlaywrightTimeout = 0
  if ([int]::TryParse($env:CROWN_STEP06_PLAYWRIGHT_TIMEOUT_SEC, [ref]$parsedPlaywrightTimeout) -and $parsedPlaywrightTimeout -gt 0) {
    $playwrightTimeoutSec = $parsedPlaywrightTimeout
  }
}

$heartbeatIntervalSec = 15
if (-not [string]::IsNullOrWhiteSpace($env:CROWN_PHASE2_HEARTBEAT_SEC)) {
  [int]$parsedHeartbeat = 0
  if ([int]::TryParse($env:CROWN_PHASE2_HEARTBEAT_SEC, [ref]$parsedHeartbeat) -and $parsedHeartbeat -gt 0) {
    $heartbeatIntervalSec = $parsedHeartbeat
  }
}

$heartbeatFile = Join-Path $resolvedOutputDir "06_phase2_heartbeat.log"

function Write-Heartbeat {
  param(
    [string]$Message
  )
  $ts = (Get-Date).ToString("s")
  Add-Content -Path $heartbeatFile -Value ("[{0}] {1}" -f $ts, $Message) -Encoding utf8
}

function Resolve-CrownExecutable {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Exe
  )

  if ($IsWindows -or $env:OS -eq "Windows_NT") {
    switch -Regex ($Exe) {
      '^npm(\.cmd)?$' { return 'npm.cmd' }
      '^npx(\.cmd)?$' { return 'npx.cmd' }
      default { return $Exe }
    }
  }

  return $Exe
}

function Invoke-TimeboxedProcess {
  param(
    [string]$Name,
    [string]$FilePath,
    [string[]]$ArgumentList,
    [string]$WorkingDirectory,
    [string]$StdOutFile,
    [string]$StdErrFile,
    [int]$TimeoutSec,
    [int]$HeartbeatSec
  )

  $startedAt = Get-Date
  Write-Heartbeat ("STEP_START name={0} timeout_sec={1}" -f $Name, $TimeoutSec)

  $proc = Start-Process -FilePath $FilePath -ArgumentList $ArgumentList -WorkingDirectory $WorkingDirectory -RedirectStandardOutput $StdOutFile -RedirectStandardError $StdErrFile -PassThru

  $deadline = (Get-Date).AddSeconds($TimeoutSec)
  $timedOut = $false
  while (-not $proc.HasExited) {
    if ((Get-Date) -ge $deadline) {
      $timedOut = $true
      break
    }

    $proc.WaitForExit($HeartbeatSec * 1000) | Out-Null
    if (-not $proc.HasExited) {
      $elapsedSec = [math]::Round(((Get-Date) - $startedAt).TotalSeconds, 1)
      Write-Heartbeat ("STEP_RUNNING name={0} elapsed_sec={1}" -f $Name, $elapsedSec)
    }
  }

  if ($timedOut) {
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
  }

  $exitCode = $null
  if (-not $timedOut) {
    try {
      $proc.Refresh()
      $exitCode = [int]$proc.ExitCode
    } catch {
      $exitCode = $null
    }
  }

  $endedAt = Get-Date
  $status = if ($timedOut) { "TIMEOUT" } elseif ($exitCode -eq 0) { "PASS" } else { "FAIL" }
  $reason = if ($timedOut) {
    "Timed out after $TimeoutSec seconds"
  } elseif ($exitCode -eq 0) {
    "Completed successfully"
  } else {
    if ($null -eq $exitCode) {
      "Exited with unknown code"
    } else {
      "Exited with code $exitCode"
    }
  }

  if ($status -eq "PASS") {
    Write-Heartbeat ("STEP_PASS name={0}" -f $Name)
  } elseif ($status -eq "TIMEOUT") {
    Write-Heartbeat ("STEP_TIMEOUT name={0} timeout_sec={1}" -f $Name, $TimeoutSec)
  } else {
    Write-Heartbeat ("STEP_FAIL name={0} reason={1}" -f $Name, $reason)
  }

  return [pscustomobject]@{
    name          = $Name
    status        = $status
    reason        = $reason
    exit_code     = $exitCode
    timeout_sec   = $TimeoutSec
    started_at    = $startedAt.ToString("s")
    ended_at      = $endedAt.ToString("s")
    duration_sec  = [math]::Round(($endedAt - $startedAt).TotalSeconds, 2)
    stdout_file   = $StdOutFile
    stderr_file   = $StdErrFile
  }
}

$backendOut = Join-Path $resolvedOutputDir "06_pytest_reporting_exports_gate.txt"
$backendErr = Join-Path $resolvedOutputDir "06_pytest_reporting_exports_gate.stderr.txt"
$playwrightOut = Join-Path $resolvedOutputDir "06_playwright_sandbox_role_routes.txt"
$playwrightErr = Join-Path $resolvedOutputDir "06_playwright_sandbox_role_routes.stderr.txt"

$backendResult = $null
$playwrightResult = $null
$phase06Classification = "PASS"
$phase06FailureReason = $null

try {
  Write-Heartbeat "PHASE06_START"

  $backendResult = Invoke-TimeboxedProcess `
    -Name "backend_reporting_export_gate" `
    -FilePath "pytest" `
    -ArgumentList @("backend/tests/test_reporting_exports_gate.py", "-v") `
    -WorkingDirectory (Get-Location).Path `
    -StdOutFile $backendOut `
    -StdErrFile $backendErr `
    -TimeoutSec $backendTimeoutSec `
    -HeartbeatSec $heartbeatIntervalSec

  if ($backendResult.status -ne "PASS") {
    $phase06Classification = $backendResult.status
    $phase06FailureReason = "test_reporting_exports_gate.py $($backendResult.reason)"
    throw $phase06FailureReason
  }

  Push-Location "frontend/dashboards"
  try {
    $npmExe = Resolve-CrownExecutable "npm"
    $npxExe = Resolve-CrownExecutable "npx"

    $npx = Get-Command $npxExe -ErrorAction SilentlyContinue
    if (-not $npx) {
      $phase06Classification = "FAIL"
      $phase06FailureReason = "npx is required for sandbox route regression suite"
      throw $phase06FailureReason
    }

    & $npmExe ls @playwright/test --depth=0 *> (Join-Path $resolvedOutputDir "06_playwright_dependency_check.txt")
    if ($LASTEXITCODE -ne 0) {
      $phase06Classification = "FAIL"
      $phase06FailureReason = "Missing dependency @playwright/test"
      throw $phase06FailureReason
    }

    $playwrightResult = Invoke-TimeboxedProcess `
      -Name "sandbox_role_route_regression" `
      -FilePath $npxExe `
      -ArgumentList @("playwright", "test", "tests/e2e/sandbox-role-route-regression.spec.ts", "--reporter=line") `
      -WorkingDirectory (Get-Location).Path `
      -StdOutFile $playwrightOut `
      -StdErrFile $playwrightErr `
      -TimeoutSec $playwrightTimeoutSec `
      -HeartbeatSec $heartbeatIntervalSec

    if ($playwrightResult.status -ne "PASS") {
      $phase06Classification = $playwrightResult.status
      $phase06FailureReason = "sandbox-role-route-regression.spec.ts $($playwrightResult.reason)"
      throw $phase06FailureReason
    }
  } finally {
    Pop-Location
  }
} catch {
  if ([string]::IsNullOrWhiteSpace($phase06FailureReason)) {
    $phase06Classification = "FAIL"
    $phase06FailureReason = $_.Exception.Message
  }
  Write-Heartbeat ("PHASE06_FAIL classification={0} reason={1}" -f $phase06Classification, $phase06FailureReason)
  throw
} finally {
  $summary = [ordered]@{
    phase06_classification         = $phase06Classification
    phase06_failure_reason         = $phase06FailureReason
    backend_reporting_export_gate  = $backendResult
    sandbox_role_route_regression  = $playwrightResult
    playwright_dependency_check    = (Join-Path $resolvedOutputDir "06_playwright_dependency_check.txt")
    phase06_heartbeat_file         = $heartbeatFile
  }
  $summary | ConvertTo-Json -Depth 8 | Out-File (Join-Path $resolvedOutputDir "06_phase2_summary.json") -Encoding utf8
  Write-Heartbeat ("PHASE06_END classification={0}" -f $phase06Classification)
}
