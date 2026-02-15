param(
  [int]$TimeoutSec = 5
)

$ErrorActionPreference = "Stop"

$DemoRoot  = Join-Path $env:USERPROFILE "OneDrive\Desktop\Crown2026_DEMO_TAG"
$BootProof = Join-Path $DemoRoot "tools\dev_scripts\demo_boot_then_proof.ps1"
$Snapshot  = Join-Path $DemoRoot "tools\dev_scripts\demo_snapshot.ps1"

Write-Host "== CROWN ONE-CLICK GATE =="

if (-not (Test-Path $BootProof)) { throw "Missing demo_boot_then_proof.ps1" }
if (-not (Test-Path $Snapshot))  { throw "Missing demo_snapshot.ps1" }

# Run Boot + Proof
powershell -ExecutionPolicy Bypass -File $BootProof -TimeoutSec $TimeoutSec
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
  $demoSha = (git -C $DemoRoot rev-parse HEAD).Trim()
  $buildSha = ((Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8000/health/" -TimeoutSec $TimeoutSec).Content | ConvertFrom-Json).build_sha
  Write-Host "GREEN_PROOF DEMO_TAG_SHA=$demoSha BUILD_SHA=$buildSha"
    Write-Host "FINAL_STATUS=GREEN"
    exit 0
}

Write-Host ""
Write-Host "Boot + Proof failed. Running Snapshot diagnostics..."
Write-Host ""

powershell -ExecutionPolicy Bypass -File $Snapshot
Write-Host "FINAL_STATUS=RED"
exit 1
