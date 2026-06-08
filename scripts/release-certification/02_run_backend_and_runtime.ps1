param(
  [string]$OutputDir,
  [string]$BaseUrl = "http://127.0.0.1:8000",
  [string]$SwaggerPath = "/api/docs/",
  [string]$HealthPath = "/health/",
  [string]$IntegrityPath = "/api/integrity/"
)

$ErrorActionPreference = "Stop"

$supplementalTimeoutSec = 420
if (-not [string]::IsNullOrWhiteSpace($env:CROWN_SUPPLEMENTAL_STEP_TIMEOUT_SEC)) {
  [int]$parsedTimeout = 0
  if ([int]::TryParse($env:CROWN_SUPPLEMENTAL_STEP_TIMEOUT_SEC, [ref]$parsedTimeout) -and $parsedTimeout -gt 0) {
    $supplementalTimeoutSec = $parsedTimeout
  }
}

$heartbeatIntervalSec = 15
if (-not [string]::IsNullOrWhiteSpace($env:CROWN_SUPPLEMENTAL_HEARTBEAT_SEC)) {
  [int]$parsedHeartbeat = 0
  if ([int]::TryParse($env:CROWN_SUPPLEMENTAL_HEARTBEAT_SEC, [ref]$parsedHeartbeat) -and $parsedHeartbeat -gt 0) {
    $heartbeatIntervalSec = $parsedHeartbeat
  }
}

$heartbeatFile = Join-Path $OutputDir "02_supplemental_heartbeat.log"

$nativePreferenceVar = Get-Variable -Name PSNativeCommandUseErrorActionPreference -Scope Global -ErrorAction SilentlyContinue
$hadNativePreference = ($null -ne $nativePreferenceVar)
$oldNativePreference = if ($hadNativePreference) { [bool]$nativePreferenceVar.Value } else { $false }
if ($hadNativePreference) {
  $global:PSNativeCommandUseErrorActionPreference = $false
}

function Save-InvokeWeb {
  param(
    [string]$Url,
    [string]$OutFile
  )
  try {
    $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 20
    [pscustomobject]@{
      url    = $Url
      status = "PASS"
      code   = [int]$resp.StatusCode
      body   = $resp.Content
    } | ConvertTo-Json -Depth 5 | Out-File $OutFile -Encoding utf8
    return $true
  } catch {
    [pscustomobject]@{
      url    = $Url
      status = "FAIL"
      error  = $_.Exception.Message
    } | ConvertTo-Json -Depth 5 | Out-File $OutFile -Encoding utf8
    return $false
  }
}

function Write-Heartbeat {
  param(
    [string]$Message
  )
  $ts = (Get-Date).ToString("s")
  Add-Content -Path $heartbeatFile -Value ("[{0}] {1}" -f $ts, $Message) -Encoding utf8
}

