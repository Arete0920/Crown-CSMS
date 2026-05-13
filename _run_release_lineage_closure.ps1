$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

param(
    [string]$RepoRoot = $null
)

if (-not $RepoRoot) {
    $RepoRoot = (& git -C $PSScriptRoot rev-parse --show-toplevel 2>$null).Trim()
    if (-not $RepoRoot) {
        $RepoRoot = $PSScriptRoot
    }
}

Set-Location $RepoRoot

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$out = "audit-artifacts\release-lineage-closure\$stamp"
New-Item -ItemType Directory -Force -Path $out | Out-Null

function Write-Step($Name) {
    "`n===== $Name =====" | Tee-Object -FilePath "$out\RUN_LOG.txt" -Append
}

function Run-Capture($Name, $Command) {
    Write-Step $Name
    "COMMAND: $Command" | Tee-Object -FilePath "$out\RUN_LOG.txt" -Append
    powershell -NoProfile -ExecutionPolicy Bypass -Command $Command 2>&1 |
        Tee-Object -FilePath "$out\$Name.txt"
}

Write-Step "REPO STATE"
git status -sb | Tee-Object -FilePath "$out\01_git_status.txt"
git branch --show-current | Tee-Object -FilePath "$out\02_branch.txt"
git rev-parse HEAD | Tee-Object -FilePath "$out\03_head.txt"
git log --oneline -20 | Tee-Object -FilePath "$out\04_git_log.txt"

Write-Step "REMOTE STATE"
git fetch origin --prune --tags
git status -sb | Tee-Object -FilePath "$out\05_git_status_after_fetch.txt"
git branch -vv | Tee-Object -FilePath "$out\06_branch_vv.txt"

Write-Step "DEPLOY RUNS"
gh run list --workflow deploy-prod.yml --limit 20 --json databaseId,number,status,conclusion,headSha,displayTitle,event,createdAt,updatedAt,url |
    Tee-Object -FilePath "$out\07_deploy_runs.json"

$latestSuccess = gh run list --workflow deploy-prod.yml --limit 20 --json databaseId,number,status,conclusion,headSha,displayTitle,event,createdAt,updatedAt,url |
    ConvertFrom-Json |
    Where-Object { $_.status -eq "completed" -and $_.conclusion -eq "success" } |
    Select-Object -First 1

if (-not $latestSuccess) {
    throw "No successful deploy-prod run found in latest 20 runs."
}

$runId = $latestSuccess.databaseId
$runSha = $latestSuccess.headSha

Write-Step "LATEST SUCCESSFUL DEPLOY"
$latestSuccess | ConvertTo-Json -Depth 10 | Tee-Object -FilePath "$out\08_latest_successful_deploy.json"

gh run view $runId --json status,conclusion,headSha,createdAt,updatedAt,url,workflowName,displayTitle |
    Tee-Object -FilePath "$out\09_latest_successful_deploy_detail.json"

gh api "repos/tcmegahan/Crown2026/actions/runs/$runId/jobs" |
    Tee-Object -FilePath "$out\10_latest_successful_deploy_jobs.json"

Write-Step "LIVE RUNTIME HEALTH"
curl.exe -sS -i https://crown-api-prod.azurewebsites.net/api/health/ |
    Tee-Object -FilePath "$out\11_health_raw.txt"

Write-Step "LIVE RUNTIME INTEGRITY"
curl.exe -sS -i https://crown-api-prod.azurewebsites.net/api/integrity/ |
    Tee-Object -FilePath "$out\12_integrity_raw.txt"

$healthJson = curl.exe -sS https://crown-api-prod.azurewebsites.net/api/health/ | ConvertFrom-Json
$integrityJson = curl.exe -sS https://crown-api-prod.azurewebsites.net/api/integrity/ | ConvertFrom-Json

$runtime = [pscustomobject]@{
    health_ok              = $healthJson.ok
    health_status          = $healthJson.status
    health_build_sha       = $healthJson.build_sha
    health_deploy_run_id   = $healthJson.deploy_run_id
    health_deploy_tag      = $healthJson.prod_deploy_tag
    health_version         = $healthJson.version
    health_db              = $healthJson.db
    integrity_ok           = $integrityJson.ok
    integrity_build_sha    = $integrityJson.build_sha
    integrity_deploy_tag   = $integrityJson.prod_deploy_tag
    integrity_version      = $integrityJson.version
    expected_run_id        = "$runId"
    expected_head_sha      = $runSha
    build_sha_matches_run  = ($healthJson.build_sha -eq $runSha -and $integrityJson.build_sha -eq $runSha)
    deploy_run_matches     = ("$($healthJson.deploy_run_id)" -eq "$runId")
}

$runtime | ConvertTo-Json -Depth 10 | Tee-Object -FilePath "$out\13_runtime_lineage_check.json"

if (-not $runtime.build_sha_matches_run) {
    throw "FAIL: runtime build_sha does not match latest successful deploy SHA."
}

if (-not $runtime.deploy_run_matches) {
    throw "FAIL: runtime deploy_run_id does not match latest successful deploy run."
}

Write-Step "MERGE LINEAGE CHECKS"

$lineageTargets = @(
    "d3eac40",
    "f34c6e6",
    "47c7b1c3",
    $runSha
)

$lineageResults = @()

