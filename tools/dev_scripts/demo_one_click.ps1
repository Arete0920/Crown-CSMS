[CmdletBinding()]
param(
  [int]$APITimeout = 20,
  [switch]$SkipSnapshot,
  [switch]$SkipTag
)

$ErrorActionPreference = "Stop"
$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "== CROWN ONE-CLICK GATE ==" -ForegroundColor Cyan

function Require-File([string]$path) {
  if (-not (Test-Path $path)) { throw "Missing required script: $path" }
}

$lockdownRun = Join-Path $PSScriptRoot "lockdown_run.ps1"
$goldenGate  = Join-Path $PSScriptRoot "golden_path_gate.ps1"
$snapshot    = Join-Path $PSScriptRoot "demo_snapshot.ps1"
$tagGreen    = Join-Path $PSScriptRoot "tag_green3.ps1"

Require-File $lockdownRun
Require-File $goldenGate
if (-not $SkipSnapshot) { Require-File $snapshot }
if (-not $SkipTag)      { Require-File $tagGreen }

Write-Host "Step 1: Boot + seed + basic smoke (lockdown_run.ps1)" -ForegroundColor Yellow
& $lockdownRun -APITimeout $APITimeout

Write-Host "Step 2: Golden Path gate (golden_path_gate.ps1)" -ForegroundColor Yellow
& $goldenGate -TimeoutSec $APITimeout

if (-not $SkipSnapshot) {
  Write-Host "Step 3: Snapshot demo state (demo_snapshot.ps1)" -ForegroundColor Yellow
  & $snapshot
}

if (-not $SkipTag) {
  Write-Host "Step 4: Tag green proof (tag_green3.ps1)" -ForegroundColor Yellow
  $tagName = "lockdown-goldenpath-" + (Get-Date -Format "yyyyMMdd-HHmmss")
  & $tagGreen -TagName $tagName
}

Write-Host "✅ ONE-CLICK GATE COMPLETE" -ForegroundColor Green