function Invoke-SupplementalStep {
  param(
    [string]$Name,
    [string]$ScriptPath,
    [int]$TimeoutSec
  )

  $stdoutStderrFile = Join-Path $OutputDir ("02_{0}_stdout_stderr.txt" -f $Name)
  $statusFile = Join-Path $OutputDir ("02_{0}_status.json" -f $Name)
  $startedAt = Get-Date

  Write-Heartbeat ("STEP_START name={0} script={1} timeout_sec={2}" -f $Name, $ScriptPath, $TimeoutSec)

  $result = [ordered]@{
    name               = $Name
    script             = $ScriptPath
    status             = "RUNNING"
    timeout_sec        = $TimeoutSec
    started_at         = $startedAt.ToString("s")
    ended_at           = $null
    duration_sec       = $null
    reason             = $null
    stdout_stderr_file = $stdoutStderrFile
    status_file        = $statusFile
  }

  $result | ConvertTo-Json -Depth 6 | Out-File $statusFile -Encoding utf8

  $job = Start-Job -ScriptBlock {
    param($scriptToRun)
    & powershell -NoProfile -ExecutionPolicy Bypass -File $scriptToRun 2>&1
    $scriptExitCode = if ($null -ne $LASTEXITCODE) { [int]$LASTEXITCODE } else { 0 }
    Write-Output ("__EXITCODE__={0}" -f $scriptExitCode)
    exit $scriptExitCode
  } -ArgumentList $ScriptPath

  $deadline = (Get-Date).AddSeconds($TimeoutSec)
  $timedOut = $false
  while ($true) {
    $completed = Wait-Job -Job $job -Timeout $heartbeatIntervalSec
    if ($completed) {
      break
    }

    $now = Get-Date
    if ($now -ge $deadline) {
      $timedOut = $true
      break
    }

    $elapsedSec = [math]::Round(($now - $startedAt).TotalSeconds, 1)
    Write-Heartbeat ("STEP_RUNNING name={0} elapsed_sec={1}" -f $Name, $elapsedSec)
  }

  $rawOutput = @(Receive-Job -Job $job -Keep -ErrorAction SilentlyContinue)
  $exitMarker = ($rawOutput | Where-Object { $_ -is [string] -and $_ -like "__EXITCODE__=*" } | Select-Object -Last 1)
  $jobExitCode = $null
  if (-not [string]::IsNullOrWhiteSpace($exitMarker)) {
    [int]$parsedExitCode = 0
    if ([int]::TryParse(($exitMarker -replace "^__EXITCODE__=", ""), [ref]$parsedExitCode)) {
      $jobExitCode = $parsedExitCode
    }
  }

  $outputLines = @($rawOutput | Where-Object { -not ($_ -is [string] -and $_ -like "__EXITCODE__=*") })
  $outputText = (($outputLines | Out-String).Trim())
  if ([string]::IsNullOrWhiteSpace($outputText)) {
    $outputText = "(no output captured)"
  }
  $outputText | Out-File $stdoutStderrFile -Encoding utf8

  if ($timedOut) {
    Stop-Job -Job $job -ErrorAction SilentlyContinue
    Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    $result.status = "TIMEOUT"
    $result.reason = ("Timed out after {0} seconds" -f $TimeoutSec)
    Write-Heartbeat ("STEP_TIMEOUT name={0} timeout_sec={1}" -f $Name, $TimeoutSec)
  } else {
    Remove-Job -Job $job -Force -ErrorAction SilentlyContinue

    if ($null -eq $jobExitCode) {
      $result.status = "FAIL"
      $result.reason = "Supplemental job completed without a parseable exit code"
      Write-Heartbeat ("STEP_FAIL name={0} reason=missing_exit_code" -f $Name)
    } elseif ($jobExitCode -eq 0) {
      $result.status = "PASS"
      $result.reason = "Completed successfully"
      Write-Heartbeat ("STEP_PASS name={0}" -f $Name)
    } else {
      $result.status = "FAIL"
      $result.reason = ("Exited with code {0}" -f $jobExitCode)
      Write-Heartbeat ("STEP_FAIL name={0} exit_code={1}" -f $Name, $jobExitCode)
    }
  }

  $endedAt = Get-Date
  $result.ended_at = $endedAt.ToString("s")
  $result.duration_sec = [math]::Round(($endedAt - $startedAt).TotalSeconds, 2)

  $result | ConvertTo-Json -Depth 6 | Out-File $statusFile -Encoding utf8
  return [pscustomobject]$result
}

$healthOk = $false
$integrityOk = $false
$swaggerOk = $false
$deployCheck = Join-Path $OutputDir "02_django_check_deploy.txt"
$migrations = Join-Path $OutputDir "02_django_showmigrations.txt"
$supplementalSteps = New-Object System.Collections.Generic.List[object]
$step02Classification = "PASS"
$step02FailureReason = $null