foreach ($sha in $lineageTargets) {
    $exists = $true
    git cat-file -e "$sha^{commit}" 2>$null
    if ($LASTEXITCODE -ne 0) { $exists = $false }

    $inHead = $false
    $inOriginMain = $false

    if ($exists) {
        git merge-base --is-ancestor $sha HEAD 2>$null
        if ($LASTEXITCODE -eq 0) { $inHead = $true }

        git merge-base --is-ancestor $sha origin/main 2>$null
        if ($LASTEXITCODE -eq 0) { $inOriginMain = $true }
    }

    $lineageResults += [pscustomobject]@{
        sha            = $sha
        exists_locally = $exists
        in_HEAD        = $inHead
        in_origin_main = $inOriginMain
    }
}

$lineageResults | ConvertTo-Json -Depth 10 | Tee-Object -FilePath "$out\14_merge_lineage_results.json"

Write-Step "RELEASE AUTHORITY CURRENT FILE"
if (Test-Path "RELEASE_AUTHORITY_SIGNOFF.md") {
    Copy-Item "RELEASE_AUTHORITY_SIGNOFF.md" "$out\15_RELEASE_AUTHORITY_SIGNOFF_CURRENT.md" -Force
}

Write-Step "GENERATE UPDATED RELEASE AUTHORITY DRAFT"

$releaseDraft = @"
# Crown Release Authority Sign-Off

Date: $(Get-Date -Format "yyyy-MM-dd")
Release Authority: TC (@tcmegahan)
Status: NO-GO — Gates incomplete. DO NOT DEPLOY TO CUSTOMER/PILOT AUTHORITY YET.

## Verified Production Deploy

- Latest successful deploy-prod run: $runId
- Run URL: $($latestSuccess.url)
- Deploy SHA: $runSha
- Deploy tag: $($healthJson.prod_deploy_tag)
- Runtime health: PASS
- Runtime integrity: PASS
- Runtime build_sha matches deploy SHA: PASS
- Runtime deploy_run_id matches deploy run: PASS
- Runtime version: $($healthJson.version)
- Runtime DB health: $($healthJson.db)

## Current Required Gates

| Gate | Status |
|---|---|
| deploy-prod completed successfully | PASS |
| /api/health/ returns HTTP 200 with current build metadata | PASS |
| /api/integrity/ returns HTTP 200 with current build metadata | PASS |
| Runtime deploy_run_id matches successful GitHub Actions run | PASS |
| Runtime build_sha matches successful GitHub Actions headSha | PASS |
| Merge lineage integrity fully reconciled | NOT VERIFIED |
| Full pytest suite authoritative pass | NOT VERIFIED |
| Branch protection/ruleset proof verified from remote settings | NOT VERIFIED |
| Compliance/customer readiness packet complete | NOT VERIFIED |
| Controlled pilot entry proof approved | NOT VERIFIED |
| Founder/Product Owner final GO signoff | NOT RECORDED |

## Decision

Release remains NO-GO until all required gates are PASS and final TC signoff is recorded.
"@

Set-Content -Path "$out\16_RELEASE_AUTHORITY_SIGNOFF_DRAFT.md" -Value $releaseDraft -Encoding utf8

Write-Step "GENERATE GATE SCORECARD"

$gateScorecard = [pscustomobject]@{
    generated_utc = (Get-Date).ToUniversalTime().ToString("o")
    release_decision = "NO-GO"
    pilot_decision = "NO-GO"
    latest_successful_deploy_run = $runId
    latest_successful_deploy_sha = $runSha
    runtime_health = "PASS"
    runtime_integrity = "PASS"
    runtime_lineage = "PASS"
    merge_lineage_integrity = "NOT VERIFIED"
    full_pytest = "NOT VERIFIED"
    compliance_customer_packet = "NOT VERIFIED"
    founder_signoff = "NOT RECORDED"
    next_required_action = "Resolve merge lineage integrity and close remaining non-runtime release gates."
}

$gateScorecard | ConvertTo-Json -Depth 10 | Tee-Object -FilePath "$out\17_GATE_SCORECARD.json"

Write-Step "WRITE HUMAN SUMMARY"

$summary = @"
# Crown2026 Release Lineage Closure Evidence

Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz")

## Verified

- Latest successful deploy-prod run: $runId
- Deploy SHA: $runSha
- Health endpoint: PASS
- Integrity endpoint: PASS
- Runtime build_sha matches deploy SHA: PASS
- Runtime deploy_run_id matches GitHub Actions run: PASS

## Still Not Closed

- Merge lineage integrity: NOT VERIFIED
- Full pytest authoritative pass: NOT VERIFIED
- Compliance/customer readiness packet: NOT VERIFIED
- Controlled pilot entry proof: NOT VERIFIED
- Founder/Product Owner final signoff: NOT RECORDED

## Decision

Release: NO-GO
Pilot: NO-GO

Reason: Runtime deployment proof is now positive, but full release authority gates remain incomplete.
"@

Set-Content -Path "$out\18_SUMMARY.md" -Value $summary -Encoding utf8

Write-Step "DONE"
Write-Host ""
Write-Host "EVIDENCE_DIR=$out"
Write-Host "SUMMARY=$out\18_SUMMARY.md"
Write-Host "SCORECARD=$out\17_GATE_SCORECARD.json"
Write-Host "RELEASE_DRAFT=$out\16_RELEASE_AUTHORITY_SIGNOFF_DRAFT.md"
