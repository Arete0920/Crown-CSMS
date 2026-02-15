param(
  [int]$AdmissionsCount = 10,
  [string]$TagName = ""
)

$ErrorActionPreference = "Stop"

$demoRoot = Join-Path $env:USERPROFILE "OneDrive\Desktop\Crown2026_DEMO_TAG"
$backendRoot = Join-Path $demoRoot "backend"
$scriptsRoot = Join-Path $demoRoot "tools\dev_scripts"
$py = Join-Path $env:USERPROFILE "OneDrive\Desktop\Crown2026\.venv\Scripts\python.exe"

$oneClick = Join-Path $scriptsRoot "demo_one_click.ps1"
$gate = Join-Path $scriptsRoot "golden_path_gate.ps1"
$tagger = Join-Path $scriptsRoot "tag_green3.ps1"

if (-not (Test-Path $py)) { throw "Python not found: $py" }
if (-not (Test-Path $backendRoot)) { throw "Backend path not found: $backendRoot" }
if (-not (Test-Path $oneClick)) { throw "Missing script: $oneClick" }
if (-not (Test-Path $gate)) { throw "Missing script: $gate" }

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
& $py manage.py seed_lockdown_minimal --count $AdmissionsCount
if ($LASTEXITCODE -ne 0) { throw "seed_lockdown_minimal failed exit=$LASTEXITCODE" }
Pop-Location

powershell -ExecutionPolicy Bypass -File $oneClick
if ($LASTEXITCODE -ne 0) { throw "demo_one_click failed exit=$LASTEXITCODE" }

powershell -ExecutionPolicy Bypass -File $gate
if ($LASTEXITCODE -ne 0) { throw "golden_path_gate failed exit=$LASTEXITCODE" }

1..3 | ForEach-Object {
  Write-Host "--- GATE RUN $_ ---"
  powershell -ExecutionPolicy Bypass -File $gate
  if ($LASTEXITCODE -ne 0) { throw "GREEN_3X_FAILED run=$_ exit=$LASTEXITCODE" }
}

Write-Host "GREEN_3X=YES"

if (-not [string]::IsNullOrWhiteSpace($TagName)) {
  if (-not (Test-Path $tagger)) { throw "Missing script: $tagger" }
  powershell -ExecutionPolicy Bypass -File $tagger -TagName $TagName
  if ($LASTEXITCODE -ne 0) { throw "tag_green3 failed exit=$LASTEXITCODE" }
}

Write-Host "LOCKDOWN_RUN=GREEN"
exit 0
