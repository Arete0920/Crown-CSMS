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

Write-Host "Step 1: Boot + seed + smoke" -ForegroundColor Yellow
& $lockdownRun -APITimeout $APITimeout

Write-Host "Step 2: Golden Path gate" -ForegroundColor Yellow
if ($SkipSnapshot) {
  & $goldenGate -APITimeout $APITimeout -BackendOnly
} else {
  & $goldenGate -APITimeout $APITimeout
}

if (-not $SkipSnapshot) {
  Write-Host "Step 3: Snapshot" -ForegroundColor Yellow
  & $snapshot
}

if (-not $SkipTag) {
  Write-Host "Step 4: Tag green proof" -ForegroundColor Yellow
  & $tagGreen
}

Write-Host "✅ ONE-CLICK GATE COMPLETE" -ForegroundColor Green