try {
  Write-Heartbeat "STEP02_START backend/runtime checks started"

  $healthOk = Save-InvokeWeb -Url ($BaseUrl + $HealthPath) -OutFile (Join-Path $OutputDir "02_health.json")
  $integrityOk = Save-InvokeWeb -Url ($BaseUrl + $IntegrityPath) -OutFile (Join-Path $OutputDir "02_integrity.json")
  $swaggerOk = Save-InvokeWeb -Url ($BaseUrl + $SwaggerPath) -OutFile (Join-Path $OutputDir "02_swagger.json")

  $oldErrorActionPreference = $ErrorActionPreference
  $ErrorActionPreference = "Continue"

  & python backend/manage.py check --deploy 2>&1 | Out-File $deployCheck -Encoding utf8
  if ($LASTEXITCODE -ne 0) {
    throw "manage.py check --deploy failed"
  }

  & python backend/manage.py showmigrations 2>&1 | Out-File $migrations -Encoding utf8
  if ($LASTEXITCODE -ne 0) {
    throw "manage.py showmigrations failed"
  }

  $ErrorActionPreference = $oldErrorActionPreference

  $supplementalScriptSpecs = @(
    @{ name = "supplemental_phase4"; script = "scripts/release/phase4_backend_verification_and_django_proof.ps1" },
    @{ name = "supplemental_phase5"; script = "scripts/release/phase5_module_proof_matrix.ps1" },
    @{ name = "supplemental_phase8"; script = "scripts/release/phase8_frontend_and_dashboard_proof.ps1" }
  )

  foreach ($spec in $supplementalScriptSpecs) {
    if (-not (Test-Path $spec.script)) {
      $missingResult = [pscustomobject]@{
        name               = $spec.name
        script             = $spec.script
        status             = "SKIP"
        timeout_sec        = $supplementalTimeoutSec
        started_at         = (Get-Date).ToString("s")
        ended_at           = (Get-Date).ToString("s")
        duration_sec       = 0
        reason             = "Script not found"
        stdout_stderr_file = $null
        status_file        = $null
      }
      Write-Heartbeat ("STEP_SKIP name={0} reason=Script not found" -f $spec.name)
      $supplementalSteps.Add($missingResult) | Out-Null
      continue
    }

    $stepResult = Invoke-SupplementalStep -Name $spec.name -ScriptPath $spec.script -TimeoutSec $supplementalTimeoutSec
    $supplementalSteps.Add($stepResult) | Out-Null

    if ($stepResult.status -ne "PASS") {
      $step02Classification = $stepResult.status
      $step02FailureReason = ("Supplemental script {0} {1}" -f $spec.script, $stepResult.reason)
      throw $step02FailureReason
    }
  }

  if (-not ($healthOk -and $integrityOk -and $swaggerOk)) {
    $step02Classification = "FAIL"
    $step02FailureReason = "One or more runtime endpoints failed"
    throw "One or more runtime endpoints failed."
  }
} catch {
  if ([string]::IsNullOrWhiteSpace($step02FailureReason)) {
    $step02FailureReason = $_.Exception.Message
  }
  if ($step02Classification -eq "PASS") {
    $step02Classification = "FAIL"
  }
  Write-Heartbeat ("STEP02_FAIL classification={0} reason={1}" -f $step02Classification, $step02FailureReason)
  throw
} finally {
  $summary = [ordered]@{
    health_ok                    = $healthOk
    integrity_ok                 = $integrityOk
    swagger_ok                   = $swaggerOk
    deploy_check                 = $deployCheck
    migrations                   = $migrations
    supplemental_timeout_sec     = $supplementalTimeoutSec
    supplemental_heartbeat_file  = $heartbeatFile
    supplemental_steps           = @($supplementalSteps.ToArray())
    step02_classification        = $step02Classification
    step02_failure_reason        = $step02FailureReason
  }
  $summary | ConvertTo-Json -Depth 8 | Out-File (Join-Path $OutputDir "02_backend_runtime_summary.json") -Encoding utf8

  Write-Heartbeat ("STEP02_END classification={0}" -f $step02Classification)
  $ErrorActionPreference = "Stop"
  if ($hadNativePreference) {
    $global:PSNativeCommandUseErrorActionPreference = $oldNativePreference
  }
}
