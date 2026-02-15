param(
  [Alias("APITimeout")][int]$TimeoutSec = 20,
  [int]$AdmissionsCount = 10,
  [string]$TagName = ""
)

$ErrorActionPreference = "Stop"

$mainRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\.."))
$backendRoot = Join-Path $mainRoot "backend"
$scriptsRoot = Join-Path $mainRoot "tools\dev_scripts"
$py = Join-Path $mainRoot ".venv\Scripts\python.exe"

$tagger = Join-Path $scriptsRoot "tag_green3.ps1"

if (-not (Test-Path $py)) { throw "Python not found: $py" }
if (-not (Test-Path $backendRoot)) { throw "Backend path not found: $backendRoot" }

$env:ENVIRONMENT = "dev"
if ([string]::IsNullOrWhiteSpace($env:DEV_OPS_SECRET)) {
  $env:DEV_OPS_SECRET = [Environment]::GetEnvironmentVariable("DEV_OPS_SECRET", "User")
}
if ([string]::IsNullOrWhiteSpace($env:CROWN_OPS_SECRET)) {
  $env:CROWN_OPS_SECRET = [Environment]::GetEnvironmentVariable("CROWN_OPS_SECRET", "User")
}

if ([string]::IsNullOrWhiteSpace($env:DEV_OPS_SECRET)) {
  throw "DEV_OPS_SECRET missing in shell/User env"
}

Write-Host "== LOCKDOWN RUN =="

Push-Location $backendRoot
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

# Boot Django server in background
Write-Host "Booting Django server..."
$serverJob = Start-Job -ScriptBlock {
  param($pyPath, $backendPath)
  Set-Location $backendPath
  & $pyPath manage.py runserver 127.0.0.1:8000 --noreload
} -ArgumentList $py, $backendRoot

# Wait for server to be ready
Write-Host "Waiting for server..."
$maxAttempts = 20
$attempt = 0
$serverReady = $false
while ($attempt -lt $maxAttempts -and -not $serverReady) {
  Start-Sleep -Milliseconds 500
  try {
    $healthStatus = (Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 "http://127.0.0.1:8000/health/").StatusCode
    if ($healthStatus -eq 200) {
      $serverReady = $true
      Write-Host "Server ready!"
    }
  }
  catch {
    $attempt++
  }
}

if (-not $serverReady) {
  Stop-Job -Job $serverJob
  Remove-Job -Job $serverJob
  throw "Django server failed to start within timeout"
}

Write-Host "Seeding Heritage realism pack..."
& $py manage.py seed_heritage_realism_pack --no-finance-scripts
if ($LASTEXITCODE -ne 0) { throw "seed_heritage_realism_pack failed exit=$LASTEXITCODE" }

try {
  $healthStatus = (Invoke-WebRequest -UseBasicParsing -TimeoutSec $TimeoutSec "http://127.0.0.1:8000/health/").StatusCode
  if ($healthStatus -ne 200) { throw "backend health status=$healthStatus" }
}
catch {
  throw "backend health check failed: $($_.Exception.Message)"
}
Pop-Location

if (-not [string]::IsNullOrWhiteSpace($TagName)) {
  if (-not (Test-Path $tagger)) { throw "Missing script: $tagger" }
  powershell -ExecutionPolicy Bypass -File $tagger -TagName $TagName
  if ($LASTEXITCODE -ne 0) { throw "tag_green3 failed exit=$LASTEXITCODE" }
}

Write-Host "LOCKDOWN_RUN=GREEN"
exit 0
