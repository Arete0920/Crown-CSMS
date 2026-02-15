param(
  [int]$TimeoutSec = 5
)

$ErrorActionPreference = "Stop"

$DemoRoot = Join-Path $env:USERPROFILE "OneDrive\Desktop\Crown2026_DEMO_TAG"
$MainRoot = Join-Path $env:USERPROFILE "OneDrive\Desktop\Crown2026"

$failures = New-Object System.Collections.Generic.List[string]

function Get-PortOwnerInfo {
  param([int]$Port)

  $listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue |
    Select-Object -First 1

  if (-not $listener) {
    return [PSCustomObject]@{
      Port        = $Port
      LocalAddress= ""
      Pid         = ""
      CommandLine = ""
    }
  }

  $owningPid = $listener.OwningProcess
  $cmd = ""
  try {
    $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId = $owningPid" -ErrorAction Stop).CommandLine
  }
  catch {
    $cmd = "<unavailable>"
  }

  return [PSCustomObject]@{
    Port         = $Port
    LocalAddress = $listener.LocalAddress
      Pid          = $owningPid
    CommandLine  = $cmd
  }
}

Write-Host "== Crown Demo Snapshot =="

try {
  if (-not (Test-Path $DemoRoot)) { throw "Demo root not found: $DemoRoot" }
  if (-not (Test-Path $MainRoot)) { throw "Main root not found: $MainRoot" }

  $demoSha = (git -C $DemoRoot rev-parse HEAD).Trim()
  $mainSha = (git -C $MainRoot rev-parse HEAD).Trim()

  if (-not $demoSha) { $failures.Add("Missing DEMO_TAG git SHA") }
  if (-not $mainSha) { $failures.Add("Missing main git SHA") }

  $healthRaw = ""
  $health = $null
  try {
    $healthRaw = (Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8000/health/" -TimeoutSec $TimeoutSec).Content
    $health = $healthRaw | ConvertFrom-Json
  }
  catch {
    $failures.Add("Failed to fetch backend /health/: $($_.Exception.Message)")
  }

  $frontendStatus = ""
  try {
    $frontendStatus = (Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:3000/" -TimeoutSec $TimeoutSec).StatusCode
    if ([int]$frontendStatus -ne 200) {
      $failures.Add("Frontend status is $frontendStatus (expected 200)")
    }
  }
  catch {
    $failures.Add("Failed to reach frontend /: $($_.Exception.Message)")
  }

  $owner8000 = Get-PortOwnerInfo -Port 8000
  $owner3000 = Get-PortOwnerInfo -Port 3000

  if (-not $owner8000.Pid) { $failures.Add("No listener on port 8000") }
  if (-not $owner3000.Pid) { $failures.Add("No listener on port 3000") }

  $runservers = Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -match 'manage\.py\s+runserver' } |
    Select-Object ProcessId, CommandLine

  Write-Host "DEMO_TAG_SHA=$demoSha"
  Write-Host "MAIN_SHA=$mainSha"
  Write-Host "BACKEND_HEALTH_JSON=$healthRaw"
  Write-Host "FRONTEND_STATUS=$frontendStatus"

  Write-Host "PORT_8000_OWNER_PID=$($owner8000.Pid)"
  Write-Host "PORT_8000_OWNER_ADDR=$($owner8000.LocalAddress)"
  Write-Host "PORT_8000_OWNER_CMD=$($owner8000.CommandLine)"

  Write-Host "PORT_3000_OWNER_PID=$($owner3000.Pid)"
  Write-Host "PORT_3000_OWNER_ADDR=$($owner3000.LocalAddress)"
  Write-Host "PORT_3000_OWNER_CMD=$($owner3000.CommandLine)"

  if ($runservers.Count -eq 0) {
    Write-Host "RUNSERVER_PIDS=<none>"
  }
  else {
    $pids = ($runservers | ForEach-Object { $_.ProcessId }) -join ","
    Write-Host "RUNSERVER_PIDS=$pids"
    foreach ($r in $runservers) {
      Write-Host "RUNSERVER_CMD_$($r.ProcessId)=$($r.CommandLine)"
    }
  }

  if ($failures.Count -gt 0) {
    Write-Host "RED: snapshot detected failures."
    foreach ($f in $failures) { Write-Host "FAIL=$f" }
    exit 1
  }

  Write-Host "GREEN: snapshot complete."
  exit 0
}
catch {
  Write-Host "RED: snapshot failed."
  Write-Host $_
  exit 1
}
