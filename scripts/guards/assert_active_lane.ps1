param(
  [Parameter(Mandatory = $true)]
  [string]$Lane
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $Lane)) {
  throw "Lane packet not found: $Lane"
}

$packet = Get-Content -LiteralPath $Lane -Raw | ConvertFrom-Json
$currentRoot = (git rev-parse --show-toplevel).Trim()
$currentBranch = (git rev-parse --abbrev-ref HEAD).Trim()
$currentHead = (git rev-parse HEAD).Trim()
$expectedRoot = (Resolve-Path -LiteralPath ([string]$packet.worktree)).Path.TrimEnd('\')
$currentRoot = (Resolve-Path -LiteralPath $currentRoot).Path.TrimEnd('\')

if ($currentRoot -ne $expectedRoot) {
  throw "Wrong worktree. Current=$currentRoot Expected=$expectedRoot"
}

if ($currentBranch -ne [string]$packet.branch) {
  throw "Wrong branch. Current=$currentBranch Expected=$($packet.branch)"
}

if ($currentHead -ne [string]$packet.head_sha) {
  throw "Wrong HEAD. Current=$currentHead Expected=$($packet.head_sha)"
}

$status = (git status --short | Out-String).Trim()
if ($status) {
  throw "Worktree is dirty before validation. $status"
}

Write-Host "ACTIVE_LANE_GUARD_PASS"
Write-Host "BRANCH=$currentBranch"
Write-Host "HEAD=$currentHead"
Write-Host "WORKTREE=$currentRoot"
Write-Host "GOAL=$($packet.goal)"
Write-Host "COMPLETION_CLAIM_ALLOWED=$($packet.completion_claim_allowed)"
Write-Host "INDEPENDENT_REVIEW_REQUIRED=$($packet.independent_review_required)"
