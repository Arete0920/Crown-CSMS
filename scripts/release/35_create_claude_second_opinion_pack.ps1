[CmdletBinding()]
param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")),
    [string]$OutputDir,
    [switch]$NoZip
)

$ErrorActionPreference = "Stop"

if (-not $OutputDir) {
    $OutputDir = Join-Path $RepoRoot "audit-artifacts\prod-run-270-orderfix-verification\claude-second-opinion"
}

$sourceFiles = @(
    "audit-artifacts\prod-run-270-orderfix-verification\10_authoritative_capture_20260508_0023Z.txt",
    "audit-artifacts\prod-run-270-orderfix-verification\99_VERIFICATION_REPORT.md",
    "audit-artifacts\prod-run-270-orderfix-verification\99_verification_result.json",
    "audit-artifacts\runtime-release-closure\20260418_070051\RELEASE_AUTHORITY_95_PROOF_SNAPSHOT_20260506.md"
)

Write-Host "[1/5] Validating source evidence files..." -ForegroundColor Cyan
$missing = @()
foreach ($relative in $sourceFiles) {
    $full = Join-Path $RepoRoot $relative
    if (-not (Test-Path $full)) {
        $missing += $relative
    }
}

if ($missing.Count -gt 0) {
    Write-Error ("Missing required file(s):`n - " + ($missing -join "`n - "))
}

Write-Host "[2/5] Creating output folder..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

Write-Host "[3/5] Copying evidence files..." -ForegroundColor Cyan
foreach ($relative in $sourceFiles) {
    $src = Join-Path $RepoRoot $relative
    $dst = Join-Path $OutputDir ([IO.Path]::GetFileName($relative))
    Copy-Item -Path $src -Destination $dst -Force
}

$mainPrompt = @"
You are an independent release auditor.

Rules:
- Evidence-first only.
- No speculation.
- No unstated assumptions.
- Do not use external links or internet data unless explicitly provided in these uploaded files.

Task:
Verify whether the production deploy/runtime gate is closed for run 270 (ID 25528614282), while keeping pilot/compliance/GA decisions separate.

Required outputs:
1) Final verdict for production deploy/runtime gate only: PASS or FAIL.
2) Control-check table with status and exact evidence quotes.
3) Contradictions or weak points in current documentation.
4) Residual risks and missing evidence for pilot approval and GA approval.
5) Confidence score (0-100) with justification.
6) One-paragraph executive statement for leadership.

Hard requirement:
If a claim cannot be proven from uploaded artifacts, mark it UNPROVEN.
"@

$redTeamPrompt = @"
Now run a red-team review.

Assume the closure conclusion is wrong and try to disprove it using only uploaded artifacts.

Output requirements:
1) List every plausible failure mode.
2) For each failure mode, state whether evidence refutes it, supports it, or is insufficient.
3) Mark any unrefuted blocker clearly.
4) Final red-team verdict: BLOCKER_FOUND or NO_UNREFUTED_BLOCKER.

Rules:
- Evidence-only.
- No assumptions.
- If not proven, mark UNPROVEN.
"@

$checklist = @"
# Claude Second Opinion Runbook

## Goal
Obtain an independent, evidence-only second opinion for production deploy/runtime gate closure.

## Upload These Files To Claude
- 10_authoritative_capture_20260508_0023Z.txt
- 99_VERIFICATION_REPORT.md
- 99_verification_result.json
- RELEASE_AUTHORITY_95_PROOF_SNAPSHOT_20260506.md

## Step 1: Primary Review
1. Start a new Claude chat/project.
2. Upload the 4 files above.
3. Paste the contents of CLAUDE_PROMPT_MAIN.txt.
4. Save Claude response as CLAUDE_RESPONSE_MAIN.md.

## Step 2: Adversarial Review
1. In same chat (with same files), paste CLAUDE_PROMPT_RED_TEAM.txt.
2. Save Claude response as CLAUDE_RESPONSE_RED_TEAM.md.

## Acceptance Criteria
- Primary verdict is PASS for production deploy/runtime gate.
- Red-team verdict is NO_UNREFUTED_BLOCKER.
- Any UNPROVEN claims are tracked for follow-up.

## Scope Boundary
This validates technical gate closure only. It does not automatically close compliance, acceptance, pilot authorization, or GA authority.
"@

Write-Host "[4/5] Writing prompts and runbook..." -ForegroundColor Cyan
Set-Content -Path (Join-Path $OutputDir "CLAUDE_PROMPT_MAIN.txt") -Value $mainPrompt -Encoding UTF8
Set-Content -Path (Join-Path $OutputDir "CLAUDE_PROMPT_RED_TEAM.txt") -Value $redTeamPrompt -Encoding UTF8
Set-Content -Path (Join-Path $OutputDir "CLAUDE_SECOND_OPINION_RUNBOOK.md") -Value $checklist -Encoding UTF8

$zipPath = Join-Path (Split-Path $OutputDir -Parent) "claude-second-opinion.zip"
if (-not $NoZip) {
    Write-Host "[5/5] Building zip package..." -ForegroundColor Cyan
    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }
    Compress-Archive -Path (Join-Path $OutputDir "*") -DestinationPath $zipPath -CompressionLevel Optimal
}
else {
    Write-Host "[5/5] Zip build skipped (-NoZip)." -ForegroundColor Yellow
}

Write-Host "Done." -ForegroundColor Green
Write-Host "Output folder: $OutputDir"
if (-not $NoZip) {
    Write-Host "Zip package:   $zipPath"
}
Write-Host "Next: Upload files in output folder to Claude and run prompts in order." -ForegroundColor Green
